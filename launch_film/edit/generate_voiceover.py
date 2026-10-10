"""Generate studio-grade voiceover for Privreach 5-Minute Launch Film using edge-tts.

Produces:
- Scene-by-scene audio files (vo_scene01.mp3 to vo_scene06.mp3)
- Converted WAV masters
- Master 300.00-second timeline voiceover track (vo_full_master.wav)
- SubRip subtitle file (privreach_launch_film.srt)
"""

import os
import sys
import asyncio
import subprocess

VOICE = "en-US-ChristopherNeural"
RATE = "-3%" # calm, measured, intelligent

SCENE_VOICEOVERS = {
    1: {
        "title": "SCENE 01 — THE FRAGMENTATION",
        "start_time": 0.0,
        "window_duration": 30.0,
        "offset": 0.5,
        "rate": "+2%", # Slightly brisker to fit neatly inside 00:00-00:30 with tail pause
        "text": (
            "Research begins with a question. "
            "Then come the papers. The datasets. The equations. The experiments. "
            "The notes scattered across different tools. "
            "Each piece holds part of the picture. "
            "But connecting them takes time. "
            "And the more complex the question, the harder it becomes to keep the evidence, "
            "the process, and the result together. "
            "What if research could feel more connected?"
        )
    },
    2: {
        "title": "SCENE 02 — THE REVEAL",
        "start_time": 30.0,
        "window_duration": 40.0,
        "offset": 1.5,
        "text": (
            "Introducing Privreach. "
            "A private research operating environment designed to bring scientific information, "
            "computational tools, and research workflows into one workspace. "
            "Not just a place to ask a question. "
            "A place to work through one. "
            "From the first source to the next calculation, from an emerging idea to a result you can examine. "
            "One environment, built around the work of research."
        )
    },
    3: {
        "title": "SCENE 03 — INSIDE THE WORKSPACE",
        "start_time": 70.0,
        "window_duration": 60.0,
        "offset": 1.5,
        "text": (
            "A research project is more than a conversation. "
            "It is a collection of sources, questions, assumptions, calculations, and decisions. "
            "Privreach is designed to bring these elements into a shared workspace. "
            "Explore research by domain. Organize the material behind a question. "
            "Move between documents, visualizations, and computational views. "
            "The interface gives complex work room to breathe. "
            "A computational matrix offers a visual language for patterns, processes, and scientific data. "
            "And a modular workspace creates room for different ways of exploring a problem. "
            "The aim is simple: less fragmentation, clearer context, and a more coherent research process."
        )
    },
    4: {
        "title": "SCENE 04 — FROM SOURCE TO INSIGHT",
        "start_time": 130.0,
        "window_duration": 80.0,
        "offset": 2.0,
        "text": (
            "Good research does not end with an answer. "
            "It asks where the answer came from. "
            "Begin with a source document. Extract its contents. "
            "Find the passages relevant to your question. "
            "Keep the evidence connected to the claims it supports. "
            "Then move from information to analysis. "
            "Where a calculation is needed, use a defined method. "
            "Where assumptions matter, make them visible. "
            "Where evidence is incomplete, leave room for uncertainty. "
            "The goal is not to make every result look certain. "
            "It is to make the path to a result easier to inspect. "
            "A source. A question. A method. An output. "
            "Each step should have a clear role. "
            "Because an answer is more useful when you can understand how it was reached."
        )
    },
    5: {
        "title": "SCENE 05 — THE LARGER VISION",
        "start_time": 210.0,
        "window_duration": 60.0,
        "offset": 1.8,
        "text": (
            "Scientific questions rarely fit neatly inside one discipline. "
            "Aerospace connects with physics. Biology intersects with computation. "
            "Robotics draws on mathematics, materials, and engineering. "
            "Privreach is being developed with this breadth of research in mind. "
            "A shared environment for exploring ideas, working with scientific information, "
            "and bringing different tools into a connected process. "
            "Some workflows will be simple. "
            "Others will demand more computation, more evidence, and more careful verification. "
            "The ambition is to make that complexity easier to navigate—without losing sight of the underlying work."
        )
    },
    6: {
        "title": "SCENE 06 — THE LAUNCH",
        "start_time": 270.0,
        "window_duration": 30.0,
        "offset": 1.5,
        "text": (
            "Research deserves more than disconnected tools. "
            "It deserves a process you can follow, evidence you can examine, "
            "and a workspace built around the questions that matter. "
            "This is Privreach. "
            "Your private research operating environment. "
            "Research, connected. "
            "Explore Privreach on GitHub."
        )
    }
}

async def generate_scene_vo(scene_num, info, out_dir):
    import edge_tts
    mp3_path = os.path.join(out_dir, f"vo_scene{scene_num:02d}.mp3")
    wav_path = os.path.join(out_dir, f"vo_scene{scene_num:02d}.wav")
    print(f"[*] Synthesizing Scene {scene_num:02d} narration...")
    rate = info.get("rate", RATE)
    communicate = edge_tts.Communicate(info["text"], VOICE, rate=rate)
    await communicate.save(mp3_path)
    
    # Convert to 48kHz WAV via ffmpeg
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_path,
        "-ar", "48000", "-ac", "2",
        wav_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Get duration using ffprobe
    res = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", wav_path
    ], capture_output=True, text=True)
    dur = float(res.stdout.strip())
    print(f"    [OK] Scene {scene_num:02d} duration: {dur:.2f}s (allocated window: {info['window_duration']}s)")
    return dur

def format_srt_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    if ms >= 1000:
        s += 1
        ms -= 1000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def build_srt_subtitles(srt_path):
    subtitles = [
        # Scene 1 (00:00 - 00:30)
        (1.2, 3.5, "Research begins with a question."),
        (3.8, 8.5, "Then come the papers. The datasets. The equations. The experiments."),
        (8.8, 12.0, "The notes scattered across different tools."),
        (12.3, 15.0, "Each piece holds part of the picture."),
        (15.4, 18.2, "But connecting them takes time."),
        (18.6, 24.5, "And the more complex the question, the harder it becomes to keep the evidence, the process, and the result together."),
        (25.0, 28.5, "What if research could feel more connected?"),
        
        # Scene 2 (00:30 - 01:10)
        (31.5, 34.0, "Introducing Privreach."),
        (34.5, 41.5, "A private research operating environment designed to bring scientific information, computational tools, and research workflows into one workspace."),
        (42.0, 45.0, "Not just a place to ask a question."),
        (45.5, 48.0, "A place to work through one."),
        (48.5, 54.5, "From the first source to the next calculation, from an emerging idea to a result you can examine."),
        (55.0, 59.5, "One environment, built around the work of research."),
        
        # Scene 3 (01:10 - 02:10)
        (71.5, 75.0, "A research project is more than a conversation."),
        (75.5, 81.0, "It is a collection of sources, questions, assumptions, calculations, and decisions."),
        (81.5, 86.5, "Privreach is designed to bring these elements into a shared workspace."),
        (87.0, 92.5, "Explore research by domain. Organize the material behind a question."),
        (93.0, 98.0, "Move between documents, visualizations, and computational views."),
        (98.5, 102.5, "The interface gives complex work room to breathe."),
        (103.0, 109.5, "A computational matrix offers a visual language for patterns, processes, and scientific data."),
        (110.0, 115.5, "And a modular workspace creates room for different ways of exploring a problem."),
        (116.0, 124.0, "The aim is simple: less fragmentation, clearer context, and a more coherent research process."),
        
        # Scene 4 (02:10 - 03:30)
        (132.0, 135.5, "Good research does not end with an answer."),
        (136.0, 139.0, "It asks where the answer came from."),
        (139.5, 144.5, "Begin with a source document. Extract its contents."),
        (145.0, 148.5, "Find the passages relevant to your question."),
        (149.0, 154.0, "Keep the evidence connected to the claims it supports."),
        (154.5, 158.0, "Then move from information to analysis."),
        (158.5, 163.0, "Where a calculation is needed, use a defined method."),
        (163.5, 168.0, "Where assumptions matter, make them visible."),
        (168.5, 173.0, "Where evidence is incomplete, leave room for uncertainty."),
        (173.5, 178.0, "The goal is not to make every result look certain."),
        (178.5, 183.0, "It is to make the path to a result easier to inspect."),
        (183.5, 188.0, "A source. A question. A method. An output."),
        (188.5, 192.5, "Each step should have a clear role."),
        (193.0, 199.5, "Because an answer is more useful when you can understand how it was reached."),
        
        # Scene 5 (03:30 - 04:30)
        (211.8, 216.5, "Scientific questions rarely fit neatly inside one discipline."),
        (217.0, 222.0, "Aerospace connects with physics. Biology intersects with computation."),
        (222.5, 228.0, "Robotics draws on mathematics, materials, and engineering."),
        (228.5, 234.0, "Privreach is being developed with this breadth of research in mind."),
        (234.5, 241.5, "A shared environment for exploring ideas, working with scientific information, and bringing different tools into a connected process."),
        (242.0, 245.5, "Some workflows will be simple."),
        (246.0, 252.0, "Others will demand more computation, more evidence, and more careful verification."),
        (252.5, 261.0, "The ambition is to make that complexity easier to navigate—without losing sight of the underlying work."),
        
        # Scene 6 (04:30 - 05:00)
        (271.5, 275.5, "Research deserves more than disconnected tools."),
        (276.0, 282.5, "It deserves a process you can follow, evidence you can examine, and a workspace built around the questions that matter."),
        (283.0, 285.5, "This is Privreach."),
        (286.0, 289.0, "Your private research operating environment."),
        (289.5, 292.0, "Research, connected."),
        (292.5, 296.0, "Explore Privreach on GitHub.")
    ]
    
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (st, en, txt) in enumerate(subtitles, 1):
            f.write(f"{i}\n")
            f.write(f"{format_srt_time(st)} --> {format_srt_time(en)}\n")
            f.write(f"{txt}\n\n")
    print(f"[OK] SubRip subtitles written to {srt_path}")

async def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    vo_dir = os.path.join(root, "assets", "voiceover")
    os.makedirs(vo_dir, exist_ok=True)
    
    durations = {}
    for s_num, s_info in SCENE_VOICEOVERS.items():
        dur = await generate_scene_vo(s_num, s_info, vo_dir)
        durations[s_num] = dur
        
    print("\n[*] Assembling Master 300.00-Second Voiceover Track...")
    # Use ffmpeg adelay and amix to create exact master audio timeline of 300.0s
    filter_inputs = []
    filter_delay = []
    
    for s_num, s_info in SCENE_VOICEOVERS.items():
        wav_path = os.path.join(vo_dir, f"vo_scene{s_num:02d}.wav").replace("\\", "/")
        delay_ms = int((s_info["start_time"] + s_info["offset"]) * 1000)
        filter_inputs.extend(["-i", wav_path])
        idx = s_num - 1
        filter_delay.append(f"[{idx}:a]adelay={delay_ms}|{delay_ms}[a{s_num}];")
        
    mix_line = "".join([f"[a{s}]" for s in SCENE_VOICEOVERS.keys()]) + f"amix=inputs={len(SCENE_VOICEOVERS)}:dropout_transition=0:normalize=0,apad=whole_dur=300,atrim=0:300[aout]"
    full_filter = "".join(filter_delay) + mix_line
    
    master_vo_wav = os.path.join(vo_dir, "vo_full_master.wav")
    cmd = [
        "ffmpeg", "-y"
    ] + filter_inputs + [
        "-filter_complex", full_filter,
        "-map", "[aout]",
        "-ar", "48000", "-ac", "2",
        master_vo_wav
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[OK] Master voiceover assembled: {master_vo_wav}")
    
    # Subtitles
    srt_path = os.path.join(root, "exports", "privreach_launch_film.srt")
    os.makedirs(os.path.dirname(srt_path), exist_ok=True)
    build_srt_subtitles(srt_path)

if __name__ == "__main__":
    asyncio.run(main())
