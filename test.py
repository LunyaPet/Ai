from pprint import pprint

import yt_dlp

ydl = yt_dlp.YoutubeDL()

info = ydl.extract_info("https://tiktok.com/@grl.uwu", download=False, process=False)

i = 0

for j in info["entries"]:
    pprint(j)

    i = i + 1
    if i > 10:
        break
