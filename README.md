## The tool
### Downloads an entire youtube playlist in mp3 format.
###### I downloaded my ~145 songs playlist and it worked fine except for one song (ConvertMp3 fails to download the video, probably for privacy reasons).  
  
#### Here is the process:  

1. Using Google's api the tool retrieves all the videos' ids from a playlist.
2. All the songs are downloaded in mp3 format using [ConvertMp3](https://convertmp3.io)
3. After successfully donwloading a song its eyeD3 tags are edited:
   * It automatically finds the song title, the song author and if it is a remix based on the video title.
   * Saves on "#" (that is the track number) the song position in the playlist
   * Saves on "album" the playlist link and on "album artist" the video link (this isn't the best solution but I don't know where to put the video id)
4. Then the video id is stored in a file ("downloaded.txt"), so that when closing and reopening the program only the remaining songs are downloaded, not all the playlist all over again.
5. Every time the tool is opened all tags are updated, so that if a song was renamed or a video position changed all is up-to-date.  
  
## File requirements
Requires a YouTube developer key, that has to be saved in a file named "devkey.txt" in the same folder as the python file; the playlist id has to be saved inside "playlist.txt"; the folder that contains the program should not contain a file called "downloaded.txt", since it is used by it
