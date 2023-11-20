from utils import *
from termcolor import colored

# IMPORTANT: Check for existing folders
check_dirs()

"""
How this works:

1. Get Video URL from user
2. Download video
3. Extract audio
4. Transcribe audio
5. Get interesting parts of video using GPT by providing it transcript with timestamps
7. Cut video into interesting parts from original video
8. Transcribe each interesting part video
9. Generate subtitles for each interesting part video
10. Add subtitles to each interesting part video
11. Save each interesting part video to "output" folder
12. Done!
"""

# 1. Get Inputs from user
print(colored("Enter a YouTube video URL > ", "green"), end="")
video_url = input()

print(colored("Enter a maximum number of characters per line/frame > ", "green"), end="")
max_chars = int(input())

print(colored("Enter the path of your fonts folder > ", "green"), end="")
fonts_path = input()

print(colored("Enter your preferred font size > ", "green"), end="")
font_size = int(input())

print(colored("Enter your preferred font color (HEX) > ", "green"), end="")
font_color = input()

print(colored("Enter your preferred stroke color (HEX) > ", "green"), end="")
stroke_color = input()

print(colored("Enter your preferred stroke width > ", "green"), end="")
stroke_width = input()

print()

# 2. Download video
print(colored("[*] Downloading video...", "yellow"))
video_path = download(video_url)
print(colored(f"[+] Video downloaded: {video_path}", "green"))
print()

# 3. Extract audio
print(colored("[*] Extracting audio from initial video...", "yellow"))
extracted_audio_path = extract_audio(video_path)
print(colored(f"[+] Audio extracted: {extracted_audio_path}", "green"))
print()

# 4. Transcribe audio
print(colored("[*] Transcribing audio...", "yellow"))
initial_audio_transcript_path = \
    generate_transcript(audio_path=extracted_audio_path, max_chars=max_chars)
print(colored(f"[+] Initial Audio transcribed: {initial_audio_transcript_path}", "green"))
print()

# 5. Get interesting parts of video using GPT by providing it transcript with timestamps
print(colored("[*] Fetching interesting parts of video...", "yellow"))
srt_contents = open(initial_audio_transcript_path, "r").read()
interesting_part = query(srt_contents, max_chars)
print(colored(f"[+] Interesting parts fetched: {interesting_part}", "green"))

# (Quickly save interesting part SRT to a file)
interesting_part_srt_path = os.path.join("output", "interesting_part.srt")
with open(interesting_part_srt_path, "w") as f:
    f.write(interesting_part)
equalize(interesting_part_srt_path, max_chars)

print(colored(f"[+] Interesting parts saved to: {interesting_part_srt_path}", "green"))

# 6. Cut video into interesting parts from original video
print(colored("[*] Cutting video into interesting parts...", "yellow"))
interesting_part_video_path = cut_video(video_path, interesting_part_srt_path)
print(colored(f"[+] Interesting parts video saved to: {interesting_part_video_path}", "green"))

# 7. Refactor video into TikTok Resolution
print(colored("[*] Refactoring video resolution...", "yellow"))
refactored_video_path = refactor_video(interesting_part_video_path)
print(colored(f"[+] Video refactored: {refactored_video_path}", "green"))

# 8. Adding subtitles to video
print(colored("[*] Adding subtitles to video...", "yellow"))
subtitled_video_path = \
    add_subtitles(refactored_video_path, interesting_part_srt_path, fonts_path, font_size, font_color, stroke_color, stroke_width)
print(colored(f"[+] Subtitled video saved to: {subtitled_video_path}", "green"))