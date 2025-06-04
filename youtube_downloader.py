# youtube_downloader.py

from pytube import YouTube
from pydub import AudioSegment
import os

def download_audio_from_youtube(youtube_url, save_folder='songs'):
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        file_path = stream.download(output_path=save_folder)
        base, ext = os.path.splitext(file_path)
        mp3_path = base + '.mp3'

        # Convert to mp3 using pydub
        audio = AudioSegment.from_file(file_path)
        audio.export(mp3_path, format="mp3")
        os.remove(file_path)

        print(f"Downloaded and converted: {mp3_path}")
        return mp3_path
    except Exception as e:
        print(f"Error downloading: {e}")
        return None
