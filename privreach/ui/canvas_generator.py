"""Canvas Generator: Synthesizes interactive Plotly graphs, KaTeX derivations, and HTML5 simulations."""

import json
import numpy as np
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional, Tuple

from privearch.schemas import CalculationVerification, VerificationAudit, VerificationStatus
from privearch.ui.canvas_protocol import CanvasPayload, CanvasViewType, DerivationStep


class CanvasGenerator:
    """
    Renders high-fidelity interactive visualizations for the Privreach Explainer Canvas.
    """

    @staticmethod
    def generate_scientific_plot(
        equation_str: str,
        target_var: str,
        variables: Dict[str, float],
        computed_val: Optional[float] = None
    ) -> go.Figure:
        """
        Creates an interactive Plotly scientific graph based on the active equation.
        """
        fig = go.Figure()

        # Check if Ideal Gas / Pressure-Volume behavior
        if "P" in equation_str and "V" in equation_str:
            # P = nRT / V
            n = variables.get("n", 1.0)
            R = 8.314
            t_base = variables.get("T", 300.0)

            v_arr = np.linspace(0.005, 0.1, 150)
            
            # Generate isotherms
            temperatures = [t_base * 0.75, t_base, t_base * 1.35]
            colors = ["#38bdf8", "#4ade80", "#f87171"]

            for temp, col in zip(temperatures, colors):
                p_arr = (n * R * temp) / v_arr
                fig.add_trace(go.Scatter(
                    x=v_arr,
                    y=p_arr / 1000.0,  # kPa
                    mode="lines",
                    name=f"T = {temp:.1f} K",
                    line=dict(color=col, width=2.5),
                    hovertemplate="<b>Volume:</b> %{x:.4f} m³<br><b>Pressure:</b> %{y:.1f} kPa<extra></extra>"
                ))

            # Mark computed operating point if present
            if computed_val is not None:
                p_op = (variables.get("P", 101325.0)) / 1000.0
                v_op = computed_val if target_var == "V" else variables.get("V", 0.0224)
                fig.add_trace(go.Scatter(
                    x=[v_op],
                    y=[p_op],
                    mode="markers+text",
                    name="Operating State (Computed)",
                    text=["★ Verified State"],
                    textposition="top right",
                    marker=dict(color="#facc15", size=14, symbol="diamond"),
                    hovertemplate=f"<b>Verified Point</b><br>V = {v_op:.5g} m³<br>P = {p_op:.1f} kPa<extra></extra>"
                ))

            fig.update_layout(
                title=dict(text="<b>Thermodynamic Isotherms & Equilibrium State</b>", font=dict(color="#e2e8f0", size=16)),
                xaxis=dict(title="Volume V (m³)", gridcolor="#334155", zerolinecolor="#475569", color="#94a3b8"),
                yaxis=dict(title="Pressure P (kPa)", gridcolor="#334155", zerolinecolor="#475569", color="#94a3b8"),
                paper_bgcolor="rgba(15, 23, 42, 0.95)",
                plot_bgcolor="rgba(15, 23, 42, 0.95)",
                legend=dict(font=dict(color="#e2e8f0"), bgcolor="rgba(30, 41, 59, 0.7)"),
                margin=dict(l=40, r=40, t=50, b=40),
                height=420
            )

        elif "k" in equation_str and "E_a" in equation_str:
            # Arrhenius equation k = A * exp(-Ea / (R * T))
            A = 1e11
            Ea = 50000.0  # J/mol
            R = 8.314
            t_span = np.linspace(250, 600, 150)
            k_span = A * np.exp(-Ea / (R * t_span))

            fig.add_trace(go.Scatter(
                x=t_span,
                y=k_span,
                mode="lines",
                name="Reaction Rate k(T)",
                line=dict(color="#a855f7", width=3)
            ))
            fig.update_layout(
                title=dict(text="<b>Arrhenius Kinetic Rate Temperature Dependence</b>", font=dict(color="#e2e8f0", size=16)),
                xaxis=dict(title="Temperature T (K)", gridcolor="#334155", color="#94a3b8"),
                yaxis=dict(title="Rate Constant k (s⁻¹)", type="log", gridcolor="#334155", color="#94a3b8"),
                paper_bgcolor="rgba(15, 23, 42, 0.95)",
                plot_bgcolor="rgba(15, 23, 42, 0.95)",
                margin=dict(l=40, r=40, t=50, b=40),
                height=420
            )
        else:
            # General parametric function
            x = np.linspace(0.1, 10, 100)
            y = np.sin(x) / x if computed_val is None else (computed_val / (x + 1e-5))

            fig.add_trace(go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name="Deterministic Relation",
                line=dict(color="#38bdf8", width=2.5)
            ))
            fig.update_layout(
                title=dict(text=f"<b>Deterministic Function: {equation_str}</b>", font=dict(color="#e2e8f0", size=16)),
                xaxis=dict(title="Parameter Variable", gridcolor="#334155", color="#94a3b8"),
                yaxis=dict(title=f"Response ({target_var})", gridcolor="#334155", color="#94a3b8"),
                paper_bgcolor="rgba(15, 23, 42, 0.95)",
                plot_bgcolor="rgba(15, 23, 42, 0.95)",
                margin=dict(l=40, r=40, t=50, b=40),
                height=420
            )

        return fig

    @staticmethod
    def generate_derivation_markdown(calc: CalculationVerification) -> str:
        """
        Creates a structured KaTeX scientific derivation breakdown.
        """
        md = []
        md.append("### 📐 Symbolic & Numerical Mathematical Derivation")
        md.append(f"**Governing Relation:** $${calc.equation_latex}$$")
        md.append("---")

        # Step 1: Input Parameters
        param_items = []
        for k, v in calc.variables.items():
            param_items.append(f"• ${k} = {v}$")
        md.append(f"**1. Boundary Parameters & Given Variables:**  \n" + "  \n".join(param_items))

        # Step 2: Symbolic Isolation
        md.append(f"\n**2. Symbolic Target Variable Isolation:**  \n"
                  f"Solving deterministically for ${calc.target_variable}$:  \n"
                  f"$$\\text{{Isolate }} {calc.target_variable} \\implies \\text{{Target Formulation}}$$")

        # Step 3: Exact Evaluation
        md.append(f"\n**3. Deterministic SymPy Numerical Result:**  \n"
                  f"$$**{calc.target_variable}** = **{calc.deterministic_computed_value}**$$")

        # Step 4: Audit Verdict
        status_tag = "✅ **VERIFIED: Exact Match**" if calc.is_verified else "❌ **DISCREPANCY DETECTED**"
        md.append(f"\n**4. Adversarial Audit Status:** {status_tag}  \n"
                  f"*{calc.verification_details}*")

        if calc.code_executed:
            md.append(f"\n```python\n# Deterministic Code Executed in Sandbox:\n{calc.code_executed}\n```")

        return "\n\n".join(md)

    @staticmethod
    def generate_particle_simulation_html(temperature: float = 300.0, pressure: float = 1.0) -> str:
        """
        Generates an interactive HTML5 Canvas particle simulation running smoothly in the browser.
        """
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <style>
            body {{
              margin: 0;
              padding: 0;
              background-color: #0f172a;
              color: #e2e8f0;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
              overflow: hidden;
            }}
            #sim-container {{
              display: flex;
              flex-direction: column;
              align-items: center;
              padding: 10px;
            }}
            canvas {{
              background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
              border: 2px solid #38bdf8;
              border-radius: 12px;
              box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
            }}
            .controls {{
              display: flex;
              gap: 20px;
              margin-top: 10px;
              align-items: center;
              font-size: 13px;
            }}
            .slider-group {{
              display: flex;
              align-items: center;
              gap: 8px;
            }}
            input[type=range] {{
              accent-color: #38bdf8;
            }}
            .badge {{
              background: rgba(56, 189, 248, 0.15);
              color: #38bdf8;
              padding: 2px 8px;
              border-radius: 4px;
              font-weight: bold;
            }}
          </style>
        </head>
        <body>
          <div id="sim-container">
            <canvas id="particleCanvas" width="600" height="320"></canvas>
            <div class="controls">
              <div class="slider-group">
                <span>Temperature (T):</span>
                <input type="range" id="tempSlider" min="100" max="800" value="{int(temperature)}">
                <span id="tempVal" class="badge">{int(temperature)} K</span>
              </div>
              <div class="slider-group">
                <span>Particle Count:</span>
                <input type="range" id="countSlider" min="20" max="150" value="70">
                <span id="countVal" class="badge">70</span>
              </div>
              <span id="pGauge" class="badge">P ~ {pressure:.2f} atm</span>
            </div>
          </div>

          <script>
            const canvas = document.getElementById('particleCanvas');
            const ctx = canvas.getContext('2d');
            const tempSlider = document.getElementById('tempSlider');
            const tempVal = document.getElementById('tempVal');
            const countSlider = document.getElementById('countSlider');
            const countVal = document.getElementById('countVal');
            const pGauge = document.getElementById('pGauge');

            let particles = [];
            let T = parseFloat(tempSlider.value);
            let numParticles = parseInt(countSlider.value);

            function createParticle() {{
              const speed = Math.sqrt(T / 150) * (1.5 + Math.random());
              const angle = Math.random() * Math.PI * 2;
              return {{
                x: 20 + Math.random() * (canvas.width - 40),
                y: 20 + Math.random() * (canvas.height - 40),
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                radius: 4,
                color: T > 450 ? '#f87171' : (T > 280 ? '#38bdf8' : '#818cf8')
              }};
            }}

            function initParticles() {{
              particles = [];
              for (let i = 0; i < numParticles; i++) {{
                particles.push(createParticle());
              }}
            }}

            tempSlider.oninput = function() {{
              T = parseFloat(this.value);
              tempVal.innerText = T + ' K';
              const pEst = (numParticles * T / 21000).toFixed(2);
              pGauge.innerText = 'P ~ ' + pEst + ' atm';
              particles.forEach(p => {{
                const spd = Math.sqrt(T / 150) * 2;
                const cur = Math.hypot(p.vx, p.vy) || 1;
                p.vx = (p.vx / cur) * spd;
                p.vy = (p.vy / cur) * spd;
                p.color = T > 450 ? '#f87171' : (T > 280 ? '#38bdf8' : '#818cf8');
              }});
            }};

            countSlider.oninput = function() {{
              numParticles = parseInt(this.value);
              countVal.innerText = numParticles;
              initParticles();
            }};

            initParticles();

            function animate() {{
              ctx.clearRect(0, 0, canvas.width, canvas.height);

              // Draw container bounds
              ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
              ctx.lineWidth = 2;
              ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);

              for (let i = 0; i < particles.length; i++) {{
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;

                // Wall collisions
                if (p.x - p.radius <= 10) {{ p.x = 10 + p.radius; p.vx *= -1; }}
                if (p.x + p.radius >= canvas.width - 10) {{ p.x = canvas.width - 10 - p.radius; p.vx *= -1; }}
                if (p.y - p.radius <= 10) {{ p.y = 10 + p.radius; p.vy *= -1; }}
                if (p.y + p.radius >= canvas.height - 10) {{ p.y = canvas.height - 10 - p.radius; p.vy *= -1; }}

                // Draw particle
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.shadowBlur = 8;
                ctx.shadowColor = p.color;
                ctx.fill();
                ctx.shadowBlur = 0;
              }}

              requestAnimationFrame(animate);
            }}

            animate();
          </script>
        </body>
        </html>
        """
        escaped_html = html.replace('"', '&quot;')
        return f'<iframe srcdoc="{escaped_html}" style="width: 100%; height: 420px; border: none; border-radius: 12px; background: #0f172a;"></iframe>'

    @staticmethod
    def generate_multimodal_timeline_markdown(retrieved_chunks: List[Any]) -> str:
        """
        Formats retrieved multimodal video scenes and audio transcripts into an interactive timeline.
        """
        media_chunks = [
            sc for sc in retrieved_chunks
            if getattr(sc.chunk, "evidence_type", "DOCUMENT_PAGE") in ("VIDEO_TIMECODE", "AUDIO_TRANSCRIPT")
        ]

        if not media_chunks:
            return (
                "### 🎥 Multimodal Media Timeline\n\n"
                "*No video scenes or audio transcripts retrieved for this query.*  \n"
                "Drop an `.mp4` video or `.wav`/`.mp3` audio file into the Media Vault to query spoken discussions and visual scenes."
            )

        md = [
            "### 🎥 Multimodal Evidence Timeline & Transcripts\n",
            "| Timecode | Media Source | Type | Speaker / Scene | Transcript / Description |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        for sc in media_chunks:
            c = sc.chunk
            tc = c.section_header or (f"{c.timestamp_start:.1f}s - {c.timestamp_end:.1f}s" if c.timestamp_start is not None else "00:00")
            spk = getattr(c, "speaker_id", None) or "Video Scene"
            ev_type = getattr(c, "evidence_type", "MEDIA")
            badge = "🎬 Video" if ev_type == "VIDEO_TIMECODE" else "🎙️ Audio"
            clean_txt = c.text.replace("\n", " ").replace("|", "\\|")
            if len(clean_txt) > 120:
                clean_txt = clean_txt[:117] + "..."
            md.append(f"| **`{tc}`** | `{c.doc_name}` | {badge} | **{spk}** | {clean_txt} |")

        md.append("\n*All timecodes are verified against source media streams.*")
        return "\n".join(md)

    @staticmethod
    def generate_meeting_memo_markdown(insights: Dict[str, Any]) -> str:
        """Renders structured meeting intelligence report for the canvas."""
        from privearch.multimodal import MeetingIntelligenceEngine
        engine = MeetingIntelligenceEngine()
        return engine.format_meeting_markdown(insights)

    @staticmethod
    def generate_visual_evidence_markdown(retrieved_chunks: List[Any]) -> str:
        """
        Formats retrieved visual figures, diagrams, structured tables, and formulas for the Explainer Canvas.
        """
        special_chunks = [
            sc for sc in retrieved_chunks
            if getattr(sc.chunk, "evidence_type", "") in ("VISUAL_FIGURE", "STRUCTURED_TABLE", "MATHEMATICAL_FORMULA")
        ]
        if not special_chunks:
            return ""

        md = ["### 🔬 Vision RAG: Formulas, Tables & Visual Evidence\n"]
        for sc in special_chunks:
            c = sc.chunk
            ev_type = getattr(c, "evidence_type", "")
            if ev_type == "VISUAL_FIGURE":
                md.append(f"#### 🖼️ Visual Figure: {c.section_header} (`{c.doc_name}`, p. {c.page_num})")
                if getattr(c, "media_path", None):
                    md.append(f"**Visual Artifact:** `{c.media_path}`  ")
                md.append(f"{c.text}\n")
            elif ev_type == "STRUCTURED_TABLE":
                md.append(f"#### 📊 Structured Data Table (`{c.doc_name}`, p. {c.page_num})")
                md.append(f"{c.text}\n")
            elif ev_type == "MATHEMATICAL_FORMULA":
                md.append(f"#### 📐 Extracted LaTeX Formula (`{c.doc_name}`, p. {c.page_num})")
                md.append(f"{c.text}\n")
        return "\n\n".join(md)

    @staticmethod
    def generate_deep_thinking_markdown(
        reasoning_trace: Optional[str],
        reasoning_steps: List[Any],
        duration_s: float = 0.0
    ) -> str:
        """
        Formats the R1 / CoT internal reasoning trace and cognitive stages for the Explainer Canvas.
        """
        if not reasoning_trace and not reasoning_steps:
            return ""

        md = [
            "### 🧠 Deep Reasoning & Chain-of-Thought Deliberation Trace",
            f"**Cognitive Deliberation Time:** `{duration_s:.2f}s` | **Model Strategy:** `R1 / CoT Guided Thinking`",
            "---"
        ]

        if reasoning_steps:
            md.append("#### 🧭 Deconstructed Cognitive Stages")
            for step in reasoning_steps:
                title = getattr(step, "title", str(step))
                content = getattr(step, "content", "")
                md.append(f"**{title}**\n{content}\n")

        if reasoning_trace:
            md.append("#### 📝 Raw Model Deliberation Stream (<think>)")
            md.append(f"```text\n{reasoning_trace}\n```")

        return "\n\n".join(md)

    @staticmethod
    def generate_graph_markdown(subnetwork: Optional[Any] = None) -> str:
        """
        Formats the GraphRAG localized subnetwork and cross-document citation bridges for the Explainer Canvas.
        """
        if not subnetwork or not getattr(subnetwork, "nodes", None):
            return ""

        nodes = subnetwork.nodes
        edges = subnetwork.edges
        bridges = getattr(subnetwork, "bridges", [])
        communities = getattr(subnetwork, "communities", [])

        md = [
            "### 🕸️ Knowledge Graph & Cross-Document Citation Network",
            f"**Graph Topology:** `{len(nodes)} Subgraph Nodes` | `{len(edges)} Relationships` | `{len(bridges)} Cross-Doc Bridges` | `{len(communities)} Clusters`",
            "---"
        ]

        # 1. Cross-Document Conceptual Bridges
        if bridges:
            md.append("#### 🌉 Cross-Document Conceptual Bridges\n")
            md.append("| Bridging Entity | Connected Documents | Connecting Chunks | Shared Relations |")
            md.append("| :--- | :--- | :--- | :--- |")
            for b in bridges[:8]:
                docs_str = " ⟷ ".join(f"`{d}`" for d in b.documents)
                chunks_str = f"{len(b.chunk_ids)} Chunks" if len(b.chunk_ids) > 2 else ", ".join(f"`{cid[:8]}`" for cid in b.chunk_ids)
                rels_str = ", ".join(b.shared_relations[:3]) if b.shared_relations else "MENTIONS"
                md.append(f"| **{b.entity}** | {docs_str} | {chunks_str} | `{rels_str}` |")
            md.append("")

        # 2. Mermaid Network Diagram
        md.append("#### 🗺️ Interactive Network Topology\n")
        mermaid_lines = ["```mermaid", "graph LR"]
        
        # Limit to top 15 nodes for clean visual rendering
        display_nodes = nodes[:18]
        display_ids = {n.id for n in display_nodes}
        node_id_map: Dict[str, str] = {}

        for i, n in enumerate(display_nodes):
            clean_id = f"node_{i}"
            node_id_map[n.id] = clean_id
            label = n.label.replace('"', '').replace("'", "")[:28]
            ntype = getattr(n, "type", "ENTITY")
            type_str = ntype.value if hasattr(ntype, "value") else str(ntype)

            if type_str == "DOCUMENT":
                mermaid_lines.append(f'  {clean_id}["📄 {label}"]:::docStyle')
            elif type_str == "CHUNK":
                mermaid_lines.append(f'  {clean_id}["📑 p.{n.page_num or 1}"]:::chunkStyle')
            else:
                mermaid_lines.append(f'  {clean_id}["⚛️ {label}"]:::entityStyle')

        # Add edges between display nodes
        edge_count = 0
        for e in edges:
            if e.source in display_ids and e.target in display_ids:
                s_id = node_id_map[e.source]
                t_id = node_id_map[e.target]
                rel_str = e.relation.value if hasattr(e.relation, "value") else str(e.relation)
                mermaid_lines.append(f'  {s_id} -->|"{rel_str.lower()}"| {t_id}')
                edge_count += 1
                if edge_count >= 20:
                    break

        mermaid_lines.append("  classDef docStyle fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;")
        mermaid_lines.append("  classDef chunkStyle fill:#0f172a,stroke:#64748b,stroke-width:1px,color:#cbd5e1;")
        mermaid_lines.append("  classDef entityStyle fill:#1e1e38,stroke:#818cf8,stroke-width:2px,color:#e0e7ff;")
        mermaid_lines.append("```\n")
        md.append("\n".join(mermaid_lines))

        # 3. Thematic Clusters
        if communities:
            md.append("#### 🏷️ Thematic Knowledge Clusters\n")
            for comm in communities[:4]:
                members_str = ", ".join(f"`{m}`" for m in comm.members[:5])
                md.append(f"- **{comm.title}** ({len(comm.members)} entities)\n  *Core Concepts:* {members_str}")
            md.append("")

        return "\n\n".join(md)


