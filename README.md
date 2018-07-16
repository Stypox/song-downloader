# Playlist downloader
Downloads an entire youtube playlist (or single videos) in **mp3 format**, **deducing** and saving **artist**, **name**, **remixer**, **tracknumber**... If the song has already been downloaded updates only its metadata.  

Uses the API of an online downloader ([ConvertMp3](https://convertmp3.io)) so **only the audio data is downloaded**.
##### I downloaded a ~150 songs playlist and it worked fine. I also developed an [mp3-player](https://github.com/Stypox/mp3-player), that can play playlists in order.

# [ID3](https://en.wikipedia.org/wiki/ID3) metadata and title parsing
Imagine a playlist (id ``1234567890abcdefghijklmnopqrstuvwx``) whose second video (id ``0a1b3c4d5e6``) is titled<br/>``ArtistName feat. Ft1 | SongName [Rel release](Remixer ft. Ft2 remix)``; the song's ID3 metadata would be:

    artist: "Remixer (original by ArtistName)"
    title: "SongName (remix)"
    tracknumber: "1"
    album: "1234567890abcdefghijklmnopqrstuvwx"
    albumartist: "0a1b3c4d5e6"
Yes, **"albumartist" is the video id**. "tracknumber" is **1** because the video is the **second** one of the playlist

# Usage
Choose some videos and playlists to **download** (for example [this video](https://www.youtube.com/watch?v=z-teFykRk0Y) and [this playlist](https://www.youtube.com/playlist?list=PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C)) and **extract their ids** (in this case "z-teFykRk0Y" and "PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C").  

Then there are **two ways** to provide the script with those ids: using a **file** or using **command line arguments** (all parameters between **\[square brackets\]** are to be considered optional; **\|** means **or**):

## Saving ids in file
In the directory the script is executed in create a file named ``playlist-downloader-ids.txt``. In that file you can insert the **videos/playlists to be downloaded** this way:

    [--d | --delete]
    ID [DIRECTORY]
    ID [DIRECTORY]
    ...
The first argument, -d (or --delete, use the one you prefer), is **optional**: when used the script will **remove songs** in the playlist directory not belonging to it. "ID" represents the playlist or video id; "DIRECTORY" is **optional**, represents the directory in which to save the song(s), and defaults to ``./`` for videos and ``./ID/`` for playlists. **Save the file and run** the script. In this case the file could be:

    --delete
    z-teFykRk0Y ./my_songs/
    PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C

## Passing ids as command line arguments
**Open a terminal** and navigate to the "DIRECTORY" the python script is in (run ``cd DIRECTORY``). Then run ``python3 FILENAME [-d | --delete] ARGUMENTS`` (*) replacing "FILENAME" with the name of the script. -d (or --delete, use the one you prefer) is **optional**: when used the script will **remove songs** in the playlist directory not belonging to it. "ARGUMENTS" is the list of **videos/playlists to be downloaded** and must be formatted this way:
  
    ID [DIRECTORY] - ID [DIRECTORY] - ... - ID [DIRECTORY]
Here "ID" represents the playlist or video id; "DIRECTORY" is **optional**, represents the directory in which to save the song(s), and defaults to ``./`` for videos and ``./ID/`` for playlists. For example (command line commands):

    > cd C:/playlist-downloader/
    > python3 playlist-downloader.py --delete z-teFykRk0Y ./my_songs/ - PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C
(*) Note that the command used for Python is **not always** ``python3``: it could be ``py``, ``python`` or others too.

## Result
After the process finishes the folders ``my_songs`` (containing ``Jim Yosef - Smile [Fairytale].mp3``) and ``PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C`` (containing the playlist) should be in the **directory the script is executed in**. 

# Requirements
  * Requires **[Python 3.6.6+](https://www.python.org/downloads/release/python-370/)** installed (I didn't test older versions). 
  * Requires the following **modules** installed: [google-api-python-client](https://pypi.org/project/google-api-python-client/); [mutagen](https://pypi.org/project/mutagen/).  
  [Install them using pip](https://packaging.python.org/tutorials/installing-packages/).
  * Requires a Google **API Key** registered for "**YouTube Data API v3**" to be saved in a file named ``playlist-downloader-devkey.txt`` placed in the directory the script is executed in.
    To get a Google API Key for Youtube follow [this](https://developers.google.com/youtube/v3/getting-started) tutorial.

# Notes and known issues
  * The songs should be downloaded at the **highest quality**, as [ConvertMP3 states](http://www.convertmp3.io/):
    > MP3s will always be provided in the highest quality available (based on the maximum audio quality of the video, usually 256 kbps).
  * To check if the song has already been downloaded uses the **video id** (saved in ID3 metadata as ``albumartist``) and **not the file name**.
  * Video ids (**11** chars) and playlist ids (**34** chars) are automatically distinguished based on their **length**.
  * When downloading more videos with the exact same name only the **first one** is going to be **downloaded**, and it's going to be saved using the **metadata of the last one**.
  * It can happen that **ConvertMP3 fails to convert** a video (probably for **copyright or location reasons**), even when trying manually, so in that case the script **saves in the song file the response** from ConvertMP3 (usually an HTML page).
