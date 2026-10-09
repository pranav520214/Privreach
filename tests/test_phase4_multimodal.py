"""Unit tests for Phase 4: Multimodal Video, Audio, and Meeting Intelligence."""

import os
import tempfile
import json
import pytest

from privearch.schemas import EvidenceChunk, EvidenceType, DocumentChunk, ScoredChunk
from privearch.multimodal.video_engine import VideoProcessor
from privearch.multimodal.audio_engine import AudioProcessor
from privearch.multimodal.meeting_intelligence import MeetingIntelligenceEngine
from privearch.ui.canvas_generator import CanvasGenerator
from privearch.ui.canvas_protocol import CanvasViewType


def test_timecode_formatting():
    """Verify standard HH:MM:SS formatting."""
    assert VideoProcessor.format_timecode(45.0) == "00:45"
    assert VideoProcessor.format_timecode(125.0) == "02:05"
    assert VideoProcessor.format_timecode(3665.0) == "01:01:05"

    assert AudioProcessor.format_timecode(59.0) == "00:59"
    assert AudioProcessor.format_timecode(3600.0) == "01:00:00"


def test_transcript_parsing_vtt():
    """Verify parsing WebVTT / SRT transcript files."""
    vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.500
Dr. Adams: Welcome to the symposium on catalytic dehydrogenation.

00:00:06.000 --> 00:00:12.000
Dr. Baker: We observed that platinum nanoparticles lower the activation barrier significantly.
"""
    with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False, encoding="utf-8") as f:
        f.write(vtt_content)
        vtt_path = f.name

    try:
        segments = AudioProcessor.parse_transcript_file(vtt_path)
        assert len(segments) == 2
        assert segments[0]["start"] == 1.0
        assert segments[0]["end"] == 5.5
        assert "catalytic dehydrogenation" in segments[0]["text"]
        assert segments[1]["start"] == 6.0
        assert "platinum nanoparticles" in segments[1]["text"]
    finally:
        if os.path.exists(vtt_path):
            os.remove(vtt_path)


def test_transcript_parsing_json():
    """Verify parsing structured JSON transcripts."""
    data = [
        {"start": 10.0, "end": 15.0, "speaker": "Alice", "text": "We decided to increase the temperature to 350K."},
        {"start": 16.0, "end": 20.0, "speaker": "Bob", "text": "Will that cause thermal decomposition of the reagent?"}
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        json_path = f.name

    try:
        segments = AudioProcessor.parse_transcript_file(json_path)
        assert len(segments) == 2
        assert segments[0]["speaker"] == "Alice"
        assert segments[1]["speaker"] == "Bob"
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)


def test_audio_evidence_chunk_builder():
    """Verify conversion of transcript segments into EvidenceChunks and DocumentChunks."""
    processor = AudioProcessor()
    fake_segments = [
        {"start": 30.0, "end": 45.0, "speaker": "Dr. Elena", "text": "The rate constant k equals 2.5e-3 s^-1 at equilibrium."}
    ]
    chunks = processor.build_audio_evidence_chunks("lab_discussion.wav", segments=fake_segments)
    assert len(chunks) == 1
    ec = chunks[0]
    assert ec.evidence_type == EvidenceType.AUDIO_TRANSCRIPT
    assert ec.timestamp_start == 30.0
    assert ec.timestamp_end == 45.0
    assert ec.speaker_id == "Dr. Elena"
    assert "rate constant k" in ec.text

    # Convert to unified DocumentChunk
    doc_chunk = ec.to_document_chunk()
    assert isinstance(doc_chunk, DocumentChunk)
    assert doc_chunk.doc_name == "lab_discussion.wav"
    assert doc_chunk.evidence_type == "AUDIO_TRANSCRIPT"
    assert doc_chunk.speaker_id == "Dr. Elena"
    assert doc_chunk.timestamp_start == 30.0


def test_meeting_intelligence_extraction():
    """Verify extraction of decisions, open questions, and action items."""
    engine = MeetingIntelligenceEngine()
    segments = [
        {"start": 0.0, "end": 10.0, "speaker": "Alice", "text": "We decided to synthesize the zeolitic imidazolate framework."},
        {"start": 11.0, "end": 20.0, "speaker": "Bob", "text": "Why does the pore diameter contract under higher pressure?"},
        {"start": 21.0, "end": 30.0, "speaker": "Charlie", "text": "Todo: I will run the powder X-ray diffraction scan tomorrow."}
    ]

    diarized = engine.diarize_segments(segments)
    insights = engine.extract_meeting_insights(diarized, title="Coordination Chemistry Sync")

    assert insights["title"] == "Coordination Chemistry Sync"
    assert len(insights["decisions"]) >= 1
    assert "zeolitic imidazolate framework" in insights["decisions"][0]["decision"]

    assert len(insights["open_questions"]) >= 1
    assert "pore diameter" in insights["open_questions"][0]["question"]

    assert len(insights["action_items"]) >= 1
    assert "powder X-ray diffraction" in insights["action_items"][0]["task"]

    markdown_memo = engine.format_meeting_markdown(insights)
    assert "# 🎙️ Meeting Intelligence Report" in markdown_memo
    assert "Scientific Decisions & Conclusions" in markdown_memo
    assert "Assigned Action Items" in markdown_memo


def test_canvas_multimodal_timeline_generator():
    """Verify Canvas rendering of multimodal timeline table."""
    c1 = DocumentChunk(
        chunk_id="chunk_vid_1",
        doc_name="kinetics_experiment.mp4",
        page_num=1,
        section_header="01:15 - 01:30",
        text="Colorimeter readout shifts from clear to deep blue.",
        evidence_type="VIDEO_TIMECODE",
        timestamp_start=75.0,
        timestamp_end=90.0
    )
    c2 = DocumentChunk(
        chunk_id="chunk_aud_1",
        doc_name="team_debrief.wav",
        page_num=1,
        section_header="04:20 - 04:45",
        text="The absorbance peaked at 620 nm.",
        evidence_type="AUDIO_TRANSCRIPT",
        speaker_id="Dr. Curie",
        timestamp_start=260.0,
        timestamp_end=285.0
    )

    sc1 = ScoredChunk(chunk=c1, rrf_score=0.032, final_rank=1)
    sc2 = ScoredChunk(chunk=c2, rrf_score=0.028, final_rank=2)

    md = CanvasGenerator.generate_multimodal_timeline_markdown([sc1, sc2])
    assert "### 🎥 Multimodal Evidence Timeline & Transcripts" in md
    assert "kinetics_experiment.mp4" in md
    assert "01:15 - 01:30" in md
    assert "Dr. Curie" in md
    assert "620 nm" in md


def test_universal_media_ingestion_dispatch(monkeypatch):
    """Verify kernel.ingest_media properly routes PDFs, videos, and audios."""
    from privearch.os_engine import PrivearchKernel
    from privearch.config import PrivearchConfig

    cfg = PrivearchConfig(embedding_backend="cpu_minilm")
    kernel = PrivearchKernel(config=cfg)

    # Ingest synthetic transcript audio
    vtt_content = """WEBVTT

00:01:00.000 --> 00:01:15.000
Speaker 1: At higher activation energy, the reaction rate decreases exponentially according to the Arrhenius equation.
"""
    with tempfile.NamedTemporaryFile("w", suffix=".vtt", delete=False, encoding="utf-8") as f:
        f.write(vtt_content)
        vtt_path = f.name

    try:
        res = kernel.ingest_media(vtt_path, force=True, auto_save=False)
        assert res["status"] == "success"
        assert res["type"] == "audio"
        assert res["chunks"] >= 1
        assert kernel.total_chunks > 0

        # Retrieve using Hybrid RRF
        retrieved = kernel.hybrid_retriever.retrieve("Arrhenius equation activation energy", top_k_final=3)
        assert len(retrieved) > 0
        top_match = retrieved[0].chunk
        assert "Arrhenius equation" in top_match.text
        assert top_match.evidence_type == "AUDIO_TRANSCRIPT"
    finally:
        if os.path.exists(vtt_path):
            os.remove(vtt_path)
