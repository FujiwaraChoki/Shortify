import os
import requests
import assemblyai as aai

from typing import List
from pytube import YouTube
from dotenv import load_dotenv
from srt_equalizer import srt_equalizer
from moviepy.editor import VideoFileClip, TextClip

load_dotenv(".env")

ACCESS_TOKEN = os.getenv("OPENAI_ACCESS_TOKEN")

def check_dirs() -> None:
    """
    Generates directories if they don't exist.
    """
    if not os.path.exists("video"):
        os.mkdir("video")
    if not os.path.exists("audio"):
        os.mkdir("audio")
    if not os.path.exists("subtitles"):
        os.mkdir("subtitles")
    if not os.path.exists("output"):
        os.mkdir("output")

def adjust_subtitle_length(subtitle_path: str, max_chars: int = 15) -> None:
    """
    Adjusts the length of each subtitle line to a maximum number of characters.

    Args:
        subtitle_path (str): Path to subtitle file (SRT).
        max_chars (int, optional): Maximum number of characters per line. Defaults to 15.
    """
    srt_equalizer.equalize_srt_file(subtitle_path, subtitle_path, max_chars)

def generate_transcript(audio_path: str, max_chars: int = 15) -> str:
    """
    Generates Transcript for a audio file.
    
    Args:
        audio_path (str): Path to audio file.
        
    Raises:
        FileNotFoundError: If subtitle file is not found.
        EnvironmentError: If AssemblyAI API key is not found in .env.

    Returns:
        str: Path to subtitle file (SRT).
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    if not os.getenv("ASSEMBLY_AI_API_KEY"):
        raise EnvironmentError("AssemblyAI API key not found in .env.")

    # Set AssemblyAI API key
    aai.settings.api_key = os.getenv("ASSEMBLY_AI_API_KEY")

    # Transcribe audio
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path)

    # Export transcript to SRT
    subtitle_path = os.path.join("subtitles", os.path.basename(audio_path).replace(".mp3", ".srt"))

    # Export transcript to SRT
    transcript_in_srt = transcript.export_subtitles_srt()

    # Write transcript to file
    with open(subtitle_path, "w") as f:
        f.write(transcript_in_srt)

    # Equalize subtitle length
    adjust_subtitle_length(subtitle_path=subtitle_path, max_chars=max_chars)

    return subtitle_path

def remove_obstructing_characters(text: str) -> str:
    """
    Removes obstructing characters from text.

    Args:
        text (str): Text to remove obstructing characters from.

    Returns:
        str: Text with obstructing characters removed.
    """
    text = text.replace(":", "").replace("?", "").replace("!", "").replace(",", "").replace(";", "").replace("(", "").replace(")", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "").replace("<", "").replace(">", "").replace("/", "").replace("\\", "").replace("|", "").replace("-", "").replace("_", "").replace("=", "").replace("+", "").replace("*", "").replace("&", "").replace("^", "").replace("%", "").replace("$", "").replace("#", "").replace("@", "").replace(" ", "_")

    return text

def download(video_url: str) -> str:
    """
    Downloads a youtube video by URL.

    Args:
        video_url (str): URL of video.

    Raises:
        ValueError: If no video URL is provided.

    Returns:
        str: Path to downloaded video.
    """
    if not video_url:
        raise ValueError("No video URL provided.")

    # Remove obstructing characters from video title
    yt = YouTube(video_url)
    video = yt.streams.get_highest_resolution()

    # Download video
    video_path: str = video.download("video")

    return video_path

def extract_audio(video_path: str) -> str:
    """
    Extracts audio from a video file.

    Args:
        video_path (str): Path to video file.

    Raises:
        FileNotFoundError: If video file is not found.

    Returns:
        str: Path to audio file.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Generate audio path
    audio_path = os.path.join("audio", os.path.basename(video_path).replace(".mp4", ".mp3"))

    # Extract audio
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)

    return audio_path


def query(transcript: str, max_chars) -> List[dict]:
    # Refine transcript, only first 1500 characters
    refined_transcript = transcript[:20000]

    """
    Queries GPT-3.5 to get the interesting parts of a video.

    Args:
        transcript (str): Transcript of video.

    Returns:
        List[dict]: List of interesting parts of video.
    """
    prompt: str = f"""Hello ChatGPT, I have a video transcript and I want you to find one interesting part of the video for me.
Don't explain what you're doing, don't reference anything else, don't hallucinate, and don't repeat yourself.

Send me the interesting part of the video transcript in the SRT format, with each part line being max {max_chars} characters long.

Do NOT change ANYTHING, merely send me the most interesting part of the video transcript. The part's end has to make sense.

Make the part at least 7 seconds long.

Relevant transcript:
"{refined_transcript}"
"""
    
    # Query GPT-3.5
    r = requests.post("http://localhost:5000/query", json={
        "prompt": prompt,
        "accessToken": ACCESS_TOKEN
    })

    # Parse response as JSON
    response = r.json()

    # Return GPT response
    return response["message"].replace("```", "").replace("```json", "")

def equalize(path: str, max_chars: int) -> str:
    """
    Equalizes a path to SRT format.

    Args:
        path (str): path to equalize.

    Returns:
        str: Equalized path.
    """
    return srt_equalizer.equalize_srt_file(path, path, max_chars)

def cut_video(original_video_path: str, interesting_part_srt_path: str) -> str:
    """
    Cuts a video into interesting parts.

    Args:
        original_video_path (str): Path to original video.
        interesting_part_srt_path (str): Path to interesting parts SRT file.

    Raises:
        FileNotFoundError: If original video file is not found.
        FileNotFoundError: If interesting parts SRT file is not found.

    Returns:
        str: Path to interesting parts video.
    """
    if not os.path.exists(original_video_path):
        raise FileNotFoundError(f"Original video file not found: {original_video_path}")
    
    if not os.path.exists(interesting_part_srt_path):
        raise FileNotFoundError(f"Interesting parts SRT file not found: {interesting_part_srt_path}")

    # Generate interesting parts video path
    interesting_part_video_path = os.path.join("output", os.path.basename(original_video_path).replace(".mp4", "_interesting_part.mp4"))

    # Cut video
    video = VideoFileClip(original_video_path)

    first_start_time = None
    last_end_time = None

    # Get first start and  lastend times from SRT file
    with open(interesting_part_srt_path, "r") as f:
        lines = f.readlines()
        lines_with_times = []

        for line in lines:
            if line.startswith("0"):
                start = line.split(" --> ")[0]
                end = line.split(" --> ")[1]

                lines_with_times.append({
                    "start": start,
                    "end": end
                })

        first_start_time = lines_with_times[0]["start"]
        last_end_time = lines_with_times[-1]["end"]

    # Cut video
    video = video.subclip(first_start_time, last_end_time)
    video.write_videofile(interesting_part_video_path)

    return interesting_part_video_path

def refactor_video(video_path: str) -> str:
    """
    Refactors the video to TikTok/Youtube Shorts resolution.

    Args:
        video_path (str): Path to video.

    Raises:
        FileNotFoundError: If video file is not found.
    
    Returns:
        str: Path to refactored video.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Refactor video
    refactored_video_path = os.path.join("output", os.path.basename(video_path).replace(".mp4", "_refactored.mp4"))

    # Refactor video
    video = VideoFileClip(video_path)
    video = video.resize((1080, 1920))
    video.write_videofile(refactored_video_path)

    return refactored_video_path

def add_subtitles(video_path, interesting_part_srt_path, fonts_path, font_size, font_color, stroke_color, stroke_width):
    """
    Adds subtitles to a video.

    Args:
        video_path (str): Path to video.
        interesting_part_srt_path (str): Path to interesting parts SRT file.
        fonts_path (str): Path to fonts folder.
        font_size (int): Font size.
        font_color (str): Font color.
        stroke_color (str): Stroke color.
        stroke_width (int): Stroke width.

    Raises:
        FileNotFoundError: If video file is not found.
        FileNotFoundError: If interesting parts SRT file is not found.
        FileNotFoundError: If fonts folder is not found.

    Returns:
        str: Path to subtitled video.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.exists(interesting_part_srt_path):
        raise FileNotFoundError(f"Interesting parts SRT file not found: {interesting_part_srt_path}")
    
    if not os.path.exists(fonts_path):
        raise FileNotFoundError(f"Fonts folder not found: {fonts_path}")

    # Generate subtitled video path
    subtitled_video_path = os.path.join("output", os.path.basename(video_path).replace(".mp4", "_subtitled.mp4"))

    # Load video
    video = VideoFileClip(video_path)

    # Read subtitles from SRT file
    subtitles = TextClip(interesting_part_srt_path, fontsize=font_size, font=fonts_path, color=font_color, stroke_color=stroke_color, stroke_width=stroke_width)
    
    # Overlay subtitles onto the video
    video = video.subclip(0, video.duration - 1)
    video = video.set_audio(None)  # Remove audio to avoid audio/video sync issues
    video = video.set_duration(subtitles.duration)
    video = video.overlay(subtitles, position=(0, 0), times=[0])

    # Write the subtitled video to the output path
    video.write_videofile(subtitled_video_path, codec="libx264", audio_codec="aac")

    return subtitled_video_path