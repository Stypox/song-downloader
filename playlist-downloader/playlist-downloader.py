#!/usr/bin/env python3

#misc
import os
import sys

#youtube authentication
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#html page reading and saving to file
import urllib.request
import fileinput

#delays
import time

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


def authenticateYt():
	try:
		for line in open(DEVELOPER_KEY_FILE_NAME, "r"):
			devKey = line
		authentication = build(API_SERVICE_NAME, API_VERSION, developerKey = devKey)
		return authentication

	except HttpError as e:
		print("An HTTP error ({}) occurred while authenticating: {}".format(e.resp.status, e.content))
		return None
	except FileNotFoundError as e:
		print("File named \"devkey.txt\" containing a developer key doesn't exists")
		return None
def readPlaylistId():
	try:
		for line in open(PLAYLIST_ID_FILE_NAME, "r"): playlistLink = line
		return playlistLink

	except FileNotFoundError:
		print("File named \"playlist.txt\" containing a playlist id doesn't exists")
		return None
def downloadPage(link):
	linkHeader = urllib.request.Request(link, headers=HEADERS)
	data = urllib.request.urlopen(linkHeader).read()
	return data


class Song:
	invalidFilename = "playlist-downloader-invalid-song-filename.mp3"

	def __init__(self, videoTitle):
		self.title = ""
		self.artist = ""
		self.remixer = ""
		self.filename = ""

		self.parseTitle(videoTitle)
		self.composeFilename()
	def parseTitle(self, videoTitle):
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
	def composeFilename(self):
		tmpFilename = ""
		if self.artist == "":
			tmpFilename = self.title
		else:
			if self.remixer == "":
				tmpFilename = "%s - %s" % (self.artist, self.title)
			else:
				tmpFilename = "%s (original by %s) - %s (remix)" % (self.remixer, self.artist, self.title)
		for letter in tmpFilename:
			if letter not in INVALID_FILENAME_CHARS:
				if ord(letter) > VALID_CHARS_MIN:
					self.filename += letter
		if self.filename == "" or self.filename in DOS_NAMES:
			self.filename = Song.invalidFilename
		else:
			self.filename = self.filename + ".mp3"
	def isValid(self, directory):
		try: EasyID3(directory + self.filename)
		except: return False
		return True
class Video:
	ytAgent = None
	converterLink = "https://www.convertmp3.io/download/?video=https://www.youtube.com/watch?v={}"
	emptyConverterLink = "https://www.convertmp3.io{}"

	def __init__(self, Id, title = None, playlistIndex = None, directory = None):
		self.Id = Id
		self.title = title
		
		if directory is None:
			directory = "./"
		elif len(directory) > 0 and directory[-1] != "/":
			directory += "/"
		self.directory = directory

		if title is None:
			self.playlistIndex = None
			self.song = None
		else:
			self.playlistIndex = playlistIndex
			self.song = Song(title)
	def __repr__(self):
		return self.song.filename
	def loadData(self):
		if self.song is not None:
			raise RuntimeError("Error: trying to run loadData() on a video (id: %s) that already has data loaded (title: %s)" % (self.Id, self.title))
		try:
			ytVidResponse = Video.ytAgent.videos().list(id=self.Id, part="snippet").execute()
			self.song = Song(ytVidResponse["items"][0]["snippet"]["title"])
		except HttpError as e:
			print("An HTTP error ({}) occurred while retrieving videos from playlist ({}): {}".format(e.resp.status, self.Id, e.content))
			return False
		return True
	def updateFile(self, directoryFilenames = None):
		if self.song is None:
			raise RuntimeError("Error: trying to run updateFile() on a video (id: %s) with no data loaded" % self.Id)
		if directoryFilenames is None:
			files = os.listdir(self.directory)
			for filename in files:
				try:
					songFile = EasyID3(self.directory + filename)
				except: continue
				try:
					if songFile["albumartist"][0] == self.Id:
						if filename != self.song.filename:
							print("Song %s changed name: renaming to %s" % (self.directory + filename, self.directory + self.song.filename))
							os.rename(self.directory + filename, self.directory + self.song.filename)
						return
				except KeyError: continue
		else:
			try:
				if directoryFilenames[self.Id] != self.song.filename:
					print("Song %s changed name: renaming to %s" % (directoryFilenames[self.Id], self.song.filename))
					os.rename(directoryFilenames[self.Id], self.song.filename)
			except KeyError: pass
	def saveToFile(self, data):
		songFile = open(self.directory + self.song.filename, "wb")
		songFile.write(data)
		songFile.close()
	def download(self):
		if self.song is None:
			raise RuntimeError("Error: trying to download a video (id: %s) not belonging to a playlist before running loadData()" % self.Id)
		if self.song.isValid(self.directory):
			print("%s already downloaded to %s" % (self.Id, self.directory + self.song.filename))
			return True
		print("Downloading %s to %s" % (self.Id, self.directory + self.song.filename))

		infoLink = Video.converterLink.format(self.Id)
		infoData = str(downloadPage(infoLink))
		linkPosition = infoData.find("/download/get/?i=")
		if linkPosition is -1:
			self.saveToFile(infoData.encode())
			return None

		videoLink = Video.emptyConverterLink.format(infoData[linkPosition:linkPosition+68])
		videoData = downloadPage(videoLink)
		self.saveToFile(videoData)
		
		if self.song.isValid(self.directory):
			return True
		else:
			time.sleep(TIME_PAUSE_IF_ERROR)
			videoData = downloadPage(videoLink)
			self.saveToFile(videoData)
			return self.song.isValid(self.directory)
	def saveMetadata(self, playlistId = None):
		try: songFile = EasyID3(self.directory + self.song.filename)
		except: return False
		songFile["tracknumber"] = str(self.playlistIndex)
		songFile["title"] = self.song.title
		songFile["artist"] = self.song.artist
		if playlistId is not None:
			songFile["album"] = playlistId
		songFile["albumartist"] = self.Id #TODO not good
		songFile.save()
		return True
class Playlist:
	ytAgent = None

	def __init__(self, Id):
		self.nr = 0
		self.videos = []
		if len(Id) == 34:
			self.Id = Id
		else:
			print("Playlist id must be 34 chars, not %i: %s" % (len(Id), Id))
			self.Id = None
		self.directory = "./" + Id + "/"
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
	def __getitem__(self, key):
		return self.videos[key]
	def __repr__(self):
		return [video.__repr__() for video in self.videos].__repr__()

	def ready(self):
		return Playlist.ytAgent is not None and self.Id is not None
	def append(self, Id, title):
		self.videos.append(Video(Id, title, len(self.videos), self.directory))
	def loadData(self):
		if not self.ready():
			return False
		try:
			ytPlaylist = Playlist.ytAgent.playlistItems()
			ytPlLister = ytPlaylist.list(playlistId=self.Id, part="snippet", maxResults=50)
			while ytPlLister:
				ytPlResponse = ytPlLister.execute()
				for item in ytPlResponse["items"]:
					self.append(item["snippet"]["resourceId"]["videoId"], item["snippet"]["title"])
				ytPlLister = ytPlaylist.list_next(ytPlLister, ytPlResponse)
		except HttpError as e:
			print("An HTTP error ({}) occurred while retrieving videos from playlist ({}): {}".format(e.resp.status, self.Id, e.content))
			return False
		return True
	def download(self):
		directoryFilenames = dict()
		files = os.listdir(self.directory)
		for filename in files:
			try:
				songFile = EasyID3(self.directory + filename)
				directoryFilenames[songFile["albumartist"][0]] = filename
			except: continue

		print(directoryFilenames)

		for video in self.videos:
			video.updateFile(directoryFilenames)
			if not video.download():
				print("Failed to download song %s" % video.Id)
			if not video.saveMetadata():
				print("Failed to save metadata on song %s" % video.Id)
			print()


# def main():
	# 	success = []
	# 	playlistLink = getPlaylistLink(success)
	# 	if len(success) is not 0: return
	# 	youtube = authenticate(success)
	# 	if len(success) is not 0: return
	# 	videos = getVideos(youtube, playlistLink, success)
	# 	if len(success) is not 0: return
	# 	while 1:
	# 		downloadedIds = []
	# 		fileDownloaded = open(DOWNLOADED_IDS_FILE_NAME, "r")
	# 		for line in fileDownloaded:
	# 			downloadedIds.append(line[:-1])
	# 		fileDownloaded.close()
	# 		print("Already downloaded videos:    ", end = "")
	# 		print(downloadedIds, end = "\n\n\n")
	# 		fileDownloaded = open(DOWNLOADED_IDS_FILE_NAME, "a")
	# 		for i in range(0, videos.nr):
	# 			videoPath = toMp3Path(videos.songArtists[i], videos.songTitles[i])
	# 			if videos.ids[i] in downloadedIds:
	# 				setMp3Metadata(videoPath, i + 1, videos.songTitles[i], videos.songArtists[i], videos.playlistId, videos.ids[i])
	# 			else:
	# 				if downloadVideo(videoPath, videos.ids[i], True):
	# 					setMp3Metadata(videoPath, i + 1, videos.songTitles[i], videos.songArtists[i], videos.playlistId, videos.ids[i])
	# 					fileDownloaded.write(videos.ids[i] + "\n")
	# 					fileDownloaded.flush()
	# 				#else:
	# 					#os.remove(videoPath)
	# 		fileDownloaded.close()
	# 		break

def main():
	Video.ytAgent = Playlist.ytAgent = authenticateYt()
	# vid = Video("rVAMYUSnR0I")
	# vid.loadData()
	# vid.updateFile()
	# vid.download()
	# vid.saveMetadata()
	playlist = Playlist(readPlaylistId())
	if not playlist.loadData(): return

	print(*playlist, sep = "\n")

	playlist.download()


if __name__ == "__main__":
	print("\n-----\nSTART\n-----\n")
	main()
	print("\n-----\n END \n-----\n")