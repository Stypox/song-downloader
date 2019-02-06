# Song downloader
Downloads an entire youtube playlist (or single videos) in **mp3 format**, **deducing** and saving **artist**, **name**, **remixer**, **tracknumber**... If the song has already been downloaded updates only its metadata.  

**Only the audio data is downloaded**.
##### I downloaded a ~150 songs playlist and it worked fine. I also developed an [mp3-player](https://github.com/Stypox/mp3-player), that can play playlists in order and save favourites.

# [ID3 metadata](https://en.wikipedia.org/wiki/ID3) and title parsing
Imagine a playlist (id ``1234567890abcdefghijklmnopqrstuvwx``) whose second video (id ``0a1b2c3d4e5``) is titled<br/>``ArtistName feat. Ft1 | SongName [Rel release](Remixer ft. Ft2 remix)``. The filename would be ``ArtistName feat. Ft1 | SongName [Rel release](Remixer ft. Ft2 remix)_0a1b2c3d4e5.mp3`` and the song's ID3 metadata would be:

    artist: "Remixer (original by ArtistName)"
    title: "SongName (remix)"
    tracknumber: "1"
    album: "1234567890abcdefghijklmnopqrstuvwx"

"tracknumber" is **1** because the video is the **second** one of the playlist

# Usage
Choose some videos and playlists to **download** (for example [this video](https://www.youtube.com/watch?v=z-teFykRk0Y) and [this playlist](https://www.youtube.com/playlist?list=PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C)) and **extract their ids** (in this case "z-teFykRk0Y" and "PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C").  

Then there are **two ways** to provide the script with those ids: using a **file** or using **command line arguments** (all parameters between **\[square brackets\]** are to be considered optional; **\|** means **or**):

## Saving ids in file
In the directory the script is executed in create a file named ``song-downloader-ids.txt``. In that file you can insert the **videos/playlists to be downloaded** this way:

    OPTIONS
    ID [DIRECTORY]
    ID [DIRECTORY]
    ...

"OPTIONS" are some options for the script, such as ``--delete`` to delete songs that have been removed from the playlists; learn more about them by running in the terminal ``python3 FILENAME --help``. "ID" represents the playlist or video id/url; "DIRECTORY" is **optional**, represents the directory in which to save the song(s), and defaults to ``./`` for videos and ``./ID/`` for playlists. **Save the file and run** the script. In this case the file could be:

    --delete
    z-teFykRk0Y ./my_songs/
    PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C


## Passing ids as command line arguments
**Open a terminal** and navigate to the "DIRECTORY" the python script is in (run ``cd DIRECTORY``). Then run ``python3 FILENAME OPTIONS ARGUMENTS`` (*) replacing "FILENAME" with the name of the script. "OPTIONS" are some options for the script, such as ``--delete`` to delete songs that have been removed from the playlists; learn more about them by running in the terminal ``python3 FILENAME --help``. "ARGUMENTS" is the list of **videos/playlists to be downloaded** and must be formatted this way:
  
    ID [DIRECTORY] - ID [DIRECTORY] - ... - ID [DIRECTORY]

Here "ID" represents the playlist or video id/url; "DIRECTORY" is **optional**, represents the directory in which to save the song(s), and defaults to ``./`` for videos and ``./ID/`` for playlists. If a path contains spaces, you have to sorround it with ``"``. For example (command line commands):

    > cd C:/song-downloader/
    > python3 song-downloader.py --delete z-teFykRk0Y ./my_songs/ - PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C

(*) Note that the command used for Python is **not always** ``python3``: it could be ``py``, ``python``, ``python3.6`` or others too.

## Result
After the process finishes the folders ``my_songs`` (containing ``Jim Yosef - Smile [Fairytale]_z-teFykRk0Y.mp3``) and ``PLR0fgOhCSN8ilC2GWuPkipy8FRNp-m-7C`` (containing the playlist) should be in the **directory the script is executed in**. 

# Requirements
* Requires either **[Python 3.6.x](https://www.python.org/downloads/)** or **[Python 3.7.x](https://www.python.org/downloads/)** (I didn't test older versions, but newer ones may work).
* Requires the following **modules** installed: [youtube-dl](https://pypi.org/project/youtube_dl/); [mutagen](https://pypi.org/project/mutagen/).  
[Install them using pip](https://packaging.python.org/tutorials/installing-packages/).

# Notes and known issues
* The songs are downloaded at the **highest possible quality**. youtube_dl.YoutubeDL is set up to download the best format that Youtube provides ("bestaudio/best")
* To check if a song has already been downloaded uses the **video id** saved at the end of the filename, **not its file name**.
* Automatically **renames** files whose corresponding video changed name.
* Video ids and playlist ids are automatically distinguished, but if an id refers both to a playlist and to a video **only the playlist** is downloaded.
* When downloading more videos with the exact same name only the **first one** is going to be **downloaded**, and it's going to be saved using the **metadata of the last one**.
* Videos from [platforms](https://rg3.github.io/youtube-dl/supportedsites.html) other than Youtube may work, but playlists won't. If two videos/playlists from different platforms are downloaded in the same folder, the id contained in their titles may generate conflicts.
* Control characters and '``<>:\"/\|?*``' are automatically removed from filenames to prevent any problem with filesystems.
