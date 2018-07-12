#!/usr/bin/env python3

#misc
import os

#youtube authentication
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

#html page reading and saving to file
import urllib
import fileinput

#delays
import time

#exceptions
import sys

#editing file tags
from mutagen.easyid3 import EasyID3

#regex to parse video titles
import re
from re import escape as reEsc

API_SERVICE_NAME = "youtube"
API_VERSION = "v3"

HEADERS = {
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
	"Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
	"Accept-Encoding": "none",
	"Accept-Language": "en-US,en;q=0.8",
	"Connection": "keep-alive"
	}

INVALID_FILENAME_CHARS = "<>:\"/\\|?*"
VALID_CHARS_MIN = 31 #char 31
DOS_NAMES = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
INVALID_SONG_NAME = "invalid_song_name.mp3"

PLAYLIST_LINK = "https://www.youtube.com/playlist?list={}"
VIDEO_LINK = "https://youtu.be/{}"
CONVERTER_VIDEO_LINK = "https://www.convertmp3.io/download/?video=https://www.youtube.com/watch?v={}"
CONVERTER_EMPTY_LINK = "https://www.convertmp3.io{}"

PLAYLIST_ID_FILE_NAME = "playlist.txt"
DEVELOPER_KEY_FILE_NAME = "devkey.txt"
DOWNLOADED_IDS_FILE_NAME = "downloaded.txt"

TIME_PAUSE_IF_ERROR = 10 #seconds
TIME_BEFORE_RESTARTING = 30 #seconds

class Song:
	def __init__(self, videoTitle):
		self.title = ""
		self.artist = ""
		self.remixer = ""

		#finds the artist
		artistEndMatch = re.search("([%s] )|( [%s] )" % (reEsc(":"), reEsc("-_|<>^")), videoTitle)
		if artistEndMatch is None:
			self.title = videoTitle
			return
		else:
			self.artist = videoTitle[:artistEndMatch.start()].strip()
			videoTitle = videoTitle[artistEndMatch.end():].strip()

		#finds the title
		titleEndMatch = re.search("( [%s])|( [%s] )" % (reEsc("()[]{}<>"), reEsc("-_|\\/")), videoTitle)
		if titleEndMatch is None:
			self.title = videoTitle
		else:
			self.title = videoTitle[:titleEndMatch.start()].strip()

			#finds the remixer
			remixMatch = re.search(" ((([Rr][Ee])?[Mm][Ii][Xx])|([Rr][Ee][Ww][Oo][Rr][Kk]([Ii][Nn][Gg])?))", videoTitle)
			if remixMatch is not None:
				videoTitle = videoTitle[:remixMatch.start()]
				remixerStartMatches = re.finditer("( [%s])|( [%s] )" % (reEsc("()[]{}<>"), reEsc("-_|\\/")), videoTitle)
				remixerStart = None
				for match in remixerStartMatches:
					remixerStart = match.end()
				if remixerStart != -1:
					self.remixer = videoTitle[remixerStart:].strip()

		#removes featurings
		featMatch = re.search("[;,]?[ ][Ff]([Ee][Aa])?[Tt]", self.artist)
		if featMatch is not None:
			self.artist = self.artist[:featMatch.start()]
		featMatch = re.search("[;,]?[ ][Ff]([Ee][Aa])?[Tt]", self.title)
		if featMatch is not None:
			self.title = self.title[:featMatch.start()]
		featMatch = re.search("[;,]?[ ][Ff]([Ee][Aa])?[Tt]", self.remixer)
		if featMatch is not None:
			self.remixer = self.remixer[:featMatch.start()]



class Video:
	def __init__(self, title, id):
		self.title = title
		self.id = id
		self.song = Song(title)
class Playlist:
	def __init__(self, PlaylistId):
		self.nr = 0
		self.titles = []
		self.ids = []
		self.songTitles = []
		self.songArtists = []
		self.playlistId = PlaylistId

	def append(self, title, id):
		self.titles.append(title)
		self.ids.append(id)

		foundRemix = False
		songArtist, songTitle, tempRemixArtist = "", "", ""
		artistEnd = title.find(" - ")
		if (artistEnd is -1):
			artistEnd = title.find(" | ")
		if (artistEnd is -1):
			songTitle = title
		else:
			songArtist = title[:artistEnd]
			titleLength = len(title)
			end = False
			for i in range(artistEnd + 3, titleLength):
				if title[i] in "()[]{}<>|-\\/:;,_":
				   end = True
				if title[i] in "Ff":
					if i + 1 < titleLength and title[i + 1] in "Tt":
						if i + 2 < titleLength and title[i + 2] is ".":
							end = True
					elif i + 1 < titleLength and title[i + 1] in "Ee":
						if i + 2 < titleLength and title[i + 2] in "Aa":
							if i + 3 < titleLength and title[i + 3] in "Tt":
								if i + 4 < titleLength and title[i + 4] is ".":
									end = True
				if end:
				   if ("remix" in title.lower()):
					   foundRemix = True
					   tempRemixArtist = ""
					   remixPos = title.lower().find("remix")
					   for r in range(i, len(title)):
						   if r is remixPos:
							   break
						   tempRemixArtist += title[r]
						   if (title[r] in "()[]{}<>|\\/;,") or (title[r] in "-_:" and r > 0 and r < titleLength and title[r + 1] is " " and title[r - 1] is " "):
							   tempRemixArtist = ""
				   break

				songTitle += title[i]


		if foundRemix:
			if (tempRemixArtist.strip() is ""):
				self.songArtists.append(songArtist.strip() + " (remixed)")
			else:
				self.songArtists.append(tempRemixArtist.strip() + " (original by " + songArtist.strip() + ")")
			self.songTitles.append(songTitle.strip() + " (remix)")
		else:
			self.songArtists.append(songArtist.strip())
			self.songTitles.append(songTitle.strip())
		self.nr += 1

	def all(self):
		All = []
		for t, i in zip(self.titles, self.ids):
			All.append([t, i])
		return All

	def at(self, position):
		return [self.titles[position], self.ids[position]]


def setMp3Metadata(path, nr, title, artist, playlistIdAsAlbum, videoIdAsAlbumArtist):
	try: songFile = EasyID3(path)
	except: return False
	songFile["tracknumber"] = str(nr)
	songFile["title"] = title
	songFile["artist"] = artist
	songFile["album"] = PLAYLIST_LINK.format(playlistIdAsAlbum)
	songFile["albumartist"] = VIDEO_LINK.format(videoIdAsAlbumArtist)
	songFile.save()
def getPlaylistLink(readingSuccess):
	try:
		for line in open(PLAYLIST_ID_FILE_NAME, "r"): playlistLink = line
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
		for line in open(DEVELOPER_KEY_FILE_NAME, "r"): devKey = line
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
		videos = Playlist(PlaylistId)
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

def toMp3Path(artist, title):
	if (artist is ""): path = title
	else: path = artist + " - " + title
	final = ""
	for letter in path:
		if letter not in INVALID_FILENAME_CHARS:
			if ord(letter) > VALID_CHARS_MIN:
				final += letter
			else:
				final += "-"
	if (final is "") or (final in DOS_NAMES):
		return SONG_INVALID_NAME
	return (final + ".mp3")
def downloadPage(link):
	linkHeader = urllib.request.Request(link, headers=HEADERS)
	data = urllib.request.urlopen(linkHeader).read()
	return data
def downloadVideo(path, id, Print = False):
	try:
		if Print: print (path)
		infoLink = CONVERTER_VIDEO_LINK.format(id)
		infoData = str(downloadPage(infoLink))
		linkPosition = infoData.find("/download/get/?i=")
		if linkPosition is -1:
			if Print: print("An error occurred: cannot find a download link\n")
			file = open(path, "wb")
			file.write(infoData.encode())
			file.close()
			return False

		videoLink = CONVERTER_EMPTY_LINK.format(infoData[linkPosition:linkPosition+68])
		
		
		if Print: print(videoLink)
		file = open(path, "wb")
		videoData = downloadPage(videoLink)
		file.write(videoData)
		file.close()

		try: EasyID3(path)
		except:
			if Print: print("Not converted. Trying again in {} seconds... ".format(TIME_PAUSE_IF_ERROR), end = "")
			time.sleep(TIME_PAUSE_IF_ERROR)
			videoData = downloadPage(videoLink)
			file = open(path, "wb")
			file.write(videoData)
			file.close()

			try: EasyID3(path)
			except:
				if Print: print("A download error occurred: the downloaded data is invalid, since it is not a song\n")
				return False
			if Print: print("Converted!\n")
		return True
		
	except HttpError as e:
		if Print: print("An HTTP error ({}) occurred: {}\n".format(e.resp.status, e.content))
		return False
	except ValueError as e:
		if Print: print("A value error occurred: {}\n".format(repr(e)))
		return False
	except:
		if Print:
			e = sys.exc_info()[0]
			print("An error occurred: {}\n".format(e))
		return False


def main():
	success = []
	playlistLink = getPlaylistLink(success)
	if len(success) is not 0: return
	youtube = authenticate(success)
	if len(success) is not 0: return
	videos = getVideos(youtube, playlistLink, success)
	if len(success) is not 0: return
	

	while 1:
		downloadedIds = []
		fileDownloaded = open(DOWNLOADED_IDS_FILE_NAME, "r")
		for line in fileDownloaded:
			downloadedIds.append(line[:-1])
		fileDownloaded.close()
		print("Already downloaded videos:    ", end = "")
		print(downloadedIds, end = "\n\n\n")
		


		fileDownloaded = open(DOWNLOADED_IDS_FILE_NAME, "a")
		for i in range(0, videos.nr):
			videoPath = toMp3Path(videos.songArtists[i], videos.songTitles[i])
			if videos.ids[i] in downloadedIds:
				setMp3Metadata(videoPath, i + 1, videos.songTitles[i], videos.songArtists[i], videos.playlistId, videos.ids[i])
			else:
				if downloadVideo(videoPath, videos.ids[i], True):
					setMp3Metadata(videoPath, i + 1, videos.songTitles[i], videos.songArtists[i], videos.playlistId, videos.ids[i])
					fileDownloaded.write(videos.ids[i] + "\n")
					fileDownloaded.flush()
				#else:
					#os.remove(videoPath)
		fileDownloaded.close()
		break


if __name__ == "__main__":
	print("\n-----\nSTART\n-----\n")
	s = Song("Clean Bandit - Symphony feat. Zara Larsson (Jim Yosef remix)")
	print(s.artist, s.title, s.remixer, sep = " - ")
	#main()
	print("\n-----\n END \n-----\n")
