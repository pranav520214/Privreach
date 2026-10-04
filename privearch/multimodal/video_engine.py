"""Video Understanding Engine: FFmpeg metadata extraction, audio separation, and keyframing."""

import os
import re
import json
import subprocess
import shutil
from typing import Dict, Any, List, Optional, Tuple

from privearch.schemas import EvidenceChunk, EvidenceType


class VideoProcessor:
    """
    Multimodal Video Processor using native FFmpeg and FFprobe.
    Extracts timecoded keyframes, audio tracks, and technical media metadata.
    """

    def __init__(self, cache_dir: str = ".privearch_media_cache"):
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

    @staticmethod
    def is_available() -> bool:
        """Check if FFmpeg and FFprobe binaries are accessible in system PATH."""
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    @staticmethod
    def format_timecode(seconds: float) -> str:
        """Convert seconds into standard HH:MM:SS format."""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def probe(self, video_path: str) -> Dict[str, Any]:
        """Extract media streams and metadata using ffprobe."""
        if not self.is_available():
            return {"error": "FFprobe is not installed or not in PATH"}

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            
            format_info = data.get("format", {})
            duration = float(format_info.get("duration", 0.0))
            size_mb = round(float(format_info.get("size", 0.0)) / (1024 * 1024), 2)

            video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
            audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})

            width = video_stream.get("width", 0)
            height = video_stream.get("height", 0)
            fps_eval = video_stream.get("r_frame_rate", "30/1")
            try:
                num, den = fps_eval.split("/")
                fps = round(float(num) / float(den), 2)
            except Exception:
                fps = 30.0

            return {
                "file_name": os.path.basename(video_path),
                "file_path": os.path.abspath(video_path),
                "duration_seconds": duration,
                "duration_formatted": self.format_timecode(duration),
                "size_mb": size_mb,
                "resolution": f"{width}x{height}",
                "width": width,
                "height": height,
                "fps": fps,
                "video_codec": video_stream.get("codec_name", "unknown"),
                "has_audio": bool(audio_stream),
                "audio_codec": audio_stream.get("codec_name", "none")
            }
        except Exception as e:
            return {"error": f"Failed to probe video: {e}"}

    def extract_audio(self, video_path: str, output_wav_path: Optional[str] = None) -> Optional[str]:
        """
        Extracts audio track from video as 16kHz mono WAV for speech recognition.
        """
        if not self.is_available():
            return None

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        out_path = output_wav_path or os.path.join(self.cache_dir, f"{video_name}_audio.wav")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            out_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            if os.path.exists(out_path):
                return out_path
        except Exception as e:
            print(f"[Warning] Audio extraction failed: {e}")
        return None

    def extract_keyframes(
        self,
        video_path: str,
        interval_seconds: float = 10.0,
        max_frames: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Extracts keyframes at uniform intervals.
        Returns list of metadata dicts with timecodes and saved image paths.
        """
        if not self.is_available():
            return []

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        frames_dir = os.path.join(self.cache_dir, f"{video_name}_frames")
        os.makedirs(frames_dir, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-vf", f"fps=1/{interval_seconds}",
            "-q:v", "3",
            os.path.join(frames_dir, "frame_%04d.jpg")
        ]

        frames: List[Dict[str, Any]] = []
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            files = sorted([f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".jpg")])

            for idx, fname in enumerate(files[:max_frames], start=1):
                timestamp = (idx - 1) * interval_seconds
                frames.append({
                    "frame_index": idx,
                    "timestamp_seconds": timestamp,
                    "timecode": self.format_timecode(timestamp),
                    "image_path": os.path.join(frames_dir, fname),
                    "file_name": fname
                })
        except Exception as e:
            print(f"[Warning] Keyframe extraction failed: {e}")

        return frames

    def build_video_evidence_chunks(
        self,
        video_path: str,
        interval_seconds: float = 15.0
    ) -> List[EvidenceChunk]:
        """
        Builds indexed evidence chunks spanning the video timeline.
        """
        meta = self.probe(video_path)
        if "error" in meta:
            return []

        frames = self.extract_keyframes(video_path, interval_seconds=interval_seconds)
        chunks: List[EvidenceChunk] = []
        doc_name = os.path.basename(video_path)

        for f in frames:
            t_start = f["timestamp_seconds"]
            t_end = min(t_start + interval_seconds, meta["duration_seconds"])
            tc_range = f"{self.format_timecode(t_start)} - {self.format_timecode(t_end)}"
            
            chunk_text = (
                f"[Video Scene: {doc_name} at {tc_range}] "
                f"Visual frame index #{f['frame_index']} recorded at resolution {meta['resolution']}. "
                f"Timeline segment in scientific media presentation."
            )

            chunks.append(EvidenceChunk(
                chunk_id=f"vid_{doc_name}_{f['frame_index']}",
                source_name=doc_name,
                evidence_type=EvidenceType.VIDEO_TIMECODE,
                timestamp_start=t_start,
                timestamp_end=t_end,
                text=chunk_text,
                metadata={
                    "timecode_range": tc_range,
                    "image_path": f["image_path"],
                    "video_path": video_path,
                    "resolution": meta["resolution"]
                }
            ))

        return chunks
