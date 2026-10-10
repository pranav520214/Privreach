# PRIVREACH — 5-MINUTE MASTER LAUNCH FILM
### *"RESEARCH, CONNECTED."*
**Your Private Research Operating Environment**

---

## 1. Project Overview

This repository contains the complete production project, source assets, procedural animation generators, voiceover synthesis, sound design, and master renders for the official five-minute launch film of **Privreach**.

The film is styled as a world-class minimalist software launch campaign: elegant, architectural, technically disciplined, and grounded in the authentic product architecture.

- **Master Runtime**: Exactly **05:00.00** (300.00 Seconds | 7,200 Frames @ 24 fps)
- **Aspect Ratio**: 16:9 (1920 × 1080 Full HD Master)
- **Audio Master**: 48,000 Hz, 24-bit Stereo
- **Distribution Video Format**: H.264 MP4 (`libx264`, High Profile, Level 4.1, `-crf 18`, 320 kbps AAC)
- **Archival Intermediate Format**: Apple ProRes 422 Standard MOV (`prores_ks`, Linear PCM Audio)
- **Subtitles**: SubRip (`.srt`) and embedded MP4 timed subtitles

---

## 2. Directory Structure

```
launch_film/
├── brief/
│   ├── creative_direction.md         # Design system, color palette, typography & motion rules
│   ├── storyboard.md                 # Shot-by-shot timestamps, cues, on-screen text & voiceover
│   ├── production_notes.md           # Verification audit & technical engineering specifications
│   ├── asset_generation_prompts.md   # Generative prompts and mathematical parameter specs
│   └── audio_design_notes.md         # Voiceover timeline, harmonic score & sound design notes
├── assets/
│   ├── brand/
│   │   └── logo.png                  # Official Privreach vector logo mark (1024×1024)
│   ├── product_captures/
│   │   ├── full_workstation.png      # High-fidelity native workstation capture
│   │   ├── computational_matrix.png  # Extracted 100×100 fluid matrix component
│   │   ├── verification_panel.png    # Extracted claim audit & chat synthesis panel
│   │   └── scientific_domain_picker.png # Domain selector component
│   ├── voiceover/
│   │   ├── script.md                 # Complete verbatim voiceover script
│   │   ├── vo_scene01.wav to 06.wav  # 48kHz scene-by-scene voiceover stems
│   │   └── vo_full_master.wav        # Master 300.0s synchronized voiceover track
│   ├── music/
│   │   └── score_ambient_pulse.wav   # Custom 300.0s ambient-electronic score
│   └── sound_effects/
│       ├── ui_soft_click.wav         # Bandpass tactile UI impulse
│       ├── ui_subtle_chime.wav       # Deterministic verification dual-tone chime
│       ├── sonic_signature.wav       # Multi-octave brand resolve chime
│       └── final_soundtrack_master.wav # Master 48kHz mixed soundtrack (VO + Score + SFX)
├── scenes/
│   ├── 01_fragmentation/scene01.mp4  # Scene 01 (00:00–00:30 | 30.0s, 720 frames)
│   ├── 02_reveal/scene02.mp4         # Scene 02 (00:30–01:10 | 40.0s, 960 frames)
│   ├── 03_workspace/scene03.mp4      # Scene 03 (01:10–02:10 | 60.0s, 1440 frames)
│   ├── 04_evidence/scene04.mp4       # Scene 04 (02:10–03:30 | 80.0s, 1920 frames)
│   ├── 05_science/scene05.mp4        # Scene 05 (03:30–04:30 | 60.0s, 1440 frames)
│   └── 06_end_card/scene06.mp4       # Scene 06 (04:30–05:00 | 30.0s, 720 frames)
├── edit/
│   ├── render_utils.py               # Shared PIL/NumPy vector graphics & FFmpeg pipe helpers
│   ├── generate_voiceover.py         # Microsoft Neural TTS voiceover generator & SRT builder
│   ├── generate_audio_design.py      # Score synthesis, SFX generator & master soundtrack mixer
│   ├── render_scene01.py             # Scene 01 procedural renderer
│   ├── render_scene02.py             # Scene 02 procedural renderer
│   ├── render_scene03.py             # Scene 03 procedural renderer
│   ├── render_scene04.py             # Scene 04 procedural renderer
│   ├── render_scene05.py             # Scene 05 procedural renderer
│   ├── render_scene06.py             # Scene 06 procedural renderer
│   └── assemble_film.py              # Master timeline assembler, multiplexer & QC validator
├── exports/
│   ├── Privreach_Launch_Film_5min.mp4 # Final Master 5-Minute Distribution Video (H.264)
│   ├── Privreach_Launch_Film_Master.mov # Archival Intermediate Master (Apple ProRes 422)
│   └── privreach_launch_film.srt     # Synchronized SubRip Subtitles
└── README.md
```

---

## 3. Truthfulness & Verification Audit

In strict compliance with the **Critical Truthfulness Requirement**:
- **Verified Features**: In-process Gemma 3 1B IT local GGUF inference, SymPy/NumPy AST equation verification, PyMuPDF citation extraction, WebView2 PDF citation jumping, and live CPU/RAM/VRAM resource monitors are presented as working functionality.
- **Conceptual Features**: Broad multi-domain vision diagrams (kinematic robotic arms, tensor manifolds, FEA stress trusses) are explicitly framed as the project's forward-looking scientific roadmap rather than existing working tools.
- **Zero Mock Data**: No simulated benchmarks or fabricated privacy guarantees are shown.

---

## 4. How to Reopen, Revise, and Re-Render

The entire film is 100% deterministic, script-driven, and reproducible. Any component can be modified and re-rendered in seconds.

### Prerequisites
- Python 3.11+
- FFmpeg (on system `PATH`)
- `edge-tts`, `numpy`, `scipy`, `pillow` (installed via pip)

### Step 1: Revise Voiceover or Script
To change wording or adjust narration speed:
1. Edit text or rate in [`launch_film/edit/generate_voiceover.py`](file:///E:/PrivreachOS/launch_film/edit/generate_voiceover.py).
2. Run:
   ```powershell
   python launch_film\edit\generate_voiceover.py
   ```
   This regenerates all voiceover stems, master timeline track, and `privreach_launch_film.srt`.

### Step 2: Revise Music or Sound Effects
To adjust background score volume, chord progressions, or sound effects:
1. Modify [`launch_film/edit/generate_audio_design.py`](file:///E:/PrivreachOS/launch_film/edit/generate_audio_design.py).
2. Run:
   ```powershell
   python launch_film\edit\generate_audio_design.py
   ```
   This outputs `final_soundtrack_master.wav` with ducking and synchronized SFX.

### Step 3: Re-Render Individual Scenes
Each scene can be modified and re-rendered independently:
```powershell
python launch_film\edit\render_scene01.py  # 30.0s (720 frames)
python launch_film\edit\render_scene02.py  # 40.0s (960 frames)
python launch_film\edit\render_scene03.py  # 60.0s (1440 frames)
python launch_film\edit\render_scene04.py  # 80.0s (1920 frames)
python launch_film\edit\render_scene05.py  # 60.0s (1440 frames)
python launch_film\edit\render_scene06.py  # 30.0s (720 frames)
```

### Step 4: Re-Assemble Master Film
To concatenate all scenes, multiplex audio, embed subtitles, and run Quality Control:
```powershell
python launch_film\edit\assemble_film.py
```
Outputs:
`E:\PrivreachOS\launch_film\exports\Privreach_Launch_Film_5min.mp4`

---

## 5. Master Specifications & Quality Control Report

```
Duration: 00:05:00.00 (300.000000 Seconds)
Frame Rate: 24.000 fps (CFR)
Total Frames: 7,200
Video Stream: H.264 High Profile @ 1920×1080 (16:9), YUV 4:2:0 Progressive
Audio Stream: AAC 320 kbps Stereo @ 48,000 Hz
Subtitles: mov_text / SubRip timed track
Campaign Motto: RESEARCH, CONNECTED.
Official Link: https://github.com/pranav520214/Privreach
```
