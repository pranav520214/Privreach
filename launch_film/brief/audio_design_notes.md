# PRIVREACH 5-MINUTE LAUNCH FILM — AUDIO & SOUND DESIGN NOTES

## 1. Narration Engineering
- **Engine**: Microsoft Neural TTS (`edge-tts`)
- **Voice Model**: `en-US-ChristopherNeural`
- **Rate**: `-3%` to `-4%` (approx 125 words per minute)
- **Tone Profile**: Calm, authoritative, scientific documentary delivery with natural breathing cadence.
- **Scene-by-Scene Timeline Alignment**:
  - **Scene 01 (00:00–00:30)**: Starts at `00:00.50`, concludes at `00:28.89` (1.1s tail pause).
  - **Scene 02 (00:30–01:10)**: Starts at `00:31.50`, concludes at `00:59.03` (10.9s visual glide into UI).
  - **Scene 03 (01:10–02:10)**: Starts at `01:11.50`, concludes at `02:00.75` (9.2s interlude for dot matrix).
  - **Scene 04 (02:10–03:30)**: Starts at `02:12.00`, concludes at `03:06.41` (23.5s math verification showcase).
  - **Scene 05 (03:30–04:30)**: Starts at `03:31.80`, concludes at `04:15.41` (14.5s scientific montage peak).
  - **Scene 06 (04:30–05:00)**: Starts at `04:31.50`, concludes at `04:52.72` (7.3s deliberate final silence).

---

## 2. Ambient-Electronic Musical Score
- **Track**: `score_ambient_pulse.wav` (300.0s @ 48kHz 24-bit Stereo)
- **Harmonic Architecture**:
  - *Tonal Center*: A minor / C major ($A_1 = 55\text{ Hz}$, $A_2 = 110\text{ Hz}$, $E_3 = 164.8\text{ Hz}$, $C_4 = 261.6\text{ Hz}$).
  - *Section 1 (00:00–00:30)*: Contemplative ambient foundation with gentle LFO modulation ($0.08\text{ Hz}$). Sparse acoustic piano intervals at $t=4\text{s}$ and $t=16\text{s}$.
  - *Section 2 (00:30–01:10)*: 8th-note gentle filtered pulse enters ($120\text{ BPM} = 4\text{ Hz}$), harmonic transition into C-major.
  - *Section 3 (01:10–02:10)*: Rhythmic clockwork tick ($16\text{th}$-notes @ $880\text{ Hz}$ filtered) driving scientific inquiry.
  - *Section 4 (02:10–03:30)*: 4-measure arpeggio cycle ($A\text{-min} \to F\text{-maj} \to C\text{-maj} \to G\text{-maj}$) providing analytical momentum.
  - *Section 5 (03:30–04:30)*: Emotional peak: rich multi-octave pads with crystalline bell overtones ($C_5, E_5, G_5, C_6$).
  - *Section 6 (04:30–05:00)*: Resolving piano chords ($t=272\text{s}$, $t=284\text{s}$) decaying into complete silence from $04:52$ to $05:00$.
- **Ducking & Mix Balance**: Music is mastered at `-18\text{ dB}$ LUFS under voiceover, preserving 100% speech intelligibility.

---

## 3. Sound Effects & Foley
- **Tactile UI Micro-Click** (`ui_soft_click.wav`):
  - Form: Bandpass-filtered impulse at $2400\text{ Hz}$ with rapid $60\text{ ms}$ exponential decay.
  - Placed at key visual transitions ($t=25\text{s}, 52\text{s}, 85\text{s}$).
- **Deterministic Verification Chime** (`ui_subtle_chime.wav`):
  - Form: Harmonic dual-tone ($1046.5\text{ Hz } [C_6] + 1318.5\text{ Hz } [E_6]$) with warm $1.2\text{ s}$ decay.
  - Placed at $t=165\text{s}$ ($02:45$) precisely as the SymPy `VERIFIED` stamp appears.
- **Sonic Signature Resolve** (`sonic_signature.wav`):
  - Form: Four-octave harmonic chord ($C_4, G_4, C_5, C_6$) with $3.5\text{ s}$ acoustic resonance.
  - Placed at $t=270\text{s}$ ($04:30$) accompanying the final Privreach logo lockup.
