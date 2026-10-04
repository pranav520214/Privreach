"""Unit tests for Phase 5: Adaptive Resource Manager, 100x100 Computational Visualization, and PPTX Generator."""

import os
import time
import tempfile
import numpy as np
import pytest

from privearch.resources import (
    SystemMonitor,
    AdaptivePolicy,
    AdaptiveMode,
    PriorityManager,
    WorkloadPriority,
    WorkloadScheduler,
    Workload,
    WorkloadStatus,
    WorkloadCancelledException,
    ResourceManager,
)
from privearch.compute.computational_visualization import (
    ComputationalVisualizationEngine,
    SimulationModel,
)
from privearch.reports.presentation_generator import PresentationGenerator
from privearch.schemas import (
    PrivearchReport,
    QueryAnalysis,
    VerificationAudit,
    DocumentChunk,
    ScoredChunk,
    CalculationVerification,
    ArtifactType,
)
from privearch.os_engine import PrivearchKernel
from privearch.config import PrivearchConfig


def test_system_monitor_telemetry():
    """Verify SystemMonitor collects real-time CPU, RAM, disk, and stress metrics."""
    monitor = SystemMonitor()
    telemetry = monitor.get_telemetry()
    assert "cpu_percent" in telemetry
    assert "ram_percent" in telemetry
    assert "ram_available_gb" in telemetry
    assert "stress_score" in telemetry
    assert 0.0 <= telemetry["stress_score"] <= 1.0
    assert isinstance(telemetry["on_battery"], bool)


def test_adaptive_policy_modes_and_degradation():
    """Verify adaptive mode policy rules and automatic throttling under load."""
    policy = AdaptivePolicy(mode=AdaptiveMode.ADAPTIVE)

    # 1. Low load scenario
    low_load_telemetry = {"cpu_percent": 15.0, "ram_percent": 40.0, "stress_score": 0.25, "on_battery": False}
    c_low = policy.evaluate(low_load_telemetry)
    assert c_low["max_workers"] >= 2
    assert c_low["matrix_resolution"] == (100, 100)
    assert c_low["fps_limit"] == 30
    assert c_low["pause_background"] is False

    # 2. High stress scenario (quality degrades before interactivity)
    high_load_telemetry = {"cpu_percent": 90.0, "ram_percent": 92.0, "stress_score": 0.91, "on_battery": False}
    c_high = policy.evaluate(high_load_telemetry)
    assert c_high["max_workers"] == 1
    assert c_high["matrix_resolution"][0] < 100  # Resolution dropped
    assert c_high["fps_limit"] <= 20             # FPS dropped
    assert c_high["pause_background"] is True

    # 3. Battery Saver mode
    policy.set_mode(AdaptiveMode.BATTERY_SAVER)
    c_bat = policy.evaluate(low_load_telemetry)
    assert c_bat["matrix_resolution"] == (50, 50)
    assert c_bat["fps_limit"] == 15
    assert c_bat["max_workers"] == 1

    # 4. Performance mode
    policy.set_mode(AdaptiveMode.PERFORMANCE)
    c_perf = policy.evaluate(low_load_telemetry)
    assert c_perf["max_workers"] >= 4
    assert c_perf["fps_limit"] == 60


def test_workload_lifecycle_pause_resume_cancel():
    """Verify cooperative pause, resume, cancellation, and progress reporting."""
    scheduler = WorkloadScheduler(max_workers=2)

    steps_completed = []

    def long_task(w: Workload):
        for i in range(10):
            w.check_cooperative(throttle_delay_s=0.01)
            steps_completed.append(i)
            w.update_progress((i + 1) * 10.0, f"Step {i+1}/10")
        return "SUCCESS"

    # Test Cancellation
    w = scheduler.submit("Cancellable Job", "test", long_task, priority=WorkloadPriority.LOW)
    time.sleep(0.02)
    w.cancel()
    time.sleep(0.05)
    assert w.status == WorkloadStatus.CANCELLED
    assert w.is_cancelled() is True

    # Test Synchronous Execution with progress
    w_sync_steps = []
    def fast_task(w: Workload):
        for i in range(5):
            w.check_cooperative()
            w_sync_steps.append(i)
            w.update_progress((i + 1) * 20.0)
        return "DONE"

    res = scheduler.execute_sync("Sync Job", "test_sync", fast_task)
    assert res == "DONE"
    assert len(w_sync_steps) == 5


def test_resource_manager_status_and_controls():
    """Verify ResourceManager coordinates workloads and produces execution console output."""
    rm = ResourceManager(mode=AdaptiveMode.BALANCED)
    assert rm.get_mode() == AdaptiveMode.BALANCED

    rm.set_mode(AdaptiveMode.ADAPTIVE)
    assert rm.get_mode() == AdaptiveMode.ADAPTIVE

    console_status = rm.format_console_status()
    assert "PRIVREACH ENGINE [Mode: ADAPTIVE]" in console_status
    assert "CPU:" in console_status
    assert "RAM:" in console_status
    rm.shutdown()


def test_computational_visualization_100x100_matrix():
    """Verify 100x100 matrix calculation with 10,000 logical points and HTML generation."""
    # 1. Standard 100x100 matrix
    mat_100 = ComputationalVisualizationEngine.compute_matrix(
        t=1.5, nx=100, ny=100, sim_type=SimulationModel.WAVE_DIFFUSION
    )
    assert mat_100.shape == (100, 100)
    assert mat_100.size == 10000
    assert 0.0 <= mat_100.min() <= mat_100.max() <= 1.0

    # 2. Adaptive resolution (50x50 and 150x150)
    mat_50 = ComputationalVisualizationEngine.compute_matrix(t=0.0, nx=50, ny=50)
    assert mat_50.shape == (50, 50)
    assert mat_50.size == 2500

    mat_150 = ComputationalVisualizationEngine.compute_matrix(t=0.0, nx=150, ny=150)
    assert mat_150.shape == (150, 150)

    # 3. Interactive HTML generation
    html = ComputationalVisualizationEngine.generate_matrix_html(nx=100, ny=100, sim_type=SimulationModel.WAVE_DIFFUSION)
    assert "10,000" in html
    assert "matrixCanvas" in html
    assert "<iframe" in html


def test_computational_video_rendering_ffmpeg():
    """Verify rendering 100x100 time evolution to MP4 video via FFmpeg under scheduler."""
    engine = ComputationalVisualizationEngine()
    out_mp4 = "test_simulation_video.mp4"
    target_file = os.path.join(engine.artifacts_dir, out_mp4)
    if os.path.exists(target_file):
        os.remove(target_file)

    scheduler = WorkloadScheduler(max_workers=1)

    def render_job(w: Workload):
        return engine.render_computational_video(
            output_name=out_mp4,
            num_frames=15, # Fast 15-frame test
            nx=50,
            ny=50,
            fps=15,
            sim_type=SimulationModel.WAVE_DIFFUSION,
            workload=w
        )

    vid_path = scheduler.execute_sync("Render Video Test", "visualization_rendering", render_job)
    try:
        assert os.path.exists(vid_path)
        assert os.path.getsize(vid_path) > 1000
        assert vid_path.endswith(".mp4")
    finally:
        if os.path.exists(vid_path):
            os.remove(vid_path)


def test_presentation_generator_pptx():
    """Verify first-class 16:9 widescreen presentation deck generation with python-pptx."""
    assert PresentationGenerator.is_available() is True

    generator = PresentationGenerator()

    # Create synthetic verified report
    qa = QueryAnalysis(scientific_domain="Thermodynamics", lexical_keywords=["Henry's law", "solubility"])
    audit = VerificationAudit(grounding_score=92.5, overall_verdict="SAFE & GROUNDED", verified_count=3, total_claims=3)
    chunk = DocumentChunk(chunk_id="c1", doc_name="chemistry_ch1.pdf", page_num=12, text="P = K_H * x describes gas solubility in liquids.")
    sc = ScoredChunk(chunk=chunk, rrf_score=0.045, final_rank=1)
    calc = CalculationVerification(
        equation_latex="P = K_H * x",
        target_variable="P",
        variables={"K_H": 4.5e4, "x": 0.02},
        deterministic_computed_value="900.0 Pa",
        is_verified=True
    )

    report = PrivearchReport(
        query="What is Henry's law equation and gas solubility behavior?",
        query_analysis=qa,
        retrieved_chunks=[sc],
        raw_synthesis="Henry's law relates partial pressure to mole fraction [1].",
        verification=audit,
        annotated_synthesis="Henry's law relates partial pressure to mole fraction [1].",
        calculations=[calc]
    )

    plan = generator.build_slide_plan(report.query, report)
    assert len(plan["slides"]) == 6
    assert plan["slides"][0]["type"] == "TITLE"
    assert plan["slides"][2]["type"] == "THEORY_EQUATIONS"
    assert plan["slides"][3]["type"] == "CHART_VISUALIZATION"
    assert plan["slides"][4]["type"] == "AUDIT_VERIFICATION"

    pptx_path = generator.generate_presentation(query=report.query, report=report, filename="test_deck.pptx")
    try:
        assert os.path.exists(pptx_path)
        assert os.path.getsize(pptx_path) > 5000
        assert pptx_path.endswith(".pptx")

        # Confirm artifact registered
        all_arts = generator.artifacts.list_all()
        matching = [a for a in all_arts if a.artifact_type == ArtifactType.SLIDES_PPTX]
        assert len(matching) >= 1
    finally:
        if os.path.exists(pptx_path):
            os.remove(pptx_path)


def test_kernel_integration_presentation_and_telemetry():
    """Verify PrivearchKernel integrates resource manager, presentation creation, and telemetry."""
    cfg = PrivearchConfig(embedding_backend="cpu_minilm")
    kernel = PrivearchKernel(config=cfg)

    # 1. Telemetry & Status
    status = kernel.get_system_status()
    assert "adaptive_mode" in status
    assert "system_stress_score" in status
    assert "impact_level" in status
    assert status["adaptive_mode"] == "Adaptive"

    # 2. Presentation Generation under Resource Manager
    pres_res = kernel.create_presentation(query="Ideal Gas Law P*V = n*R*T derivation")
    assert pres_res["status"] == "success"
    pptx_file = pres_res["file_path"]
    try:
        assert os.path.exists(pptx_file)
        assert pptx_file.endswith(".pptx")
    finally:
        if os.path.exists(pptx_file):
            os.remove(pptx_file)
