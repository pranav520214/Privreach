"""Render Scene 03: INSIDE THE WORKSPACE (01:10 - 02:10 | 60.0s = 1,440 Frames @ 24 fps)"""

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

TOTAL_FRAMES = 1440
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene03():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\03_workspace"
    out_mp4 = os.path.join(out_dir, "scene03.mp4")
    print(f"[*] Rendering Scene 03: Inside the Workspace (1440 frames) -> {out_mp4}...")
    
    # Load captures
    ws_img = Image.open(r"E:\PrivreachOS\launch_film\assets\product_captures\full_workstation.png").convert("RGB")
    matrix_img = Image.open(r"E:\PrivreachOS\launch_film\assets\product_captures\computational_matrix.png").convert("RGB")
    chat_img = Image.open(r"E:\PrivreachOS\launch_film\assets\product_captures\verification_panel.png").convert("RGB")
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_head = get_font(52, "regular")
    font_sub = get_font(20, "light")
    font_card_title = get_font(24, "bold")
    font_label = get_font(13, "bold")
    font_code = get_font(14, "mono")
    font_body = get_font(15, "regular")

    cx, cy = WIDTH // 2, HEIGHT // 2

    # Pre-render a 100x100 matrix grid base
    grid_size = 50 # 50x50 dots for crisp rendering
    dot_spacing = 10

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        draw_grid(draw, WIDTH, HEIGHT, step=80)

        # -------------------------------------------------------------
        # Part A (0s - 18s): Full Three-Panel Workstation Tour
        # -------------------------------------------------------------
        if t < 20.0:
            p_a_prog = min(t / 18.0, 1.0)
            
            # Subtle pan / push-in
            scale = 1.0 + 0.04 * (t / 18.0)
            target_w = int(1620 * scale)
            target_h = int(1012 * scale)
            cur_ws = ws_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            ws_x = cx - target_w // 2
            ws_y = cy - target_h // 2 + 10
            
            draw_card(draw, (ws_x - 6, ws_y - 6, ws_x + target_w + 6, ws_y + target_h + 6), radius=12, shadow=True)
            img.paste(cur_ws, (ws_x, ws_y))
            
            # Contextual callout brackets (04s - 16s)
            c_alpha = get_fade_alpha(t, 3.0, 5.0, 15.0, 17.0)
            if c_alpha > 0:
                col_bracket = blend_color(BG_WARM_WHITE, ELECTRIC_BLUE, c_alpha)
                # Bracket 1: Domain Navigation
                bx0, by0, bx1, by1 = ws_x + 10, ws_y + 40, ws_x + 280, ws_y + target_h - 20
                draw.rectangle([bx0, by0, bx1, by1], outline=col_bracket, width=2)
                draw.text((bx0 + 10, by0 - 24), "1. DOMAIN ARCHITECTURE", font=font_label, fill=col_bracket)
                
                # Bracket 2: Computational Canvas
                cx0, cy0, cx1, cy1 = ws_x + 295, ws_y + 40, ws_x + 1120, ws_y + 700
                draw.rectangle([cx0, cy0, cx1, cy1], outline=col_bracket, width=2)
                draw.text((cx0 + 10, cy0 - 24), "2. COMPUTATIONAL CANVAS", font=font_label, fill=col_bracket)
                
                # Bracket 3: Adversarial Research Panel
                rx0, ry0, rx1, ry1 = ws_x + 1135, ws_y + 40, ws_x + target_w - 15, ws_y + target_h - 20
                draw.rectangle([rx0, ry0, rx1, ry1], outline=col_bracket, width=2)
                draw.text((rx0 + 10, ry0 - 24), "3. VERIFICATION & CITATION MATRIX", font=font_label, fill=col_bracket)

            # Headline: "Your research." (05s - 14s)
            h_alpha = get_fade_alpha(t, 4.5, 6.0, 13.0, 15.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "Your research.", 70, WIDTH, font_head, fill=col_h)

        # -------------------------------------------------------------
        # Part B (18s - 38s): The 100x100 Computational Dot Matrix
        # -------------------------------------------------------------
        elif t < 40.0:
            s_t = t - 18.0
            
            # Central Matrix Showcase Card
            mat_card_w = 1100
            mat_card_h = 760
            mc_x0 = cx - mat_card_w // 2
            mc_y0 = cy - mat_card_h // 2 + 30
            mc_x1 = mc_x0 + mat_card_w
            mc_y1 = mc_y0 + mat_card_h
            
            draw_card(draw, (mc_x0, mc_y0, mc_x1, mc_y1), radius=16, shadow=True)
            
            # Header bar of Matrix View
            draw.rectangle([mc_x0, mc_y0, mc_x1, mc_y0 + 55], fill=(248, 250, 252))
            draw.line([(mc_x0, mc_y0 + 55), (mc_x1, mc_y0 + 55)], fill=BORDER_MIST, width=1)
            draw.text((mc_x0 + 25, mc_y0 + 16), "COMPUTATIONAL MATRIX // 100×100 FLUID SIMULATION", font=font_label, fill=INK_NAVY)
            
            # Pill Badges
            # Badge 1: 60 fps
            b1_x = mc_x1 - 320
            draw.rounded_rectangle([b1_x, mc_y0 + 12, b1_x + 85, mc_y0 + 42], radius=6, fill=PALE_BLUE, outline=ELECTRIC_BLUE)
            draw.text((b1_x + 14, mc_y0 + 17), "60 fps", font=font_label, fill=ELECTRIC_BLUE)
            # Badge 2: Grid View
            b2_x = mc_x1 - 220
            draw.rounded_rectangle([b2_x, mc_y0 + 12, b2_x + 95, mc_y0 + 42], radius=6, fill=WHITE, outline=BORDER_MIST)
            draw.text((b2_x + 12, mc_y0 + 17), "Grid View", font=font_label, fill=TEXT_MUTED)
            # Badge 3: 100x100
            b3_x = mc_x1 - 110
            draw.rounded_rectangle([b3_x, mc_y0 + 12, b3_x + 90, mc_y0 + 42], radius=6, fill=WHITE, outline=BORDER_MIST)
            draw.text((b3_x + 10, mc_y0 + 17), "100×100", font=font_label, fill=TEXT_MUTED)

            # Draw procedural animated 50x50 dot wave inside matrix canvas
            mx_start = mc_x0 + 60
            my_start = mc_y0 + 80
            time_phase = s_t * 2.5
            
            # Vectorized dot drawing
            for row in range(grid_size):
                for col in range(grid_size):
                    # 2D radial wave formula simulating shockwave interference
                    dx = col - grid_size / 2.0
                    dy = row - grid_size / 2.0
                    dist = math.sqrt(dx * dx + dy * dy)
                    wave = math.sin(dist * 0.45 - time_phase) + math.cos(col * 0.3 + time_phase * 0.8)
                    
                    px = mx_start + col * (dot_spacing + 1)
                    py = my_start + row * (dot_spacing + 1)
                    
                    if wave > 0.8:
                        # Highlighted active wave crest (Electric blue)
                        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=ELECTRIC_BLUE)
                    elif wave > -0.2:
                        # Standard dot (Slate)
                        draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(203, 213, 225))
                    else:
                        # Subdued node
                        draw.point((px, py), fill=(226, 232, 240))
            
            # Scientific Telemetry HUD Card on right side of matrix
            hud_x0 = mc_x0 + 640
            hud_y0 = mc_y0 + 90
            hud_x1 = mc_x1 - 50
            hud_y1 = mc_y1 - 60
            draw_card(draw, (hud_x0, hud_y0, hud_x1, hud_y1), fill=WHITE, radius=12, shadow=False)
            draw.text((hud_x0 + 20, hud_y0 + 20), "AERODYNAMIC TELEMETRY", font=font_label, fill=ELECTRIC_BLUE)
            
            metrics = [
                ("Mach Number", "0.78 M", "Subsonic cruise speed"),
                ("Reynolds Number", "6.5 × 10⁶", "Airfoil chord boundary"),
                ("Boundary Layer", "0.012 m", "Transition thickness"),
                ("Peak Vorticity", "42.8 s⁻¹", "Trailing edge vortex"),
                ("Lift-to-Drag", "18.42 L/D", "Cruise efficiency factor"),
                ("Stall Angle", "14.2° AoA", "NACA 64-416 critical angle")
            ]
            for i, (m_title, m_val, m_desc) in enumerate(metrics):
                y_pos = hud_y0 + 60 + i * 85
                draw.text((hud_x0 + 20, y_pos), m_title, font=font_body, fill=TEXT_MUTED)
                draw.text((hud_x0 + 20, y_pos + 22), m_val, font=font_card_title, fill=INK_NAVY)
                draw.text((hud_x0 + 20, y_pos + 52), m_desc, font=font_label, fill=TEXT_SUBTLE)
                if i < len(metrics) - 1:
                    draw.line([(hud_x0 + 20, y_pos + 72), (hud_x1 - 20, y_pos + 72)], fill=BORDER_MIST, width=1)

            # Headline: "Your tools." (22s - 34s)
            h_alpha = get_fade_alpha(t, 22.0, 24.0, 34.0, 36.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "Your tools.", 50, WIDTH, font_head, fill=col_h)

        # -------------------------------------------------------------
        # Part C (38s - 60s): System Monitors & Multi-Domain Architecture
        # -------------------------------------------------------------
        else:
            s_t = t - 38.0
            
            # Grid of 2 Cards: Left = Live System Status, Right = Domain Switcher
            c1_x0, c1_y0, c1_x1, c1_y1 = cx - 740, cy - 300, cx - 40, cy + 340
            c2_x0, c2_y0, c2_x1, c2_y1 = cx + 40, cy - 300, cx + 740, cy + 340
            
            # Left Card: Authentic System Telemetry
            draw_card(draw, (c1_x0, c1_y0, c1_x1, c1_y1), radius=16, shadow=True)
            draw.text((c1_x0 + 30, c1_y0 + 30), "SYSTEM ARCHITECTURE & RUNTIME", font=font_label, fill=TEXT_MUTED)
            draw.text((c1_x0 + 30, c1_y0 + 58), "Hardware Resource Telemetry", font=font_card_title, fill=INK_NAVY)
            
            # Status Indicators (100% Truthful / Verified)
            sys_items = [
                ("Local LLM Engine", "Gemma 3 1B IT", "Native In-Process GGUF via llama.cpp", MINT_GREEN, "ONLINE"),
                ("System CPU", "7.2% Utilized", "Balanced asynchronous thread allocation", MINT_GREEN, "OPTIMAL"),
                ("Physical RAM", "0.6 / 32.0 GB", "High-efficiency FAISS & BM25 index", MINT_GREEN, "VERIFIED"),
                ("Airgap Security", "Active", "Zero outbound telemetry, fully local sandbox", MINT_GREEN, "AIRGAPPED")
            ]
            for i, (name, val, desc, dot_col, badge_text) in enumerate(sys_items):
                y_i = c1_y0 + 120 + i * 115
                draw.rectangle([c1_x0 + 30, y_i, c1_x1 - 30, y_i + 95], fill=(248, 250, 252), outline=BORDER_MIST)
                draw.ellipse([c1_x0 + 45, y_i + 22, c1_x0 + 57, y_i + 34], fill=dot_col)
                draw.text((c1_x0 + 68, y_i + 18), name, font=font_label, fill=INK_NAVY)
                
                # Badge pill
                bw = 90
                draw.rounded_rectangle([c1_x1 - bw - 45, y_i + 16, c1_x1 - 45, y_i + 38], radius=4, fill=MINT_BG, outline=MINT_GREEN)
                draw.text((c1_x1 - bw - 35, y_i + 20), badge_text, font=font_label, fill=MINT_GREEN)
                
                draw.text((c1_x0 + 45, y_i + 46), val, font=font_card_title, fill=INK_NAVY)
                draw.text((c1_x0 + 45, y_i + 72), desc, font=font_body, fill=TEXT_MUTED)

            # Right Card: Multi-Domain Switcher
            draw_card(draw, (c2_x0, c2_y0, c2_x1, c2_y1), radius=16, shadow=True)
            draw.text((c2_x0 + 30, c2_y0 + 30), "RESEARCH WORKSPACES", font=font_label, fill=TEXT_MUTED)
            draw.text((c2_x0 + 30, c2_y0 + 58), "Scientific Domain Switcher", font=font_card_title, fill=INK_NAVY)
            
            domains = [
                ("Aerospace", "Wing Design & Subsonic Cruise Aerodynamics", "C_L = 2L / (ρ v² S)", "Active Project"),
                ("Physics", "Thermodynamics & Adiabatic Gas Expansion", "P = n R T / V", "Equilibrium Study"),
                ("Biology", "Pharmacokinetics & Receptor Binding Kinetics", "CL = V_d · k_el", "Target Assay"),
                ("Chemistry", "Gibbs Free Energy & Reaction Spontaneity", "ΔG = ΔH - T ΔS", "Equilibrium Calc")
            ]
            
            # Animate active domain selection cycling
            active_dom_idx = int(s_t // 5.0) % 4
            
            for i, (d_name, d_title, d_eq, d_status) in enumerate(domains):
                y_i = c2_y0 + 120 + i * 115
                is_active = (i == active_dom_idx)
                
                b_col = ELECTRIC_BLUE if is_active else BORDER_MIST
                f_col = PALE_BLUE if is_active else WHITE
                draw.rectangle([c2_x0 + 30, y_i, c2_x1 - 30, y_i + 95], fill=f_col, outline=b_col, width=2 if is_active else 1)
                
                draw.text((c2_x0 + 45, y_i + 18), d_name.upper(), font=font_label, fill=ELECTRIC_BLUE if is_active else TEXT_MUTED)
                if is_active:
                    draw.rounded_rectangle([c2_x1 - 140, y_i + 14, c2_x1 - 45, y_i + 38], radius=4, fill=ELECTRIC_BLUE)
                    draw.text((c2_x1 - 130, y_i + 19), "SELECTED", font=font_label, fill=WHITE)
                    
                draw.text((c2_x0 + 45, y_i + 44), d_title, font=font_card_title if is_active else font_body, fill=INK_NAVY)
                draw.text((c2_x0 + 45, y_i + 70), f"Governing: {d_eq}", font=font_code, fill=ELECTRIC_BLUE if is_active else TEXT_MUTED)

            # Headline: "One workspace." (44s - 56s)
            h_alpha = get_fade_alpha(t, 44.0, 46.0, 56.0, 58.0)
            if h_alpha > 0:
                col_h = blend_color(BG_WARM_WHITE, INK_NAVY, h_alpha)
                draw_text_centered(draw, "One workspace.", 50, WIDTH, font_head, fill=col_h)

        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 03 rendered successfully.")

if __name__ == "__main__":
    render_scene03()
