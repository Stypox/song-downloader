# The tool
### Downloads an entire youtube playlist (or single videos) in **mp3 format**, **parsing and saving** ID3 metadata: **artist**, **name**, track number... If the song has already been downloaded only updates its metadata.
### Uses the API of an online downloader ([ConvertMp3](https://convertmp3.io)) so **only the audio data is downloaded**.
I downloaded my ~150 songs playlist and it worked fine except for one video (ConvertMp3 fails to convert it, even if I try manually, probably for copyright reasons).

# [ID3 metadata](https://en.wikipedia.org/wiki/ID3)
#### Imagine a video (id ``0a1b3c4d5e6``) titled<br/>``ArtistName feat. Ft1 | SongName [Rel release](Remixer ft. Ft2 remix)``<br/>being the second video of a playlist (id ``1234567890abcdefghijklmnopqrstuvwx``); the song ID3 metadata would be:
    "artist": "Remixer (original by ArtistName)"
    "title": "SongName (remix)"
    "tracknumber" = "1"
    "album" = "1234567890abcdefghijklmnopqrstuvwx"
    "albumartist": "0a1b3c4d5e6"
### Yes, "albumartist" is the video id. "tracknumber" is 1 because the video is the second one of the playlist

# Usage
Choose some videos and playlists to download (for example [this video](https://www.youtube.com/watch?v=z-teFykRk0Y) and [this playlist](https://www.youtube.com/playlist?list=PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C)) and **extract their ids** (in this case "z-teFykRk0Y" and "PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C").  

Then there are **two ways** to proceed, using a file or using the terminal:

  * In the directory the script is in create a file named ``playlist-downloader-ids.txt``. In that file you can insert the **videos/playlists to be downloaded** this way:

        ID (opt)DIRECTORY
        ID (opt)DIRECTORY
        ...
    Here "ID" represents the playlist or video id, and "DIRECTORY" represents the directory in which to save the song(s). "DIRECTORY" is **optional** and defaults to ``./`` for videos and ``./ID/`` for playlists. Save the file and run the script. In this case the file could be:

        z-teFykRk0Y ./my_songs/
        PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C

  * Open a terminal and navigate to the "DIRECTORY" the python script is in (run ``cd DIRECTORY``). Then run ``python3 FILENAME ARGUMENTS`` replacing "FILENAME" with the name of the script. "ARGUMENTS" is the **list of videos/playlists to be downloaded** and must be formatted this way:
  
        ID (opt)DIRECTORY - ID (opt)DIRECTORY - ... - ID (opt)DIRECTORY
    Here "ID" represents the playlist or video id, and "DIRECTORY" represents the directory in which to save the song(s). "DIRECTORY" is **optional** and defaults to ``./`` for videos and ``./ID/`` for playlists. For example:

        > cd C:/playlist-downloader/
        > python3 playlist-downloader.py z-teFykRk0Y ./my_songs/ - PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C
    Note that the command to invoke to use Python is **not always ``python3``** but could also be ``py`` or ``python``
#### After the process finishes the folders ``my_songs`` (containing ``Jim Yosef - Smile [Fairytale].mp3``) and ``PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C`` (containing the playlist) should be in the **directory the script is executed in**. 

# Requirements
  * #### Requires [Python 3.7](https://www.python.org/downloads/release/python-370/) installed. 
  * #### Requires the following modules installed: [google-api-python-client](); [mutagen]().
    Install them by running ``python3 -m pip install MODULE_NAME``, replacing MODULE_NAME with the name of the module to be installed. As written above: the command to invoke to use Python is **not always "python3"** but could also be "py" or "python"
  * #### Requires a Google API Key registered for "YouTube Data API v3" to be saved in a file named ``playlist-downloader-devkey.txt`` placed in the directory the script is executed in.
    To get a Google API Key for Youtube follow [this](https://developers.google.com/youtube/v3/getting-started) tutorial.

# Notes and known issues
  * The songs should be downloaded at the highest quality, as [ConvertMP3 states](http://www.convertmp3.io/):
    > MP3s will always be provided in the highest quality available (based on the maximum audio quality of the video, usually 256 kbps).
  * To check if the song has already been downloaded uses the video id (saved in ID3 metadata as ``albumartist``) and not the file name.
  * Video ids (11 chars) and playlist ids (34 chars) are automatically distinguished based on their length.
  * If trying to download more videos with the exact same name only the first one is going to be downloaded, but will contain the metadata of the last one.