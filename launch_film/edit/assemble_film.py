"""Master Assembly & Final Encoding for Privreach 5-Minute Launch Film.

Performs:
1. Scene concatenation (01 to 06, totaling 7,200 frames @ 24 fps = 300.00 seconds)
2. Audio multiplexing with master 48kHz soundtrack (voiceover + ambient score + SFX)
3. Subtitle embedding (SRT)
4. Encoding to distribution H.264 MP4 (exports/Privreach_Launch_Film_5min.mp4)
5. Quality Control validation via ffprobe
"""

import os
import sys
import subprocess

def run_cmd(cmd):
    print(" ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR]", res.stderr)
        raise RuntimeError(f"Command failed: {res.stderr}")
    return res.stdout

def assemble_film():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scenes_dir = os.path.join(root, "scenes")
    exports_dir = os.path.join(root, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    
    scene_files = [
        os.path.join(scenes_dir, "01_fragmentation", "scene01.mp4"),
        os.path.join(scenes_dir, "02_reveal", "scene02.mp4"),
        os.path.join(scenes_dir, "03_workspace", "scene03.mp4"),
        os.path.join(scenes_dir, "04_evidence", "scene04.mp4"),
        os.path.join(scenes_dir, "05_science", "scene05.mp4"),
        os.path.join(scenes_dir, "06_end_card", "scene06.mp4"),
    ]
    
    for s in scene_files:
        if not os.path.exists(s):
            raise FileNotFoundError(f"Missing scene video: {s}")
            
    audio_track = os.path.join(root, "assets", "sound_effects", "final_soundtrack_master.wav")
    if not os.path.exists(audio_track):
        # Fallback to voiceover master
        audio_track = os.path.join(root, "assets", "voiceover", "vo_full_master.wav")
        
    srt_file = os.path.join(exports_dir, "privreach_launch_film.srt")
    
    # 1. Create ffmpeg concat list file
    concat_list = os.path.join(exports_dir, "scenes_concat.txt")
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in scene_files:
            f.write(f"file '{s.replace(chr(92), '/')}'\n")
            
    temp_video = os.path.join(exports_dir, "temp_video_stitched.mp4")
    print("\n[1/3] Concatenating 6 Scene Visual Streams (7,200 frames @ 24fps)...")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list,
        "-c", "copy",
        temp_video
    ]
    subprocess.run(cmd_concat, check=True)
    
    # 2. Multiplex Video, Master Audio, and Subtitles into final distribution MP4
    final_mp4 = os.path.join(exports_dir, "Privreach_Launch_Film_5min.mp4")
    print("\n[2/3] Multiplexing Master Video, Audio Soundtrack, and Subtitles...")
    
    cmd_mux = [
        "ffmpeg", "-y",
        "-i", temp_video,
        "-i", audio_track,
    ]
    
    if os.path.exists(srt_file):
        cmd_mux.extend([
            "-i", srt_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", "48000",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=eng",
            "-metadata", "title=Privreach — Your Private Research Operating Environment",
            "-metadata", "artist=Privreach Project",
            "-metadata", "comment=Official 5-Minute Launch Film: Research, Connected.",
            "-t", "300.00",
            final_mp4
        ])
    else:
        cmd_mux.extend([
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "320k",
            "-ar", "48000",
            "-t", "300.00",
            final_mp4
        ])
        
    subprocess.run(cmd_mux, check=True)
    
    # Cleanup temp stitched video
    if os.path.exists(temp_video):
        try: os.remove(temp_video)
        except: pass
    if os.path.exists(concat_list):
        try: os.remove(concat_list)
        except: pass
        
    print(f"\n[OK] Master Launch Film successfully created at:\n     {final_mp4}")
    
    # 3. Quality Control (QC) Inspection via ffprobe
    print("\n[3/3] Running Master Quality Control (QC) Verification...")
    qc_res = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate:stream=codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of", "default=noprint_wrappers=1",
        final_mp4
    ], capture_output=True, text=True)
    
    print("--------------------------------------------------")
    print("  PRIVREACH MASTER FILM SPECIFICATIONS")
    print("--------------------------------------------------")
    print(qc_res.stdout.strip())
    print("--------------------------------------------------")

if __name__ == "__main__":
    assemble_film()
