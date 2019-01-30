#!/usr/bin/env python3
#TODO use multithreading to download and convert. i.e. after a download is finished: start another one AND, at the same time, convert the file.

#misc
import os
import sys
import argparse
import enum

#getting info and downloading
import youtube_dl

#saving/editing mp3 tags
from mutagen.easyid3 import EasyID3

#regex to parse video titles
import re
from re import escape as reEsc

YDL_FILENAME = "playlist_downloader_temp_file.%(ext)s"
YDL_FILENAME_MP3 = YDL_FILENAME % {'ext': 'mp3'}
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
		log(LogLevel.warning, "Creating directory \"%s\"" % directory)
		os.makedirs(directory)
	return directory

class Song:
	invalidFilename = "playlist_downloader_invalid_song_filename_%s.mp3"

	def __init__(self, videoId, videoTitle, validDirectory):
		self.title = ""
		self.artist = ""
		self.remixer = ""
		self.filename = ""
		self.path = ""

		self.parseTitle(videoTitle)
		self.composeFilename(videoId, videoTitle, validDirectory)

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
	def composeFilename(self, videoId, videoTitle, validDirectory):
		Song.composeFilename.invalidChars = "<>:\"/\\|?*"
		Song.composeFilename.validCharsMin = 31 #chr(31)
		Song.composeFilename.dosNames = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

		for letter in videoTitle:
			if letter not in Song.composeFilename.invalidChars:
				if ord(letter) > Song.composeFilename.validCharsMin:
					self.filename += letter
		if self.filename == "" or self.filename in Song.composeFilename.dosNames:
			self.filename = Song.invalidFilename % videoId
		else:
			self.filename = self.filename + "_" + videoId + ".mp3"
		self.path = validDirectory + self.filename 
	def isValid(self):
		try: EasyID3(self.path)
		except: return False
		return True
class Video:
	def __init__(self, info, directory, playlistIndex = None):
		self.info = info
		self.id = info['id']
		self.title = info['title']
		self.directory = ensureValidDirectory(directory)
		self.song = Song(self.id, self.title, self.directory)
		self.inPlaylist = (playlistIndex is not None)
		self.playlistIndex = playlistIndex
	def __repr__(self):
		return self.title + " (" + self.id + ")"

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
							log(LogLevel.info, "Song %s changed name: renaming to %s" % (self.directory + filename, self.song.path))
							os.rename(self.directory + filename, self.song.path)
						return
				except KeyError: continue
		else:
			try:
				if directoryFilenames[self.id] != self.song.filename:
					log(LogLevel.info, "Song %s changed name: renaming to %s" % (self.directory + directoryFilenames[self.id], self.song.path))
					os.rename(self.directory + directoryFilenames[self.id], self.song.path)
			except KeyError: pass
	def download(self):
		try:
			if self.song.isValid():
				log(LogLevel.info, "\"%s\" already downloaded." % self)
				return

			log(LogLevel.info, "Downloading \"%s\"..." % self, flush=True)
			log(LogLevel.info, "Destination: \"%s\"" % self.song.path, flush=True)
			log(LogLevel.debug, "Song will be converted to mp3 and saved to \"%s\"" % (self.directory + YDL_FILENAME_MP3), flush=True)
			if self.inPlaylist:
				log(LogLevel.debug, "This video is in a playlist. Extracting info and downloading using id \"%s\"" % self.id)
				ydl.extract_info(self.id, download=True)
			else:
				#info already downloaded, only processing is needed
				log(LogLevel.debug, "This video is not in a playlist. The info has already been extracted, proceeding to download (id: \"%s\")" % self.id)
				ydl.process_ie_result(self.info, download=True)
			log(LogLevel.debug, "Renaming \"%s\" to \"%s\"" % (YDL_FILENAME_MP3, self.song.path))
			os.rename(YDL_FILENAME_MP3, self.song.path)
		except KeyboardInterrupt:
			raise
		except:
			log(LogLevel.error, "Failed to download")
	def saveMetadata(self, playlistId = None):
		log(LogLevel.debug, "Saving metadata...", flush=True)
		try:
			songFile = EasyID3(self.song.path)
		except:
			log(LogLevel.error, "Failed to save metadata")
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
	def __repr__(self):
		return self.title + " (" + self.id + ")"
	def logVideos(self):
		log(LogLevel.debug, "Playlist \"%s\" at \"%s\":" % (self, self.directory))
		if not Options.quiet and Options.verbose:
			for video in self.videos:
				print("*", video)

	def download(self):
		log(LogLevel.info, "Downloading playlist \"%s\" (id: \"%s\") to \"%s\"" % (self.title, self.id, self.directory))

		directoryFilenames = {}
		files = os.listdir(self.directory)
		for filename in files:
			# len("VIDEOTITLE_aaVIDEOIDaa.mp3") > 16
			if len(filename) > 16 and filename[-16] == "_" and filename[-4:] == ".mp3":
				try:
					if EasyID3(self.directory + filename)["album"][0] == self.id:
						directoryFilenames[filename[-15:-4]] = filename
				except KeyboardInterrupt:
					raise
				except:
					pass

		for video in self.videos:
			video.updateFile(directoryFilenames)
			video.download()
			video.saveMetadata(self.id)

		if Options.delete:
			playlistIds = [video.id for video in self.videos]
			for fileId, filename in directoryFilenames.items():
				if fileId not in playlistIds:
					log(LogLevel.info, "Removing song \"%s\" since its id \"%s\" doesn't refer to a video of the playlist \"%s\"." % (self.directory + filename, fileId, self.id))
					os.remove(self.directory + filename)

class Options:
	delete = False
	quiet = False
	verbose = False
	limitToConsoleWidth = False
	videos = []
	playlists = []

	argParser = argparse.ArgumentParser(prog="song-downloader.py")
	argParser.add_argument('-d', '--delete', action='store_true', default=False, help="Delete downloaded songs that do not belong anymore to the provided playlists")
	argParser.add_argument('-q', '--quiet', action='store_true', default=False, help="Do not print anything")
	argParser.add_argument('-v', '--verbose', action='store_true', default=False, help="Print more debug information")
	argParser.add_argument('-w', '--limit-to-console-width', action='store_true', default=False, help="Print to the console only part of the output so that it can fit in the console width")
	argParser.add_argument('download', nargs='+', metavar='IDS', help="Videos/Playlists to be downloaded (ID) and DIRECTORY to use (optional), formatted this way: ID [DIRECTORY] - ... - ID [DIRECTORY]")

	@staticmethod
	def parse(arguments, idsFileIfArgumentsEmpty = "song-downloader-ids.txt"):
		if len(arguments) == 1:
			try:
				arguments = open(idsFileIfArgumentsEmpty).read().split()
			except FileNotFoundError:
				log(LogLevel.warning, "no argument was provided via console and the file \"%s\" can't be opened." % idsFileIfArgumentsEmpty)
		else:
			arguments = arguments[1:]

		args = vars(Options.argParser.parse_args(arguments))
		Options.delete = args['delete']
		Options.quiet = args['quiet']
		Options.verbose = args['verbose']
		Options.limitToConsoleWidth = args['limit_to_console_width']

		if Options.limitToConsoleWidth:
			Options.consoleWidth = int(os.popen('stty size', 'r').read().split()[1])

		currentDownloadArgs = []
		for arg in args['download']:
			if arg == '-':
				Options.parseDownload(currentDownloadArgs)
				currentDownloadArgs = []
			else:
				currentDownloadArgs.append(arg)
		log(LogLevel.debug, "Options: Delete=%s; Quiet=%s; Verbose=%s; LimitToConsoleWidth=%s;" % (Options.delete, Options.quiet, Options.verbose, Options.limitToConsoleWidth))

		Options.parseDownload(currentDownloadArgs)
		log(LogLevel.info, "Videos:", Options.videos)
		log(LogLevel.info, "Playlists:", Options.playlists)
		for playlist in Options.playlists:
			playlist.logVideos()
		
	@staticmethod
	def parseDownload(downloadArgs):
		log(LogLevel.debug, "Parsing download arguments %s" % downloadArgs)
		if len(downloadArgs) == 0:
			return
		elif len(downloadArgs) == 1:
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
				log(LogLevel.debug, "Gotten playlist \"%s\" at \"%s\"" % (Options.playlists[-1], Options.playlists[-1].directory))
			else:
				Options.videos.append(Video(info, directory))
				log(LogLevel.debug, "Gotten video \"%s\" at \"%s\"" % (Options.videos[-1], Options.videos[-1].directory))

class LogLevel(enum.Enum):
	debug = 0,
	info = 1,
	warning = 2,
	error = 3
def log(level, *args, **kwargs):
	if not Options.quiet:
		if level == LogLevel.error:
			print("[error]", *args, **kwargs)
		else:
			if Options.limitToConsoleWidth:
				

				separator = kwargs.get('sep', " ")
				end = kwargs.get('end', "\n")
				newKwargs = {}
				for key, value in kwargs.items():
					if key != 'sep' and key != 'end':
						newKwargs[key] = value

				toPrint = ""
				if level == LogLevel.debug and Options.verbose:
					toPrint = "[debug] "
				elif level == LogLevel.info:
					toPrint = "[info] "
				elif level == LogLevel.warning:
					toPrint = "[warning] "
				else:
					return
					
				firstTime = True
				for arg in args:
					if firstTime:
						toPrint += arg.__str__()
					else:
						toPrint += separator + arg.__str__()
					firstTime = False
				toPrint += end

				lines = toPrint.split("\n")
				toPrint = ""
				for line in lines:
					if len(line) > Options.consoleWidth:
						toPrint += line[:Options.consoleWidth]
					else:
						toPrint += line + "\n"
				if toPrint[-1] == "\n":
					toPrint = toPrint[:-1]

				print(toPrint, sep="", end="", **newKwargs)
			else:
				if level == LogLevel.debug and Options.verbose:
					print("[debug]", *args, **kwargs)
				elif level == LogLevel.info:
					print("[info]", *args, **kwargs)
				elif level == LogLevel.warning:
					print("[warning]", *args, **kwargs)

def main(arguments):
	#arguments
	Options.parse(arguments)

	#downloading
	if len(Options.videos) == 0 and len(Options.playlists) == 0:
		log(LogLevel.warning, "Nothing has been provided to download")
	for video in Options.videos:
		video.updateFile()
		video.download()
		video.saveMetadata()
	for playlist in Options.playlists:
		playlist.download()


if __name__ == "__main__":
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
