# Background Music

## Audio Extraction Required

To extract audio from the video files:

1. Install ffmpeg: https://ffmpeg.org/download.html
2. Run:
   ```bash
   cd "C:\Users\irfan\Downloads"
   ffmpeg -i "Asset_Production_and_Delivery_Notes.mp4" -vn -acodec libmp3lame -q:a 2 background-music.mp3
   ```
3. Copy the resulting `background-music.mp3` to this directory

Alternatively, use an online tool like CloudConvert or Audacity to extract the audio track.
