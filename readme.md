# SLyP - Spotify Lyrics Printer
SLyP is a terminal-based program that prints the lyrics for the song you're currently listening to (on spotify)
## Usage
### Windows
```powershell
python main.py song_name artist_name
```
### Linux
```bash
python3 main.py song_name artist_name
```
- `song_name`: specifies the song to be played
- `artist_name`: specifies the artist of the song

If any of these arguments isn't specified, the program will enter live mode, playing the lyrics from the currently playing song on spotify
## How it works
The program fetches the songs' data from [lrclib.net](https://lrclib.net) and then tries fecthing data from `lyricsplus`, a smaller library that can provide word for word lyrics
## Requirements
You need to have python installed on your machine and also the `PyYAML` module