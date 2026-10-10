"""Generate cinematic ambient electronic score and sound effects for Privreach Launch Film.

Music Structure (300.0s @ 48kHz Stereo):
- 00:00 - 00:30 (Scene 1): Sparse, contemplative ambient bed, low sub-drone (A1/A2, 55Hz/110Hz), delicate sparse piano notes.
- 00:30 - 01:10 (Scene 2): Warm pulse enters (8th-note gentle filtered pulse), harmonic transition to C-major / F-major.
- 01:10 - 02:10 (Scene 3): Subtle rhythmic clockwork tick (subtle 16th-note tactile pulses), warm pad progression.
- 02:10 - 03:30 (Scene 4): Methodical, focused arpeggio layer, resonant filter opening slowly, steady scientific cadence.
- 03:30 - 04:30 (Scene 5): Emotional peak: broader harmonic movement, layered rich pads, crystalline bell overtone.
- 04:30 - 05:00 (Scene 6): Resolving cadence settling into pure stillness; piano chord decays at 04:50, leaving deliberate silence.

SFX:
- Tactile UI micro-clicks (bandpass filtered impulse)
- Deterministic verification chime (harmonically pure C6/E6 dual tone with exponential decay)
- Sonic signature resolve (warm multi-octave harmonic chime)
"""

import os
import numpy as np
import scipy.io.wavfile as wavfile
import subprocess

SAMPLE_RATE = 48000
TOTAL_DURATION = 300.0  # seconds
TOTAL_SAMPLES = int(SAMPLE_RATE * TOTAL_DURATION)

def create_sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)

def create_envelope(n_samples, attack_s, release_s, sr=SAMPLE_RATE):
    att_samples = int(attack_s * sr)
    rel_samples = int(release_s * sr)
    env = np.ones(n_samples, dtype=np.float32)
    if att_samples > 0:
        env[:att_samples] = np.linspace(0, 1, att_samples)
    if rel_samples > 0:
        env[-rel_samples:] = np.linspace(1, 0, rel_samples)
    return env

def generate_ambient_score():
    print("[*] Generating 300.0-second custom ambient-electronic score...")
    t = np.linspace(0, TOTAL_DURATION, TOTAL_SAMPLES, endpoint=False, dtype=np.float32)
    left = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    right = np.zeros(TOTAL_SAMPLES, dtype=np.float32)
    
    # 1. Foundation Drone: Sub-bass & Warm Pad (55Hz [A1], 110Hz [A2], 164.8Hz [E3], 220Hz [A3])
    # Gentle LFO modulation
    lfo_drone = 0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t)
    sub = np.sin(2 * np.pi * 55.0 * t) * 0.12 * lfo_drone
    pad_a = np.sin(2 * np.pi * 110.0 * t) * 0.08
    pad_e = np.sin(2 * np.pi * 164.81 * t) * 0.06
    pad_c = np.sin(2 * np.pi * 261.63 * t) * 0.04 # C4
    
    drone = sub + pad_a + pad_e + pad_c
    
    # Envelope over 300 seconds: Fades in 0-4s, gently swells in Scene 2-5, decays 280-292s, pure silence 292-300s
    global_env = np.ones(TOTAL_SAMPLES, dtype=np.float32)
    global_env[:SAMPLE_RATE * 4] = np.linspace(0, 1, SAMPLE_RATE * 4)
    # Decay starting at 282s to 292s
    decay_start = int(282 * SAMPLE_RATE)
    decay_end = int(292 * SAMPLE_RATE)
    global_env[decay_start:decay_end] = np.linspace(1, 0, decay_end - decay_start)
    global_env[decay_end:] = 0.0
    
    drone *= global_env
    left += drone
    right += drone
    
    # 2. Scene 2 (30s - 70s): Warm pulse entrance (8th notes @ 120 bpm = 4 pulses per second)
    pulse_mask = (t >= 30.0) & (t < 70.0)
    pulse_t = t[pulse_mask] - 30.0
    pulse_env = (0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * pulse_t)) ** 4
    pulse_tone = np.sin(2 * np.pi * 220.0 * pulse_t) * 0.05 * pulse_env
    left[pulse_mask] += pulse_tone * 0.8
    right[pulse_mask] += pulse_tone * 0.9
    
    # 3. Scene 3 (70s - 130s): Rhythmic minimal tactile sequence (16th notes = 8 per second)
    s3_mask = (t >= 70.0) & (t < 130.0)
    s3_t = t[s3_mask] - 70.0
    s3_click = np.sin(2 * np.pi * 880.0 * s3_t) * np.exp(-30.0 * (s3_t % 0.125)) * 0.02
    left[s3_mask] += s3_click * 0.9
    right[s3_mask] += s3_click * 0.7
    
    # 4. Scene 4 (130s - 210s): Focused arpeggiated chords (A-min -> F-maj -> C-maj -> G-maj)
    # 4-measure cycle every 8 seconds
    s4_mask = (t >= 130.0) & (t < 210.0)
    s4_t = t[s4_mask] - 130.0
    notes = [220.0, 261.63, 329.63, 392.0, 440.0, 523.25]
    arp = np.zeros(len(s4_t), dtype=np.float32)
    step = 0.25 # 4 notes per second
    for i, n_freq in enumerate(notes):
        step_mask = ((s4_t // step) % len(notes)) == i
        phase = (s4_t % step) / step
        decay = np.exp(-4.0 * phase)
        arp += np.sin(2 * np.pi * n_freq * s4_t) * 0.03 * decay * step_mask
    left[s4_mask] += arp * 0.85
    right[s4_mask] += arp * 1.05
    
    # 5. Scene 5 (210s - 270s): Broad harmonic swelling peak (Crystalline harmonics + deep strings)
    s5_mask = (t >= 210.0) & (t < 270.0)
    s5_t = t[s5_mask] - 210.0
    s5_env = np.sin(np.pi * (s5_t / 60.0)) # smooth parabolic swell
    bell_chime = (
        np.sin(2 * np.pi * 523.25 * s5_t) * 0.04 + # C5
        np.sin(2 * np.pi * 659.25 * s5_t) * 0.03 + # E5
        np.sin(2 * np.pi * 783.99 * s5_t) * 0.03 + # G5
        np.sin(2 * np.pi * 1046.50 * s5_t) * 0.02  # C6
    ) * s5_env
    left[s5_mask] += bell_chime * 0.9
    right[s5_mask] += bell_chime * 0.9
    
    # 6. Scene 6 (270s - 300s): Gentle resolving piano chord at 271s and 283s
    def add_piano_chord(start_sec, chord_freqs, duration_sec):
        idx = int(start_sec * SAMPLE_RATE)
        chord_len = int(duration_sec * SAMPLE_RATE)
        if idx + chord_len > TOTAL_SAMPLES:
            chord_len = TOTAL_SAMPLES - idx
        t_c = np.linspace(0, duration_sec, chord_len, endpoint=False)
        decay = np.exp(-0.7 * t_c)
        c_sig = np.zeros(chord_len, dtype=np.float32)
        for f in chord_freqs:
            c_sig += (np.sin(2 * np.pi * f * t_c) + 0.3 * np.sin(2 * np.pi * 2 * f * t_c)) * 0.04
        c_sig *= decay
        left[idx:idx+chord_len] += c_sig
        right[idx:idx+chord_len] += c_sig

    # Opening sparse notes (Scene 1)
    add_piano_chord(4.0, [261.63, 329.63, 392.0], 8.0) # C-maj
    add_piano_chord(16.0, [220.0, 261.63, 329.63], 9.0) # A-min
    
    # Final resolution (Scene 6)
    add_piano_chord(272.0, [220.0, 261.63, 329.63, 440.0], 12.0)
    add_piano_chord(284.0, [130.81, 261.63, 329.63, 392.0], 7.0)
    
    # Normalize to -16 dB peak
    peak = max(np.max(np.abs(left)), np.max(np.abs(right)), 1e-6)
    target_peak = 0.35 # comfortable headroom under voiceover
    left = (left / peak) * target_peak
    right = (right / peak) * target_peak
    
    # Stereo interleaved 16-bit PCM
    stereo = np.column_stack([left, right])
    int16_stereo = np.clip(stereo * 32767.0, -32768, 32767).astype(np.int16)
    return int16_stereo

def generate_sfx(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    # 1. UI Soft Click (0.06s)
    dur = 0.06
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    noise = np.random.uniform(-1, 1, n).astype(np.float32)
    filt = np.sin(2 * np.pi * 2400.0 * t) * np.exp(-120.0 * t)
    click = (noise * 0.2 + filt * 0.8) * np.exp(-90.0 * t)
    click = np.clip(click * 0.4 * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(os.path.join(out_dir, "ui_soft_click.wav"), SAMPLE_RATE, click)
    
    # 2. UI Verification Chime (1.2s)
    dur = 1.2
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    tone = (
        np.sin(2 * np.pi * 1046.50 * t) * 0.6 + # C6
        np.sin(2 * np.pi * 1318.51 * t) * 0.4   # E6
    ) * np.exp(-3.5 * t)
    chime = np.clip(tone * 0.35 * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(os.path.join(out_dir, "ui_subtle_chime.wav"), SAMPLE_RATE, chime)
    
    # 3. Sonic Signature (3.5s)
    dur = 3.5
    n = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    sig = (
        np.sin(2 * np.pi * 261.63 * t) * 0.5 + # C4
        np.sin(2 * np.pi * 392.00 * t) * 0.3 + # G4
        np.sin(2 * np.pi * 523.25 * t) * 0.2 + # C5
        np.sin(2 * np.pi * 1046.50 * t) * 0.1  # C6
    ) * np.exp(-1.2 * t)
    sig = np.clip(sig * 0.38 * 32767.0, -32768, 32767).astype(np.int16)
    wavfile.write(os.path.join(out_dir, "sonic_signature.wav"), SAMPLE_RATE, sig)
    print(f"[OK] Sound effects generated in {out_dir}")

def mix_full_soundtrack():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    music_dir = os.path.join(root, "assets", "music")
    sfx_dir = os.path.join(root, "assets", "sound_effects")
    vo_dir = os.path.join(root, "assets", "voiceover")
    os.makedirs(music_dir, exist_ok=True)
    
    # Generate score
    score_data = generate_ambient_score()
    score_wav = os.path.join(music_dir, "score_ambient_pulse.wav")
    wavfile.write(score_wav, SAMPLE_RATE, score_data)
    print(f"[OK] Ambient score saved to {score_wav}")
    
    # Generate SFX
    generate_sfx(sfx_dir)
    
    # Final Audio Mix via ffmpeg: Combine voiceover + score with ducking + sfx at exact storyboard cues
    master_vo = os.path.join(vo_dir, "vo_full_master.wav").replace("\\", "/")
    score_p = score_wav.replace("\\", "/")
    click_p = os.path.join(sfx_dir, "ui_soft_click.wav").replace("\\", "/")
    chime_p = os.path.join(sfx_dir, "ui_subtle_chime.wav").replace("\\", "/")
    sig_p = os.path.join(sfx_dir, "sonic_signature.wav").replace("\\", "/")
    
    final_mix_wav = os.path.join(sfx_dir, "final_soundtrack_master.wav")
    
    # SFX cue timings:
    # 00:25: Electric blue point activation click
    # 00:52: Transition zoom click
    # 01:25: Dot matrix focus click
    # 02:45: Deterministic SymPy verification chime
    # 04:30: Brand resolve sonic signature
    filter_complex = (
        "[0:a]volume=1.0[vo];"
        "[1:a]volume=0.38[bgm];"
        "[2:a]adelay=25000|25000[sfx_pt];"
        "[2:a]adelay=52000|52000[sfx_zoom];"
        "[2:a]adelay=85000|85000[sfx_mat];"
        "[3:a]adelay=165000|165000[sfx_chime];"
        "[4:a]adelay=270000|270000[sfx_sig];"
        "[vo][bgm][sfx_pt][sfx_zoom][sfx_mat][sfx_chime][sfx_sig]amix=inputs=7:dropout_transition=0:normalize=0,apad=whole_dur=300,atrim=0:300[final_a]"
    )
    
    print("[*] Mixing master 300.0s soundtrack with voiceover and sound design...")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", master_vo,
        "-i", score_p,
        "-i", click_p,
        "-i", chime_p,
        "-i", sig_p,
        "-filter_complex", filter_complex,
        "-map", "[final_a]",
        "-ar", "48000", "-ac", "2",
        final_mix_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[OK] Master audio soundtrack complete: {final_mix_wav}")

if __name__ == "__main__":
    mix_full_soundtrack()
