#!/usr/bin/env python3
#TODO print more information (e.g. in Playlist.download()), add verbose mode and print an indicator for the type of information (info, warning, error)
#TODO use multithreading to download and convert. i.e. after a download is finished: start another one AND, at the same time, convert the file.
#TODO [look in Playlist.download()]
#TODO [look in Video.saveMetadata()]

#misc
import os
import sys
import argparse

#getting info and downloading
import youtube_dl

#saving/editing mp3 tags
from mutagen.easyid3 import EasyID3

#regex to parse video titles
import re
from re import escape as reEsc

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

		if Options.delete:
			playlistIds = [video.id for video in self.videos]
			for fileId, filename in directoryFilenames.items():
				if fileId not in playlistIds:
					print("Removing song \"%s\" since its id \"%s\" doesn't refer to a video of the playlist \"%s\"." % (self.directory + filename, fileId, self.id))
					os.remove(self.directory + filename)

class Options:
	delete = False
	quiet = False
	verbose = False
	videos = []
	playlists = []

	argParser = argparse.ArgumentParser(prog="playlist-downloader.py")
	argParser.add_argument('--delete', action='store_true', default=False, help="Delete downloaded songs that do not belong anymore to the provided playlists")
	argParser.add_argument('--quiet', '-q', action='store_true', default=False, help="Do not print anything")
	argParser.add_argument('--verbose', '-v', action='store_true', default=False, help="Print more debug information")
	argParser.add_argument('download', nargs='+', metavar='ID', help="Videos/Playlists to be downloaded (ID) and DIRECTORY to use (optional), formatted this way: ID [DIRECTORY] - ... - ID [DIRECTORY]")

	@staticmethod
	def parse(arguments, idsFileIfArgumentsEmpty = "playlist-downloader-ids.txt"):
		if len(arguments) == 1:
			try:
				arguments = open(idsFileIfArgumentsEmpty).read().split()
			except FileNotFoundError:
				print("Warning: no argument was provided via console and the file \"%s\" can't be opened." % idsFileIfArgumentsEmpty)
		else:
			arguments = arguments[1:]

		args = vars(Options.argParser.parse_args(arguments))
		Options.delete = args['delete']
		Options.quiet = args['quiet']
		Options.verbose = args['verbose']

		currentDownloadArgs = []
		for arg in args['download']:
			if arg == '-':
				Options.parseDownload(currentDownloadArgs)
				currentDownloadArgs = []
			else:
				currentDownloadArgs.append(arg)
		if len(currentDownloadArgs) != 0:
			Options.parseDownload(currentDownloadArgs)
		
	@staticmethod
	def parseDownload(downloadArgs):
		if len(downloadArgs) == 1:
			id = downloadArgs[0]
			directory = None
		elif len(downloadArgs) == 2:
			id = downloadArgs[0]
			directory = downloadArgs[1]
		else:
			raise argparse.ArgumentError("download", "Excepted 1 or 2 arguments but got %d: \"%s\"" % (len(downloadArgs), downloadArgs))

		with ydl:
			info = ydl.extract_info(id, download=False, process=False)
			if 'entries' in info:
				Options.playlists.append(Playlist(info, directory))
			else:
				Options.videos.append(Video(info, directory))

def main(arguments):
	Options.parse(arguments)
	print("Videos:", *Options.videos, "- Playlists:", *Options.playlists)

	#downloading
	if len(Options.videos) == 0 and len(Options.playlists) == 0:
		print ("Nothing has been provided to download")
	for video in Options.videos:
		video.updateFile()
		video.download()
		video.saveMetadata()
	for playlist in Options.playlists:
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
