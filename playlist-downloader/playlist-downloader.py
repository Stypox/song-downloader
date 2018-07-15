#!/usr/bin/env python3

#misc
import os
import sys
import time

#youtube authentication
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#html page reading, saving to file and editing mp3 tags
import urllib.request
import fileinput
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

VIDEO_ID_LEN = 11
PLAYLIST_ID_LEN = 34

DEVELOPER_KEY_FILE_NAME = "playlist-downloader-devkey.txt"
IDS_FILE_NAME = "playlist-downloader-ids.txt"

TIME_PAUSE_IF_ERROR = 10 #seconds


def authenticateYt():
	try:
		for line in open(DEVELOPER_KEY_FILE_NAME, "r"):
			devKey = line
		authentication = build(API_SERVICE_NAME, API_VERSION, developerKey = devKey)
		return authentication

	except HttpError as e:
		print("An HTTP error (%s) occurred while authenticating: %s" % (e.resp.status, e.content))
		return None
	except FileNotFoundError as e:
		print("File named \"%s\" containing a developer key doesn't exists" % DEVELOPER_KEY_FILE_NAME)
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
		self.composeFilename(videoTitle)
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
	def composeFilename(self, videoTitle):
		Song.composeFilename.invalidChars = "<>:\"/\\|?*"
		Song.composeFilename.validCharsMin = 31 #chr(31)
		Song.composeFilename.dosNames = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

		for letter in videoTitle:
			if letter not in Song.composeFilename.invalidChars:
				if ord(letter) > Song.composeFilename.validCharsMin:
					self.filename += letter
		if self.filename == "" or self.filename in Song.composeFilename.dosNames:
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
		if self.song is None:
			return self.Id
		else:
			return self.song.filename
			
	def loadData(self):
		if self.song is not None:
			raise RuntimeError("Error: trying to run loadData() on a video (id: %s) that already has data loaded (title: %s)" % (self.Id, self.title))
		try:
			ytVidResponse = Video.ytAgent.videos().list(id=self.Id, part="snippet").execute()
			self.song = Song(ytVidResponse["items"][0]["snippet"]["title"])
		except HttpError as e:
			print("An HTTP error (%s) occurred while retrieving video title of %s: %s" % (e.resp.status, self.Id, e.content))
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
					print("Song %s changed name: renaming to %s" % (self.directory + directoryFilenames[self.Id], self.directory + self.song.filename))
					os.rename(self.directory + directoryFilenames[self.Id], self.directory + self.song.filename)
			except KeyError: pass
	def saveToFile(self, data):
		songFile = open(self.directory + self.song.filename, "wb")
		songFile.write(data)
		songFile.close()
	def download(self):
		if self.song is None:
			raise RuntimeError("Error: trying to download a video (id: %s) not belonging to a playlist before running loadData()" % self.Id)
		if self.song.isValid(self.directory):
			print("%s already downloaded to %s... " % (self.Id, self.directory + self.song.filename), end = "", flush=True)
			return True
		print("Downloading %s to %s... " % (self.Id, self.directory + self.song.filename), end = "", flush=True)

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
		if self.playlistIndex is not None:
			songFile["tracknumber"] = str(self.playlistIndex)
		if self.song.remixer == "":
			songFile["title"] = self.song.title
			songFile["artist"] = self.song.artist
		else:
			songFile["title"] = "%s (remix)" % self.song.title
			songFile["artist"] = "%s (original by %s)" % (self.song.remixer, self.song.artist)
		if playlistId is not None:
			songFile["album"] = playlistId
		songFile["albumartist"] = self.Id #TODO not good
		songFile.save()
		return True
class Playlist:
	ytAgent = None

	def __init__(self, Id, directory = None):
		self.nr = 0
		self.videos = []
		if len(Id) == 34:
			self.Id = Id
		else:
			print("Playlist id must be 34 chars, not %i: %s" % (len(Id), Id))
			self.Id = None
		if directory is None:
			self.directory = "./" + Id + "/"
		else:
			self.directory = directory
			if self.directory[-1] != "/":
				self.directory += "/"
	def __getitem__(self, key):
		return self.videos[key]
	def __repr__(self):
		if len(self.videos) == 0:
			return self.Id
		else:
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
			print("An HTTP error (%s) occurred while retrieving videos from playlist (%s): %s" % (e.resp.status, self.Id, e.content))
			return False
		return True
	def download(self):
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)

		directoryFilenames = dict()
		files = os.listdir(self.directory)
		for filename in files:
			try:
				songFile = EasyID3(self.directory + filename)
				directoryFilenames[songFile["albumartist"][0]] = filename
			except: continue

		for video in self.videos:
			video.updateFile(directoryFilenames)
			if video.download():
				if video.saveMetadata():
					print("Done")
				else:
					print("Failed to save metadata")
			else:
				print("Failed to download")


def parseArguments(tmpArgs, arguments):
	if len(tmpArgs) == 0:
		return None
	elif len(tmpArgs) == 1:
		if len(tmpArgs[0]) == VIDEO_ID_LEN:
			return Video(tmpArgs[0])
		elif len(tmpArgs[0]) == PLAYLIST_ID_LEN:
			return Playlist(tmpArgs[0])
		else:
			raise RuntimeError("Invalid arguments (argument \"%s\" is neither a video nor a playlist id) \"%s\"" % (tmpArgs[0], arguments))
	elif len(tmpArgs) == 2:
		if not os.path.isdir(tmpArgs[1]):
			print("%s is not an existing directory, it will be cerated" % (tmpArgs[1]))
		if len(tmpArgs[0]) == VIDEO_ID_LEN:
			return Video(tmpArgs[0], tmpArgs[1])
		elif len(tmpArgs[0]) == PLAYLIST_ID_LEN:
			return Playlist(tmpArgs[0], tmpArgs[1])
		else:
			raise RuntimeError("Invalid arguments (argument 1 of list \"%s\" is neither a video nor a playlist id) \"%s\"" % (tmpArgs, arguments))
	else:
		raise RuntimeError("Invalid arguments (list of arguments \"%s\" too long) \"%s\"" % (tmpArgs, arguments))
def main(arguments):
	Video.ytAgent = Playlist.ytAgent = authenticateYt()
	if Playlist.ytAgent is None:
		return

	#arguments parsing
	videos = []
	playlists = []
	if len(arguments) > 1:
		print("Parsing command line arguments... ", end = "", flush = True)
		tmpArgs = []
		args = arguments[1:]
		for arg in args:
			if arg == "-":
				downloader = parseArguments(tmpArgs, args)
				if type(downloader) is Video:
					videos.append(downloader)
				elif type(downloader) is Playlist:
					playlists.append(downloader)
				tmpArgs = []
			else:
				tmpArgs.append(arg)
		downloader = parseArguments(tmpArgs, args)
		if type(downloader) is Video:
			videos.append(downloader)
		elif type(downloader) is Playlist:
			playlists.append(downloader)
		print("Done")
	else:
		print("Reading and parsing file %s... " % IDS_FILE_NAME, end = "", flush = True)
		idsFile = open(IDS_FILE_NAME, "r")
		for arg in idsFile:
			downloader = parseArguments(arg.split(' '), arguments)
			if type(downloader) is Video:
				videos.append(downloader)
			elif type(downloader) is Playlist:
				playlists.append(downloader)
		print("Done")

	print("Videos:", *videos, "- Playlists:", *playlists)

	#downloading
	for video in videos:
		video.loadData()
		video.updateFile()
		if video.download():
			if video.saveMetadata():
				print("Done")
			else:
				print("Failed to save metadata")
		else:
			print("Failed to download")
	for playlist in playlists:
		playlist.loadData()
		playlist.download()


if __name__ == "__main__":
	print("\n%s\nSTART %s\n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))
	main(sys.argv)
	print("\n%s\n END %s \n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))