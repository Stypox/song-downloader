#!/usr/bin/env python3
#TODO print more information (e.g. in Playlist.download()), add verbose mode and print an indicator for the type of information (info, warning, error)
#TODO use multithreading to download and convert. i.e. after a download is finished: start another one AND, at the same time, convert the file.
#TODO [look in Playlist.download()]
#TODO [look in Video.saveMetadata()]

#misc
import os
import sys

#getting info and downloading
import youtube_dl

#saving/editing mp3 tags
from mutagen.easyid3 import EasyID3

#regex to parse video titles
import re
from re import escape as reEsc

IDS_FILE_NAME = "playlist-downloader-ids.txt"
DELETE_ARGUMENTS = ["-d", "--delete"]

YDL_FILENAME = "playlist_downloader_temp_file.%(ext)s"
YDL_OPTS = {
	'outtmpl': YDL_FILENAME,
	'format': 'bestaudio/best',
	'postprocessors': [{
		'key': 'FFmpegExtractAudio',
		'preferredcodec': 'mp3',
		'preferredquality': '192',
	}],
	'noplaylist': False,
	'quiet': True,
}
ydl = youtube_dl.YoutubeDL(YDL_OPTS)

def ensureValidDirectory(directory, directoryIfInvalid = "./"):
	if directory is None:
		directory = directoryIfInvalid
	if len(directory) > 0 and directory[-1] != "/":
		directory += "/"

	if not os.path.isdir(directory):
		print("Creating directory \"%s\"" % directory)
		os.makedirs(directory)
	return directory

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
	def __init__(self, info, directory, playlistIndex = None):
		self.info = info
		self.id = info['id']
		self.title = info['title']
		self.song = Song(self.title)
		self.directory = ensureValidDirectory(directory)
		self.inPlaylist = (playlistIndex is not None)
		self.playlistIndex = playlistIndex
	def __repr__(self):
		if self.song is None:
			return self.title + " (" + self.id + ")"
		else:
			return self.song.filename

	def updateFile(self, directoryFilenames = None):
		if directoryFilenames is None:
			files = os.listdir(self.directory)
			for filename in files:
				try:
					songFile = EasyID3(self.directory + filename)
				except: continue
				try:
					if songFile["albumartist"][0] == self.id:
						if filename != self.song.filename:
							print("Song %s changed name: renaming to %s" % (self.directory + filename, self.directory + self.song.filename))
							os.rename(self.directory + filename, self.directory + self.song.filename)
						return
				except KeyError: continue
		else:
			try:
				if directoryFilenames[self.id] != self.song.filename:
					print("Song %s changed name: renaming to %s" % (self.directory + directoryFilenames[self.id], self.directory + self.song.filename))
					os.rename(self.directory + directoryFilenames[self.id], self.directory + self.song.filename)
			except KeyError: pass
	def download(self):
		if self.song.isValid(self.directory):
			print("\"%s\" already downloaded." % self.song.filename)
			return

		print("Downloading \"%s\"..." % self, flush=True)
		if self.inPlaylist:
			ydl.extract_info(self.id, download=True)
		else:
			#info already downloaded, only processing is needed
			ydl.process_ie_result(self.info, download=True)
		os.rename(YDL_FILENAME % {'ext': 'mp3'}, self.directory + self.song.filename)
	def saveMetadata(self, playlistId = None):
		print("Saving metadata...", flush=True)
		try:
			songFile = EasyID3(self.directory + self.song.filename)
		except:
			print("Failed to save metadata")
			return
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
		songFile["albumartist"] = self.id #TODO not good
		songFile.save()
class Playlist:
	delete = False

	def __init__(self, info, directory):
		self.id = info['id']
		self.title = info['title']
		self.directory = ensureValidDirectory(directory, "./%s/" % self.id)

		self.videos = []
		playlistIndex = 0
		for entry in info['entries']:
			self.videos.append(Video(entry, self.directory, playlistIndex))
			playlistIndex += 1
	def __getitem__(self, key):
		return self.videos[key]
	def __repr__(self):
		if len(self.videos) == 0:
			return self.title + " (" + self.id + ")"
		else:
			return [video.__repr__() for video in self.videos].__repr__()

	def download(self):
		#TODO do not try to rename / delete mp3's that do not belong to this playlist
		directoryFilenames = {}
		files = os.listdir(self.directory)
		for filename in files:
			try:
				songFile = EasyID3(self.directory + filename)
				directoryFilenames[songFile["albumartist"][0]] = filename
			except: continue

		for video in self.videos:
			video.updateFile(directoryFilenames)
			video.download()
			video.saveMetadata()

		if Playlist.delete:
			playlistIds = [video.id for video in self.videos]
			for fileId, filename in directoryFilenames.items():
				if fileId not in playlistIds:
					print("Removing song \"%s\" since its id \"%s\" doesn't refer to a video of the playlist \"%s\"." % (self.directory + filename, fileId, self.id))
					os.remove(self.directory + filename)

def getDownloader(id, directory):
	with ydl:
		info = ydl.extract_info(id, download=False, process=False)
		if 'entries' in info:
			return Playlist(info, directory)
		else:
			return Video(info, directory)

def parseArgsList(args, allArgs):
	if len(args) == 0:
		return
	elif len(args) > 2:
		raise RuntimeError("Invalid arguments (list of arguments \"%s\" too long): \"%s\"" % (args, allArgs))
	return getDownloader(args[0], args[1] if len(args) == 2 else None)
def main(arguments):
	#arguments parsing
	videos = []
	playlists = []
	args = arguments[1:]
	if len(args) > 0 and args[0] in DELETE_ARGUMENTS:
		Playlist.delete = True
		args = args[1:]
	if len(args) > 0:
		print("Parsing command line arguments...")
		tmpArgs = []
		for arg in args:
			if arg == "-":
				downloader = parseArgsList(tmpArgs, args)
				if type(downloader) is Video:
					videos.append(downloader)
				elif type(downloader) is Playlist:
					playlists.append(downloader)
				tmpArgs = []
			else:
				tmpArgs.append(arg)
		downloader = parseArgsList(tmpArgs, args)
		if type(downloader) is Video:
			videos.append(downloader)
		elif type(downloader) is Playlist:
			playlists.append(downloader)
	else:
		print("Reading and parsing file \"%s\"..." % IDS_FILE_NAME)
		idsFile = open(IDS_FILE_NAME, "r")
		args = [line.strip() for line in idsFile]
		if len(args) > 0 and args[0] in DELETE_ARGUMENTS:
			delete = True
			args = args[1:]
		for arg in args:
			downloader = parseArgsList(arg.split(' '), args)
			if type(downloader) is Video:
				videos.append(downloader)
			elif type(downloader) is Playlist:
				playlists.append(downloader)

	print("Videos:", *videos, "- Playlists:", *playlists)

	#downloading
	if len(videos) == 0 and len(playlists) == 0:
		print ("Nothing has been provided to download")
	for video in videos:
		video.updateFile()
		video.download()
		video.saveMetadata()
	for playlist in playlists:
		playlist.download()


if __name__ == "__main__":
	print("\n%s\nSTART %s\n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))
	try:
		main(sys.argv)
	except:
		def removeIfExists(filename):
			if os.path.isfile(filename):
				os.remove(filename)

		removeIfExists(YDL_FILENAME % {'ext': 'mp3'})
		removeIfExists(YDL_FILENAME % {'ext': 'webm'})
		removeIfExists(YDL_FILENAME % {'ext': 'webm.part'})
		removeIfExists(YDL_FILENAME % {'ext': 'm4a'})
		removeIfExists(YDL_FILENAME % {'ext': 'm4a.part'})
		removeIfExists(YDL_FILENAME % {'ext': 'ytdl'})
		removeIfExists(YDL_FILENAME % {'ext': 'ytdl.part'})

		raise
	print("\n%s\n END %s \n%s\n" % ("-" * (6 + len(sys.argv[0])), sys.argv[0], "-" * (6 + len(sys.argv[0]))))
