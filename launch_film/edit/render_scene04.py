"""Render Scene 04: FROM SOURCE TO INSIGHT (02:10 - 03:30 | 80.0s = 1,920 Frames @ 24 fps)"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw
from render_utils import (
    BG_WARM_WHITE, WHITE, INK_NAVY, ELECTRIC_BLUE, BORDER_MIST,
    TEXT_MUTED, TEXT_SUBTLE, PALE_BLUE, MINT_GREEN, MINT_BG,
    get_font, draw_grid, draw_card, draw_text_centered,
    get_fade_alpha, blend_color, create_video_writer
)

TOTAL_FRAMES = 1920
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene04():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\04_evidence"
    out_mp4 = os.path.join(out_dir, "scene04.mp4")
    print(f"[*] Rendering Scene 04: From Source to Insight (1920 frames) -> {out_mp4}...")
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_head = get_font(52, "regular")
    font_card_title = get_font(24, "bold")
    font_paper_title = get_font(28, "bold")
    font_math_lg = get_font(30, "bold")
    font_label = get_font(13, "bold")
    font_code = get_font(15, "mono")
    font_body = get_font(16, "regular")
    font_sm = get_font(13, "regular")

    cx, cy = WIDTH // 2, HEIGHT // 2

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        draw_grid(draw, WIDTH, HEIGHT, step=80)

        # -------------------------------------------------------------
        # Part A (0s - 25s): The Source Document & Equation Isolation
        # -------------------------------------------------------------
        if t < 26.0:
            doc_w = 900
            doc_h = 760
            dx0 = cx - doc_w // 2
            dy0 = cy - doc_h // 2 + 40
            dx1 = dx0 + doc_w
            dy1 = dy0 + doc_h
            
            draw_card(draw, (dx0, dy0, dx1, dy1), radius=14, shadow=True)
            
            # Document Header
            draw.rectangle([dx0, dy0, dx1, dy0 + 50], fill=(248, 250, 252))
            draw.line([(dx0, dy0 + 50), (dx1, dy0 + 50)], fill=BORDER_MIST, width=1)
            draw.text((dx0 + 25, dy0 + 15), "PDF VIEWER // sample_wing_aerodynamics.pdf [Page 1 of 3]", font=font_label, fill=TEXT_MUTED)
            
            # Page Content
            draw.text((dx0 + 60, dy0 + 80), "Aerodynamic Principles of Subsonic Airfoils", font=font_paper_title, fill=INK_NAVY)
            draw.text((dx0 + 60, dy0 + 125), "Dr. Elena Rostova • Department of Aerospace Engineering", font=font_sm, fill=TEXT_MUTED)
            draw.line([(dx0 + 60, dy0 + 155), (dx1 - 60, dy0 + 155)], fill=BORDER_MIST, width=1)
            
            draw.text((dx0 + 60, dy0 + 175), "Abstract & Governing Equations", font=font_card_title, fill=INK_NAVY)
            abstract_text = (
                "This document establishes the governing aerodynamic relations for subsonic wing design.\n"
                "For incompressible flow, the lift coefficient is defined as:"
            )
            draw.text((dx0 + 60, dy0 + 215), abstract_text, font=font_body, fill=INK_NAVY)
            
            # Highlighted Equation Box
            eq_box = (dx0 + 60, dy0 + 285, dx1 - 60, dy0 + 415)
            # Animated blue glow border
            glow = (0.5 + 0.5 * math.sin(t * 3.0)) if t > 8.0 else 0.0
            eq_border = blend_color(BORDER_MIST, ELECTRIC_BLUE, glow)
            draw.rounded_rectangle(eq_box, radius=8, fill=PALE_BLUE if glow > 0.3 else WHITE, outline=eq_border, width=2)
            draw.text((dx0 + 90, dy0 + 310), "C_L = 2 · L / (ρ · v² · S)", font=font_math_lg, fill=ELECTRIC_BLUE)
            draw.text((dx0 + 90, dy0 + 365), "where: L = 12500 N, ρ = 1.225 kg/m³, v = 68.0 m/s, S = 16.2 m²", font=font_code, fill=TEXT_MUTED)
            
            # Supporting paragraphs
            body_text = (
                "The lift coefficient C_L is an essential non-dimensional figure of merit for aeronautical\n"
                "performance and boundary layer stability during subsonic cruise conditions."
            )
            draw.text((dx0 + 60, dy0 + 440), body_text, font=font_body, fill=TEXT_MUTED)
            
            # Subtle page navigation footer
            draw.line([(dx0 + 60, dy1 - 60), (dx1 - 60, dy1 - 60)], fill=BORDER_MIST, width=1)
            draw.text((dx0 + 60, dy1 - 42), "✓ Verified Document Ingestion • SHA-256 Validated", font=font_label, fill=MINT_GREEN)
            draw.text((dx1 - 180, dy1 - 42), "Jump to Page: 1 [Active]", font=font_label, fill=ELECTRIC_BLUE)

            # Headline: "Start with sources." (05s - 19s)
            h_alpha = get_fade_alpha(t, 5.0, 7.0, 19.0, 21.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "Start with sources.", 50, WIDTH, font_head, fill=col_h)

        # -------------------------------------------------------------
        # Part B (25s - 50s): Evidence Extraction & Dynamic Line Linking
        # -------------------------------------------------------------
        elif t < 52.0:
            s_t = t - 25.0
            
            # Left Card: Source Document Snippet (Page 1)
            doc_x0, doc_y0, doc_x1, doc_y1 = cx - 800, cy - 300, cx - 100, cy + 340
            draw_card(draw, (doc_x0, doc_y0, doc_x1, doc_y1), radius=14, shadow=True)
            draw.text((doc_x0 + 30, doc_y0 + 25), "SOURCE EVIDENCE // PAGE 1", font=font_label, fill=ELECTRIC_BLUE)
            draw.text((doc_x0 + 30, doc_y0 + 55), "sample_wing_aerodynamics.pdf", font=font_card_title, fill=INK_NAVY)
            
            draw.rectangle([doc_x0 + 30, doc_y0 + 105, doc_x1 - 30, doc_y0 + 230], fill=PALE_BLUE, outline=ELECTRIC_BLUE, width=1)
            draw.text((doc_x0 + 45, doc_y0 + 120), "EXTRACTED PASSAGE [Chunk #1]:", font=font_label, fill=ELECTRIC_BLUE)
            p_text = (
                "\"For incompressible flow, the lift coefficient is defined as:\n"
                " C_L = 2 * L / (rho * v^2 * S)\n"
                " where: L = 12500 N, rho = 1.225 kg/m^3, v = 68 m/s, S = 16.2 m^2\""
            )
            draw.text((doc_x0 + 45, doc_y0 + 145), p_text, font=font_code, fill=INK_NAVY)
            
            draw.text((doc_x0 + 30, doc_y0 + 260), "Document Metadata & Citation Index:", font=font_label, fill=TEXT_MUTED)
            meta_lines = [
                "• Ingestion Engine: PyMuPDF + BM25 High-Fidelity Chunking",
                "• Indexed Chunks: 11 Semantic Passages (3 Pages)",
                "• Section Hierarchy: Abstract & Governing Equations",
                "• Vector Representation: CPU Local Sentence Embeddings"
            ]
            for i, ml in enumerate(meta_lines):
                draw.text((doc_x0 + 30, doc_y0 + 295 + i * 32), ml, font=font_body, fill=TEXT_MUTED)

            # Right Card: Verification Matrix & Adversarial Claim Card
            cl_x0, cl_y0, cl_x1, cl_y1 = cx + 100, cy - 300, cx + 800, cy + 340
            draw_card(draw, (cl_x0, cl_y0, cl_x1, cl_y1), radius=14, shadow=True)
            draw.text((cl_x0 + 30, cl_y0 + 25), "VERIFICATION MATRIX // CLAIM AUDIT", font=font_label, fill=TEXT_MUTED)
            draw.text((cl_x0 + 30, cl_y0 + 55), "Claim 1: Governing Lift Formulation", font=font_card_title, fill=INK_NAVY)
            
            # Animated Dynamic Connecting Vector Line between cards
            link_prog = min(s_t / 8.0, 1.0)
            pt_start = (doc_x1, doc_y0 + 167)
            pt_end = (cl_x0, cl_y0 + 167)
            cur_end = (int(pt_start[0] + (pt_end[0] - pt_start[0]) * link_prog), pt_start[1])
            draw.line([pt_start, cur_end], fill=ELECTRIC_BLUE, width=2)
            draw.ellipse([cur_end[0] - 4, cur_end[1] - 4, cur_end[0] + 4, cur_end[1] + 4], fill=ELECTRIC_BLUE)
            
            # Claim Card Content
            draw.rectangle([cl_x0 + 30, cl_y0 + 105, cl_x1 - 30, cl_y0 + 250], fill=(248, 250, 252), outline=BORDER_MIST)
            draw.text((cl_x0 + 45, cl_y0 + 120), "GROUNDED CLAIM [1]:", font=font_label, fill=INK_NAVY)
            draw.text((cl_x0 + 45, cl_y0 + 145), "Lift Coefficient Definition & Sea-Level Boundary Parameters", font=font_card_title, fill=INK_NAVY)
            draw.text((cl_x0 + 45, cl_y0 + 180), "Source: sample_wing_aerodynamics.pdf (p. 1)", font=font_code, fill=ELECTRIC_BLUE)
            draw.text((cl_x0 + 45, cl_y0 + 210), "Grounding Confidence: 100.0% • 0 Hallucinations Detected", font=font_label, fill=MINT_GREEN)
            
            # Cross-document citation bridge
            draw.rectangle([cl_x0 + 30, cl_y0 + 280, cl_x1 - 30, cl_y0 + 420], fill=WHITE, outline=BORDER_MIST)
            draw.text((cl_x0 + 45, cl_y0 + 300), "SYNTHESIS INTELLIGENCE // CHAT LINK", font=font_label, fill=TEXT_MUTED)
            draw.text((cl_x0 + 45, cl_y0 + 330), "📄 [1] sample_wing_aerodynamics.pdf (p. 1)", font=font_card_title, fill=ELECTRIC_BLUE)
            draw.text((cl_x0 + 45, cl_y0 + 370), "Clicking citation pill instantly navigates native WebView2 to Page 1.", font=font_body, fill=TEXT_MUTED)

            # Headline: "Follow the evidence." (30s - 45s)
            h_alpha = get_fade_alpha(t, 29.0, 31.0, 45.0, 47.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "Follow the evidence.", 50, WIDTH, font_head, fill=col_h)

        # -------------------------------------------------------------
        # Part C (50s - 80s): Deterministic SymPy Computation & Audit
        # -------------------------------------------------------------
        else:
            s_t = t - 50.0
            
            # Central Master Computation Card
            comp_w = 1100
            comp_h = 760
            cx0 = cx - comp_w // 2
            cy0 = cy - comp_h // 2 + 40
            cx1 = cx0 + comp_w
            cy1 = cy0 + comp_h
            
            draw_card(draw, (cx0, cy0, cx1, cy1), radius=16, shadow=True)
            
            # Header
            draw.rectangle([cx0, cy0, cx1, cy0 + 60], fill=(248, 250, 252))
            draw.line([(cx0, cy0 + 60), (cx1, cy0 + 60)], fill=BORDER_MIST, width=1)
            draw.text((cx0 + 30, cy0 + 20), "DETERMINISTIC SCIENTIFIC COMPUTATION // SYMPY ENGINE", font=font_label, fill=INK_NAVY)
            
            # Audit Stamp Badge (Mint Green)
            badge_w = 190
            draw.rounded_rectangle([cx1 - badge_w - 30, cy0 + 14, cx1 - 30, cy0 + 46], radius=6, fill=MINT_BG, outline=MINT_GREEN)
            draw.text((cx1 - badge_w - 18, cy0 + 20), "✓ VERIFIED (0.0% ERROR)", font=font_label, fill=MINT_GREEN)

            # 1. Target Equation Isolation
            draw.text((cx0 + 40, cy0 + 85), "1. Governing Relation & Boundary Parameters", font=font_label, fill=TEXT_MUTED)
            draw.text((cx0 + 40, cy0 + 115), "C_L = 2 · L / (ρ · v² · S)", font=font_math_lg, fill=ELECTRIC_BLUE)
            draw.text((cx0 + 40, cy0 + 165), "Known Inputs: L = 12500.0 N  •  ρ = 1.225 kg/m³  •  v = 68.0 m/s  •  S = 16.2 m²", font=font_code, fill=INK_NAVY)
            
            draw.line([(cx0 + 40, cy0 + 205), (cx1 - 40, cy0 + 205)], fill=BORDER_MIST, width=1)
            
            # 2. Deterministic SymPy Code Execution
            draw.text((cx0 + 40, cy0 + 225), "2. Sandboxed Python AST Derivation", font=font_label, fill=TEXT_MUTED)
            draw.rectangle([cx0 + 40, cy0 + 255, cx1 - 40, cy0 + 420], fill=(248, 250, 252), outline=BORDER_MIST)
            code_lines = [
                "# Deterministic Evaluation in Zero-Trust Airgapped Sandbox:",
                "import sympy as sp",
                "L, rho, v, S = sp.symbols('L rho v S')",
                "C_L = 2 * L / (rho * v**2 * S)",
                "res = C_L.subs({'L': 12500.0, 'rho': 1.225, 'v': 68.0, 'S': 16.2}).evalf()",
                "# Exact Ground Truth Value: 0.2798038..."
            ]
            for i, cl in enumerate(code_lines):
                draw.text((cx0 + 60, cy0 + 270 + i * 24), cl, font=font_code, fill=ELECTRIC_BLUE if i == 5 else INK_NAVY)

            draw.line([(cx0 + 40, cy0 + 440), (cx1 - 40, cy0 + 440)], fill=BORDER_MIST, width=1)

            # 3. Adversarial Audit Results Comparison
            draw.text((cx0 + 40, cy0 + 460), "3. Adversarial Truth vs Hallucination Audit", font=font_label, fill=TEXT_MUTED)
            
            # Left Sub-Card: Deterministic Truth
            box_t = (cx0 + 40, cy0 + 490, cx0 + 510, cy0 + 630)
            draw.rounded_rectangle(box_t, radius=8, fill=WHITE, outline=MINT_GREEN, width=2)
            draw.text((box_t[0] + 20, box_t[1] + 16), "DETERMINISTIC EVALUATION", font=font_label, fill=MINT_GREEN)
            draw.text((box_t[0] + 20, box_t[1] + 45), "C_L = 0.2798", font=font_math_lg, fill=INK_NAVY)
            draw.text((box_t[0] + 20, box_t[1] + 95), "Exact SymPy numerical solution", font=font_body, fill=TEXT_MUTED)
            
            # Right Sub-Card: Model Claim Check
            box_m = (cx0 + 540, cy0 + 490, cx1 - 40, cy0 + 630)
            draw.rounded_rectangle(box_m, radius=8, fill=WHITE, outline=BORDER_MIST)
            draw.text((box_m[0] + 20, box_m[1] + 16), "MODEL CLAIM VERIFICATION", font=font_label, fill=TEXT_MUTED)
            draw.text((box_m[0] + 20, box_m[1] + 45), "Predicted: 0.2798", font=font_math_lg, fill=INK_NAVY)
            draw.text((box_m[0] + 20, box_m[1] + 95), "Relative Error: 0.00% • Within 5% Tolerance", font=font_body, fill=MINT_GREEN)

            # Bottom Status Bar
            draw.rectangle([cx0, cy1 - 50, cx1, cy1], fill=(241, 245, 249))
            draw.text((cx0 + 30, cy1 - 35), "Audit Status: VERIFIED • Calculation Provenance Preserved in Artifact Registry", font=font_label, fill=INK_NAVY)

            # Headline: "Make the process visible." (55s - 72s)
            h_alpha = get_fade_alpha(t, 54.0, 56.0, 72.0, 74.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "Make the process visible.", 50, WIDTH, font_head, fill=col_h)

        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 04 rendered successfully.")

if __name__ == "__main__":
    render_scene04()
