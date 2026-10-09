"""Audio Understanding & Local Speech Recognition Engine."""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple

from privearch.schemas import EvidenceChunk, EvidenceType


class AudioProcessor:
    """
    Local-first Speech Recognition and Audio Ingestion Engine.
    Supports Faster-Whisper (quantized int8 on CPU) and structured transcript parsing.
    """

    def __init__(self, model_size: str = "tiny", compute_type: str = "int8"):
        self.model_size = model_size
        self.compute_type = compute_type
        self._whisper_model = None

    @staticmethod
    def is_whisper_available() -> bool:
        """Check if faster-whisper is installed."""
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def get_whisper_model(self):
        """Lazy-load the quantized CPU whisper model."""
        if self._whisper_model is None and self.is_whisper_available():
            try:
                from faster_whisper import WhisperModel
                self._whisper_model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type=self.compute_type
                )
            except Exception as e:
                print(f"[Warning] Failed to initialize Faster-Whisper model: {e}")
        return self._whisper_model

    def transcribe(
        self,
        audio_path: str,
        beam_size: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Transcribes an audio file into timestamped segments.
        Returns: list of dicts with {start, end, text, words}.
        """
        model = self.get_whisper_model()
        if model is not None:
            try:
                segments, info = model.transcribe(
                    audio_path,
                    beam_size=beam_size,
                    word_timestamps=True
                )
                results: List[Dict[str, Any]] = []
                for s in segments:
                    clean_text = s.text.strip()
                    if clean_text:
                        results.append({
                            "start": round(s.start, 2),
                            "end": round(s.end, 2),
                            "text": clean_text,
                            "speaker": "Speaker 1"
                        })
                return results
            except Exception as e:
                print(f"[Warning] Whisper transcription failed: {e}")

        # Fallback: Check if matching .vtt, .srt, or .txt exists
        base_name = os.path.splitext(audio_path)[0]
        for ext in [".vtt", ".srt", ".txt", ".json"]:
            cand = base_name + ext
            if os.path.exists(cand):
                return self.parse_transcript_file(cand)

        return []

    @staticmethod
    def parse_transcript_file(file_path: str) -> List[Dict[str, Any]]:
        """Parses external transcript files (.vtt, .srt, .json, .txt)."""
        results: List[Dict[str, Any]] = []
        if not os.path.exists(file_path):
            return results

        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".json":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
                elif "segments" in data:
                    return data["segments"]
            except Exception:
                pass

        # Parse text or srt/vtt
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().replace("\r\n", "\n")

            # Pattern for timecodes: 00:01:23 --> 00:01:45
            timecode_pattern = re.compile(r'(\d{2}:\d{2}:\d{2}[.,]?\d*)\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]?\d*)')
            blocks = content.split("\n\n")

            for b in blocks:
                lines = [l.strip() for l in b.splitlines() if l.strip()]
                if not lines:
                    continue

                # Ignore WebVTT headers or comments
                if lines[0].upper().startswith("WEBVTT") or lines[0].upper().startswith("NOTE"):
                    # Check if there are remaining lines after header
                    lines = [l for l in lines if not l.upper().startswith("WEBVTT") and not l.upper().startswith("NOTE")]
                    if not lines:
                        continue

                match = None
                text_lines = []
                for l in lines:
                    m = timecode_pattern.search(l)
                    if m:
                        match = m
                    elif not l.isdigit():
                        text_lines.append(l)

                if match and text_lines:
                    start_sec = AudioProcessor._parse_time_str(match.group(1))
                    end_sec = AudioProcessor._parse_time_str(match.group(2))
                    results.append({
                        "start": start_sec,
                        "end": end_sec,
                        "text": " ".join(text_lines),
                        "speaker": "Speaker 1"
                    })
                elif text_lines and not lines[0].isdigit():
                    # Only append fallback if it looks like conversational speech, not headers
                    candidate_text = " ".join(text_lines)
                    if not any(candidate_text.upper().startswith(h) for h in ("STYLE", "REGION")):
                        results.append({
                            "start": len(results) * 10.0,
                            "end": (len(results) + 1) * 10.0,
                            "text": candidate_text,
                            "speaker": "Speaker 1"
                        })
        except Exception as e:
            print(f"[Warning] Failed to parse transcript {file_path}: {e}")

        return results

    @staticmethod
    def _parse_time_str(time_str: str) -> float:
        """Parse HH:MM:SS.mmm into total seconds."""
        parts = time_str.replace(",", ".").split(":")
        if len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        return 0.0

    @staticmethod
    def format_timecode(seconds: float) -> str:
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def build_audio_evidence_chunks(
        self,
        audio_path: str,
        segments: Optional[List[Dict[str, Any]]] = None
    ) -> List[EvidenceChunk]:
        """
        Converts transcript segments into searchable EvidenceChunk records.
        """
        if segments is None:
            segments = self.transcribe(audio_path)

        doc_name = os.path.basename(audio_path)
        chunks: List[EvidenceChunk] = []

        for idx, seg in enumerate(segments, start=1):
            t_start = seg.get("start", 0.0)
            t_end = seg.get("end", 0.0)
            speaker = seg.get("speaker", "Speaker")
            text = seg.get("text", "").strip()
            tc_range = f"{self.format_timecode(t_start)} - {self.format_timecode(t_end)}"

            chunk_text = f"[{doc_name} ({tc_range}) - {speaker}]: {text}"

            chunks.append(EvidenceChunk(
                chunk_id=f"aud_{doc_name}_{idx}",
                source_name=doc_name,
                evidence_type=EvidenceType.AUDIO_TRANSCRIPT,
                timestamp_start=t_start,
                timestamp_end=t_end,
                speaker_id=speaker,
                text=chunk_text,
                metadata={
                    "timecode_range": tc_range,
                    "speaker": speaker,
                    "audio_path": audio_path,
                    "raw_text": text
                }
            ))

        return chunks
