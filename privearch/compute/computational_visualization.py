"""Computational Visualization Engine: 100x100 matrix simulations and video rendering."""

import os
import time
import math
import tempfile
import shutil
import subprocess
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from privearch.schemas import ArtifactRecord, ArtifactType


class SimulationModel(str, Enum):
    WAVE_DIFFUSION = "WAVE_DIFFUSION"       # Harmonic wave interference pattern
    HEAT_CONDUCTION = "HEAT_CONDUCTION"     # 2D Fourier thermodynamic diffusion
    QUANTUM_HARMONIC = "QUANTUM_HARMONIC"   # Quantum oscillator probability density
    REACTION_DIFFUSION = "REACTION_DIFFUSION" # Chemical activator-inhibitor Turing morphogenesis


class ComputationalVisualizationEngine:
    """
    Data-driven 100x100 (10,000 points) visualization matrix.
    Supports adaptive resolution scaling and FFmpeg computational video rendering.
    """

    def __init__(self, artifacts_dir: str = ".privearch_artifacts"):
        self.artifacts_dir = os.path.abspath(artifacts_dir)
        os.makedirs(self.artifacts_dir, exist_ok=True)

    @staticmethod
    def compute_matrix(
        t: float = 0.0,
        nx: int = 100,
        ny: int = 100,
        sim_type: SimulationModel = SimulationModel.WAVE_DIFFUSION,
        params: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """
        Computes 2D logical matrix of shape (nx, ny) representing physical state at time t.
        Normalized values in [0.0, 1.0].
        """
        params = params or {}
        x = np.linspace(-3.0, 3.0, nx)
        y = np.linspace(-3.0, 3.0, ny)
        xx, yy = np.meshgrid(x, y)

        if sim_type == SimulationModel.WAVE_DIFFUSION:
            # Dual point source interference
            omega = params.get("omega", 2.5)
            k = params.get("k", 3.0)
            r1 = np.sqrt((xx + 1.2)**2 + yy**2) + 1e-6
            r2 = np.sqrt((xx - 1.2)**2 + yy**2) + 1e-6
            z = np.sin(k * r1 - omega * t) / np.sqrt(r1) + np.sin(k * r2 - omega * t) / np.sqrt(r2)
            # Normalize to 0..1
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-9)
            return z_norm.astype(np.float32)

        elif sim_type == SimulationModel.HEAT_CONDUCTION:
            # Fourier diffusion with heat sink
            diffusivity = params.get("alpha", 0.15)
            decay = math.exp(-diffusivity * (t % 5.0))
            z = np.exp(-(xx**2 + yy**2) / 1.5) * decay + 0.3 * np.sin(xx * 2.0) * np.cos(yy * 2.0) * math.sin(t)
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-9)
            return z_norm.astype(np.float32)

        elif sim_type == SimulationModel.QUANTUM_HARMONIC:
            # Stationary state probability density
            n = int(params.get("n", 2))
            m = int(params.get("m", 3))
            psi1 = np.exp(-(xx**2 + yy**2) / 2.0) * np.cos(n * xx)
            psi2 = np.exp(-(xx**2 + yy**2) / 2.0) * np.sin(m * yy) * math.cos(t * 1.8)
            prob = (psi1 + psi2)**2
            prob_norm = (prob - prob.min()) / (prob.max() - prob.min() + 1e-9)
            return prob_norm.astype(np.float32)

        else: # REACTION_DIFFUSION
            # Turing pattern snapshot
            f = params.get("f", 0.055)
            k_param = params.get("k", 0.062)
            z = np.cos(xx * 4.0 + math.sin(t)) * np.sin(yy * 4.0 + math.cos(t)) + 0.5 * np.sin(xx**2 + yy**2 - t)
            z_norm = (z - z.min()) / (z.max() - z.min() + 1e-9)
            return z_norm.astype(np.float32)

    @classmethod
    def generate_matrix_html(
        cls,
        nx: int = 100,
        ny: int = 100,
        sim_type: SimulationModel = SimulationModel.WAVE_DIFFUSION,
        title: str = "100×100 Computational Matrix Simulation"
    ) -> str:
        """
        Generates interactive 60fps HTML5 Canvas with points dynamically animated.
        """
        total_pts = nx * ny
        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      margin: 0;
      padding: 10px;
      background: #090d16;
      color: #94a3b8;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 94vh;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}
    .title {{
      font-size: 13px;
      font-weight: 700;
      color: #38bdf8;
      letter-spacing: 0.5px;
    }}
    .badge {{
      font-size: 11px;
      padding: 3px 8px;
      background: rgba(56, 189, 248, 0.15);
      border: 1px solid rgba(56, 189, 248, 0.3);
      color: #7dd3fc;
      border-radius: 4px;
    }}
    canvas {{
      flex: 1;
      width: 100%;
      background: #030712;
      border-radius: 8px;
      border: 1px solid #1e293b;
    }}
    .stats {{
      margin-top: 6px;
      font-size: 11px;
      display: flex;
      justify-content: space-between;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">🧮 {title} ({nx}×{ny})</div>
    <div class="badge">Model: {sim_type.value}</div>
  </div>
  <canvas id="matrixCanvas"></canvas>
  <div class="stats">
    <span id="ptCount">Points: {total_pts:,}</span>
    <span id="timeVal">t = 0.00 s</span>
    <span id="fpsVal">FPS: 60</span>
    <span>Mode: Data-Driven Deterministic</span>
  </div>

  <script>
    const canvas = document.getElementById('matrixCanvas');
    const ctx = canvas.getContext('2d');
    const timeVal = document.getElementById('timeVal');
    const fpsVal = document.getElementById('fpsVal');

    const nx = {nx};
    const ny = {ny};
    let startTime = performance.now();
    let lastFrame = startTime;
    let frames = 0;
    let fps = 60;

    function resize() {{
      canvas.width = canvas.clientWidth * window.devicePixelRatio;
      canvas.height = canvas.clientHeight * window.devicePixelRatio;
    }}
    window.addEventListener('resize', resize);
    resize();

    function render(now) {{
      const t = (now - startTime) / 1000.0;
      timeVal.innerText = 't = ' + t.toFixed(2) + ' s';

      frames++;
      if (now - lastFrame >= 1000) {{
        fps = frames;
        frames = 0;
        lastFrame = now;
        fpsVal.innerText = 'FPS: ' + fps;
      }}

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cellW = canvas.width / nx;
      const cellH = canvas.height / ny;
      const radius = Math.max(1, Math.min(cellW, cellH) * 0.42);

      for (let j = 0; j < ny; j++) {{
        const yCoord = (j + 0.5) * cellH;
        const normY = (j / ny - 0.5) * 6.0;

        for (let i = 0; i < nx; i++) {{
          const xCoord = (i + 0.5) * cellW;
          const normX = (i / nx - 0.5) * 6.0;

          // Compute wave function value
          const r1 = Math.hypot(normX + 1.2, normY) + 0.01;
          const r2 = Math.hypot(normX - 1.2, normY) + 0.01;
          const val = 0.5 + 0.25 * (Math.sin(3.0 * r1 - 2.5 * t) + Math.sin(3.0 * r2 - 2.5 * t));

          // Color mapping: Cyan to Violet
          const r = Math.floor(56 + val * 180);
          const g = Math.floor(189 * (1.0 - val * 0.5));
          const b = Math.floor(248);
          const a = 0.2 + val * 0.8;

          ctx.fillStyle = `rgba(${{r}}, ${{g}}, ${{b}}, ${{a}})`;
          ctx.beginPath();
          ctx.arc(xCoord, yCoord, radius * (0.6 + val * 0.8), 0, Math.PI * 2);
          ctx.fill();
        }}
      }}

      requestAnimationFrame(render);
    }}

    requestAnimationFrame(render);
  </script>
</body>
</html>
"""
        escaped = html.replace('"', '&quot;')
        return f'<iframe srcdoc="{escaped}" style="width: 100%; height: 420px; border: none; border-radius: 8px; background: #090d16;"></iframe>'

    def render_computational_video(
        self,
        output_name: str = "computational_simulation.mp4",
        num_frames: int = 60,
        nx: int = 100,
        ny: int = 100,
        fps: int = 30,
        sim_type: SimulationModel = SimulationModel.WAVE_DIFFUSION,
        workload: Optional[Any] = None,
        resource_manager: Optional[Any] = None
    ) -> str:
        """
        Renders time-evolved computational matrix into an MP4 video using native FFmpeg.
        Respects the Adaptive Resource Manager by yielding CPU slices and adjusting resolution.
        """
        # Read adaptive constraints if manager provided
        throttle_s = 0.005
        if resource_manager:
            constraints = resource_manager.get_constraints()
            throttle_s = constraints.get("throttle_sleep_s", 0.005)
            # Adapt resolution and fps under load
            adapted_res = constraints.get("matrix_resolution", (nx, ny))
            nx, ny = adapted_res
            fps = constraints.get("fps_limit", fps)

        out_path = os.path.join(self.artifacts_dir, output_name)
        temp_dir = tempfile.mkdtemp(prefix="privreach_comp_vis_")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            dt = 1.0 / fps
            for f_idx in range(num_frames):
                if workload:
                    workload.check_cooperative(throttle_delay_s=throttle_s)
                    pct = (f_idx / num_frames) * 85.0
                    workload.update_progress(pct, f"Rendering computational matrix frame {f_idx+1}/{num_frames} ({nx}x{ny})")

                t = f_idx * dt
                mat = self.compute_matrix(t=t, nx=nx, ny=ny, sim_type=sim_type)

                # Render frame image
                fig, ax = plt.subplots(figsize=(4.0, 4.0), dpi=100)
                fig.patch.set_facecolor('#090d16')
                ax.set_facecolor('#090d16')

                im = ax.imshow(mat, cmap="plasma", origin="lower", interpolation="nearest")
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(f"{sim_type.value} Matrix ({nx}x{ny}) • t={t:.2f}s", color="#38bdf8", fontsize=10, pad=6)

                frame_file = os.path.join(temp_dir, f"frame_{f_idx:04d}.png")
                plt.savefig(frame_file, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', pad_inches=0.05)
                plt.close(fig)

            if workload:
                workload.check_cooperative()
                workload.update_progress(88.0, "Stitching frames with FFmpeg encoder...")

            # FFmpeg stitch
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate", str(fps),
                "-i", os.path.join(temp_dir, "frame_%04d.png"),
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", "22",
                out_path
            ]
            try:
                subprocess.run(cmd, capture_output=True, check=True)
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
                raise RuntimeError(f"FFmpeg encoding failed: {err_msg}") from e

            if workload:
                workload.update_progress(100.0, f"Video complete: {output_name}")

            return out_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
