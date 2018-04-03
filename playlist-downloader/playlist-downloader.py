import argparse
import os
import re

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

import urllib
import fileinput

import time

import sys

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
dosnames = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
invalidSongSizeMax = 50000 #byte


class VideosList:
    def __init__(self):
        self.nr = 0
        self.titles = []
        self.ids = []

    def append(self, title, id):
        self.titles.append(title)
        self.ids.append(id)
        self.nr += 1

    def all(self):
        All = []
        for t, i in zip(self.titles, self.ids):
            All.append([t, i])
        return All

    def at(self, position):
        return [self.titles[position], self.ids[position]]


def getPlaylistLink(readingSuccess):
    try:
        for line in open("playlist.txt", "r"): playlistLink = line
        return playlistLink

    except FileNotFoundError as e:
        print("File named \"playlist.txt\" containing a playlist id doesn't exists")
        readingSuccess.append("File named \"playlist.txt\" containing a playlist id doesn't exists")
        return False
    except:
        e = sys.exc_info()[0]
        print("An error occurred while reading \"playlist.txt\": {}".format(e))
        readingSuccess.append("An error occurred while reading \"playlist.txt\": {}".format(e))
        return False
def authenticate(authenticationSuccess):
    try:
        for line in open("devkey.txt", "r"): devKey = line
        authentication = build(API_SERVICE_NAME, API_VERSION, developerKey = devKey)
        authenticationSuccess = True
        return authentication

    except HttpError as e:
        print("An HTTP error ({}) occurred while authenticating: {}".format(e.resp.status, e.content))
        authenticationSuccess.append("An HTTP error ({}) occurred while authenticating: {}".format(e.resp.status, e.content))
        return False
    except FileNotFoundError as e:
        print("File named \"devkey.txt\" containing a developer key doesn't exists")
        authenticationSuccess.append("File named \"devkey.txt\" containing a developer key doesn't exists")
        return False
    except:
        e = sys.exc_info()[0]
        print("An error occurred while authenticating: {}".format(e))
        authenticationSuccess.append("An error occurred while authenticating: {}".format(e))
        return False

def getVideos(Youtube, PlaylistId, retrievingSuccess):
    try:
        playlist = Youtube.playlistItems().list(playlistId=PlaylistId, part="snippet", maxResults=50)
        videos = VideosList()
        while playlist:
            playlistItems = playlist.execute()
            for video in playlistItems["items"]:
                videos.append(video["snippet"]["title"], video["snippet"]["resourceId"]["videoId"])
            playlist = Youtube.playlistItems().list_next(playlist, playlistItems)
        return videos

    except HttpError as e:
        print("An HTTP error ({}) occurred while retrieving videos from playlist ({}): {}".format(e.resp.status, PlaylistId, e.content))
        retrievingSuccess.append("An HTTP error ({}) occurred while retrieving videos from playlist ({}): {}".format(e.resp.status, PlaylistId, e.content))
        return False
    except:
        e = sys.exc_info()[0]
        print("An error occurred while retrieving videos from playlist ({}): {}".format(PlaylistId, e))
        retrievingSuccess.append("An error occurred while retrieving videos from playlist ({}): {}".format(PlaylistId, e))
        return False

def toMp3Path(path):
    final = ""
    for letter in path:
        if letter not in '<>:"/\|?*':
            if ord(letter) > 31:
                final += letter
            else:
                final += "-"
    if (final == "") or (final in dosnames):
        return "invalid_songname.mp3"
    return (final + ".mp3")
def downloadPage(link):
    linkHeader = urllib.request.Request(link, headers=hdr)
    data = urllib.request.urlopen(linkHeader).read()
    return data
def downloadVideo(path, id, Print = False):
    if Print: print (path)
    infoLink = "https://www.convertmp3.io/download/?video=https://www.youtube.com/watch?v={}".format(id)
    infoData = str(downloadPage(infoLink))
    linkPosition = infoData.find("/download/get/?i=")
    videoLink = "https://www.convertmp3.io{}".format(infoData[linkPosition:linkPosition+68])


    if videoLink == "https://www.convertmp3.io":
        if Print: print("ERROR")
        file = open(path, "wb")
        file.write(infoData.encode())
        file.close()
        return False
        
        
    if Print: print(videoLink)
    file = open(path, "wb")
    videoData = downloadPage(videoLink)

    if len(videoData) < invalidSongSizeMax:
        if Print: print("Not converted. Trying again.")
        time.sleep(5)
        videoData = downloadPage(videoLink)

        if len(videoData) < invalidSongSizeMax:
            if Print: print("ERROR")
            file.write(videoData)
            file.close()
            return False
        elif Print: print("Converted!")

    file.write(videoData)
    file.close()
    return True


def main():
    success = []
    playlistLink = getPlaylistLink(success)
    if len(success) != 0: return
    youtube = authenticate(success)
    if len(success) != 0: return
    videos = getVideos(youtube, playlistLink, success)
    if len(success) != 0: return
    

    while 1:
        downloadedIds = []
        fileDownloaded = open("downloaded.txt", "r")
        for line in fileDownloaded:
            downloadedIds.append(line[:-1])
        fileDownloaded.close()
        print(downloadedIds, end = "\n\n\n")
        

        if (len(downloadedIds) == videos.nr):
            print("Completed...")
            return


        fileDownloaded = open("downloaded.txt", "a")
        for i in range(0, videos.nr):
            if videos.ids[i] not in downloadedIds:
                if downloadVideo(toMp3Path(videos.titles[i]), videos.ids[i], True):
                    fileDownloaded.write(videos.ids[i] + "\n")
                    fileDownloaded.flush()
        fileDownloaded.close()


        print("Restarting in 5 seconds", end = "\r")
        time.sleep(1)
        print("Restarting in 4 seconds", end = "\r")
        time.sleep(1)
        print("Restarting in 3 seconds", end = "\r")
        time.sleep(1)
        print("Restarting in 2 seconds", end = "\r")
        time.sleep(1)
        print("Restarting in 1 seconds", end = "\r")
        time.sleep(1)
        print("Restarting...          ")



main()
while 1: pass