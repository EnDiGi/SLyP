import urllib.parse
import requests
import yaml
import sys
import time
import platform
import subprocess

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


class LyricsPlayer:
    def __init__(self):
        self.maxCharDuration = 0.08
        self.playing = False

    def playSong(self, song, shift=0.0):
        print()
        if song.lyrics == []: 
            print(f"No lyrics found for {song}!")
            return
        print(f"Now playing \033[92m{song}\033[0m (source: {song.lyrics.source})")
        self.playing = True
        startTime = time.perf_counter() - shift
        for line in song.lyrics.lines:
            
            if song.lyrics.source == "lrclib":
                startMs = line["start_ms"]
                text = line["text"]
                
                if("end_ms" in line): 
                    endMs = line["end_ms"]
                else:
                    break

                if (time.perf_counter() - startTime)*1000 > endMs: 
                    continue
                

                while startMs >= (time.perf_counter() - startTime)*1000:
                    time.sleep(0.001)
                
                
                duration = endMs - startMs
                charDuration = 100000
                if len(text) != 0:
                    charDuration = duration / len(text) / 1000

                charDuration = min(charDuration, self.maxCharDuration)

                if (time.perf_counter() - startTime)*1000 > (2*startMs+endMs)/3: # ms now > 1/3 of duration
                    charDuration = 0.02

                for char in text:
                    print(char, end="", flush=True)
                    time.sleep(charDuration)
                print()

            else:

                duration = line["duration"]
                startMs = line["time"]
                text = line["text"]

                if (time.perf_counter() - startTime)*1000 > startMs + duration: 
                    continue

                while startMs / 1000 >= time.perf_counter() - startTime:
                    time.sleep(0.001)

                if line["syllabus"] != []:
                    for word in line["syllabus"]:
                        duration = word["duration"]
                        startMs = word["time"]
                        text = word["text"]

                        while startMs / 1000 >= time.perf_counter() - startTime:
                            time.sleep(0.001)

                        for char in text:
                            charDuration = duration / len(text) / 1000
                            print(char, end="", flush=True)
                            time.sleep(charDuration)
                        print(" ", end="", flush=True)
                    print()
                else:
                    charDuration = 0.070
                    if len(text) != 0:
                        charDuration = duration / len(text) / 1000

                    for char in text:
                        print(char, end="", flush=True)
                        time.sleep(charDuration)
                    print()

        self.playing = False
        print("\nSong ended!\n")


class Lyrics:
    def __init__(self, lines, src):
        self.lines = lines
        self.source = src


class Song:
    def __init__(self, name: str, artist: str, album:str|None=None, duration:float|None=None):
        self.name : str = name
        self.artist : str = artist
        self.album  : str | None = album
        self.duration : float | None = duration
        
        self.lyrics = []

        self.data = self.fetchData()

        if self.data == {}:
            print("no data")
            return
        
        if self.data["lrclib"] != {}:
            self.name = self.data["lrclib"]["trackName"]
            self.artist = self.data["lrclib"]["artistName"]
            self.album = self.data["lrclib"]["albumName"]
            self.duration = self.data["lrclib"]["duration"]
            
            yamlOut = yaml.safe_load(self.data["lrclib"]["lyricsfile"])

            self.lyrics = Lyrics(yamlOut["lines"], "lrclib")

        if self.data["lyricsplus"] != {}:
            
            self.name = self.data["lyricsplus"]["metadata"]["title"]
            self.artist = self.data["lyricsplus"]["metadata"]["artist"]
            self.album = self.data["lyricsplus"]["metadata"]["album"]
            self.duration = self.data["lyricsplus"]["metadata"]["totalDuration"]
            
            
            self.lyrics = Lyrics(self.data["lyricsplus"]["lyrics"], "lyricsplus")
        

    def fetchData(self):

        def makeRequest(url, customSiteName=""):

            try:
                response = requests.get(url, headers=headers, timeout = 1)

                if response.status_code == 200:
                    print(f"Song successfully loaded from {customSiteName}!")
                    return response.json()
                else:
                    print(f"Error fetching {customSiteName}: {response.status_code}")
                
            except requests.exceptions.Timeout:
                print(customSiteName, "API took too long to respond")
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
            return {}

        lrclibUrl = "https://lrclib.net/api/get?"
        lyricsplusUrl = "https://lyricsplus.binimum.org/v2/lyrics/get?"

        formattedArtistName = urllib.parse.quote_plus(self.artist).lower()
        formattedSongName = urllib.parse.quote_plus(self.name).lower()

        # print(f"{formattedSongName=},    {formattedArtistName=}")

        parameters = f"artist_name={formattedArtistName}&track_name={formattedSongName}"

        if self.album is not None:
            formattedAlbumName = urllib.parse.quote_plus(self.album)
            parameters += f"&album_name={formattedAlbumName}"
        if self.duration is not None:
            parameters += f"&duration={self.duration}"

        url = lrclibUrl + parameters

        data = {}

        data["lrclib"] = makeRequest(url, "lrclib")

        lyricsplusParameters = f"artist={formattedArtistName}&title={formattedSongName}"

        url = lyricsplusUrl + lyricsplusParameters

        data["lyricsplus"] = makeRequest(url, "lyricsplus")

        return data

    def __str__(self):
        return self.name + " - " + self.artist


def getMediaInfo():
    
    title, artist, position_sec = "", "", 0.0

    try:
        
        operatingSystem = platform.system()
        
        if(operatingSystem == "Linux"):
        
            output = (
                subprocess.check_output(
                    [
                        "playerctl",
                        "metadata",
                        "--format",
                        "{{title}}|{{artist}}|{{position}}",
                    ],
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )

            title, artist, pos_micros = output.split("|")
            
            position_sec = int(pos_micros) / 1000000
        
        elif operatingSystem == "Windows":
            output = (
                subprocess.check_output(
                    [
                        "powershell.exe", 
                        "-ExecutionPolicy", 
                        "Bypass", 
                        "-File", 
                        "./getPlayerInfoWindows.ps1"
                    ]
                )
                .decode("utf-8")
                .strip()
            )
            
            title, artist, positionSecStr = output.split("|")

            position_sec = float(positionSecStr)        
            
            
    except Exception:
        pass
    finally:
        return title, artist, position_sec


def main():

    deltaTime = 0.5

    player = LyricsPlayer()

    currentSong = None
    
    if len(sys.argv) > 2:
        currentSong = Song(sys.argv[1], sys.argv[2])
        player.playSong(currentSong)
        return 0
    
    lastTitle = ""
    
    try:
        while True:
            
            start = time.perf_counter()
            title, artist, timeSec = getMediaInfo()

            if(
                title == "" and
                artist == "" and
                timeSec == 0.0
            ):
                print("Waiting for a song to play...", end = "\r")
                time.sleep(deltaTime)
                continue
                    
            if(lastTitle == title or not title):
                print("Waiting for a new song to play...", end = "\r")
                time.sleep(deltaTime)
                continue

            currentSong = Song(title, artist)
            
            lastTitle = currentSong.name

            print()
            player.playSong(currentSong, timeSec + (time.perf_counter() - start))
                
                
    except KeyboardInterrupt:
        print("\nProgram termined")

if __name__ == "__main__":
    main()