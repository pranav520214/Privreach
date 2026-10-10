"""Render Scene 05: THE LARGER VISION (03:30 - 04:30 | 60.0s = 1,440 Frames @ 24 fps)"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw
from render_utils import (
    BG_WARM_WHITE, WHITE, INK_NAVY, ELECTRIC_BLUE, BORDER_MIST,
    TEXT_MUTED, TEXT_SUBTLE, PALE_BLUE,
    get_font, draw_grid, draw_card, draw_text_centered,
    get_fade_alpha, blend_color, create_video_writer
)

TOTAL_FRAMES = 1440
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene05():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\05_science"
    out_mp4 = os.path.join(out_dir, "scene05.mp4")
    print(f"[*] Rendering Scene 05: The Larger Vision (1440 frames) -> {out_mp4}...")
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_head = get_font(52, "regular")
    font_title = get_font(20, "bold")
    font_eq = get_font(15, "mono")
    font_label = get_font(12, "bold")
    font_sub = get_font(13, "regular")

    cx, cy = WIDTH // 2, HEIGHT // 2

    # 7 Discipline Nodes placed in an expansive architectural constellation
    # 4 on top row, 3 on bottom row
    disciplines = [
        # (name, subtitle, equation, center_x, center_y, draw_type)
        ("AEROSPACE", "Subsonic Aerodynamics", "C_L = 2L/(ρv²S)", cx - 650, cy - 160, "airfoil"),
        ("PHYSICS", "Thermodynamics & PV State", "P = nRT / V", cx - 220, cy - 160, "thermo"),
        ("BIOLOGY", "Receptor Pharmacokinetics", "CL = V_d · k_el", cx + 220, cy - 160, "dna"),
        ("CHEMISTRY", "Molecular Free Energy", "ΔG = ΔH - TΔS", cx + 650, cy - 160, "molecule"),
        ("ROBOTICS", "Kinematic Multi-Joint Arm", "τ = M(q)q̈ + C(q,q̇)", cx - 440, cy + 220, "robotics"),
        ("MATHEMATICS", "Differential Geometry", "R_μν - ½Rg_μν = T_μν", cx, cy + 220, "manifold"),
        ("ENGINEERING", "Finite Element Stress Grid", "σ = E · ε", cx + 440, cy + 220, "truss")
    ]

    card_w = 360
    card_h = 240

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        draw_grid(draw, WIDTH, HEIGHT, step=80)

        # Dynamic Connection Lines between adjacent disciplines
        # Traces interconnecting electric-blue lines across all nodes
        connect_prog = min(t / 15.0, 1.0)
        line_links = [
            (0, 1), (1, 2), (2, 3), # Top row
            (4, 5), (5, 6),         # Bottom row
            (0, 4), (1, 5), (2, 5), (3, 6) # Cross links
        ]
        
        for idx_a, idx_b in line_links:
            p_a = (disciplines[idx_a][3], disciplines[idx_a][4])
            p_b = (disciplines[idx_b][3], disciplines[idx_b][4])
            cur_b = (
                int(p_a[0] + (p_b[0] - p_a[0]) * connect_prog),
                int(p_a[1] + (p_b[1] - p_a[1]) * connect_prog)
            )
            draw.line([p_a, cur_b], fill=(191, 219, 254), width=1)
            # Animated flowing pulse dot along lines
            if connect_prog > 0.9:
                pulse_phase = (t * 0.8 + idx_a * 0.3) % 1.0
                px = int(p_a[0] + (p_b[0] - p_a[0]) * pulse_phase)
                py = int(p_a[1] + (p_b[1] - p_a[1]) * pulse_phase)
                draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=ELECTRIC_BLUE)

        # Draw Each Discipline Card
        for i, (name, subtitle, eq, dx, dy, d_type) in enumerate(disciplines):
            # Staggered entry animation
            entry_t = t - i * 0.8
            card_alpha = min(max(entry_t / 1.5, 0.0), 1.0)
            
            x0 = dx - card_w // 2
            y0 = dy - card_h // 2
            x1 = x0 + card_w
            y1 = y0 + card_h
            
            if card_alpha > 0.05:
                draw_card(draw, (x0, y0, x1, y1), radius=12, shadow=True)
                draw.text((x0 + 20, y0 + 16), name, font=font_label, fill=ELECTRIC_BLUE)
                draw.text((x0 + 20, y0 + 38), subtitle, font=font_title, fill=INK_NAVY)
                draw.text((x0 + 20, y0 + 68), eq, font=font_eq, fill=TEXT_MUTED)
                draw.line([(x0 + 20, y0 + 95), (x1 - 20, y0 + 95)], fill=BORDER_MIST, width=1)
                
                # Scientific Vector Illustration inside card
                ill_x = x0 + card_w // 2
                ill_y = y0 + 160
                
                if d_type == "airfoil":
                    # Streamline Airfoil
                    pts = []
                    for k in range(30):
                        xi = (k / 29.0) * 160 - 80
                        # NACA camber shape approximation
                        theta = (k / 29.0) * math.pi
                        yi = -math.sin(theta) * 22.0
                        pts.append((ill_x + xi, ill_y + yi))
                    for k in reversed(range(30)):
                        xi = (k / 29.0) * 160 - 80
                        theta = (k / 29.0) * math.pi
                        yi = math.sin(theta) * 8.0
                        pts.append((ill_x + xi, ill_y + yi))
                    draw.polygon(pts, fill=PALE_BLUE, outline=ELECTRIC_BLUE)
                    # Airflow vector streamlines
                    for s_off in [-28, -14, 18]:
                        draw.line([(ill_x - 100, ill_y + s_off), (ill_x + 100, ill_y + s_off)], fill=(203, 213, 225), width=1)
                        
                elif d_type == "thermo":
                    # P-V Curve
                    draw.line([(ill_x - 70, ill_y + 40), (ill_x + 70, ill_y + 40)], fill=BORDER_MIST, width=1) # V axis
                    draw.line([(ill_x - 70, ill_y - 40), (ill_x - 70, ill_y + 40)], fill=BORDER_MIST, width=1) # P axis
                    pts_pv = []
                    for k in range(25):
                        xi = -60 + k * 5
                        yi = 35 - 70 / (1.0 + math.exp(-k * 0.25))
                        pts_pv.append((ill_x + xi, ill_y + yi))
                    draw.line(pts_pv, fill=ELECTRIC_BLUE, width=2)
                    draw.text((ill_x + 40, ill_y - 20), "Adiabatic", font=font_label, fill=TEXT_MUTED)

                elif d_type == "dna":
                    # Double-Helix Chromatin
                    for k in range(12):
                        px = ill_x - 60 + k * 10
                        h1 = math.sin(k * 0.6 + t * 2.0) * 20.0
                        h2 = -h1
                        draw.ellipse([px - 2, ill_y + h1 - 2, px + 2, ill_y + h1 + 2], fill=ELECTRIC_BLUE)
                        draw.ellipse([px - 2, ill_y + h2 - 2, px + 2, ill_y + h2 + 2], fill=INK_NAVY)
                        draw.line([(px, ill_y + h1), (px, ill_y + h2)], fill=BORDER_MIST, width=1)

                elif d_type == "molecule":
                    # Hexagonal Benzene Ring & Functional Group
                    hex_rad = 28
                    hex_pts = []
                    for k in range(6):
                        ang = k * (math.pi / 3.0) + math.pi / 6.0
                        hx = ill_x + math.cos(ang) * hex_rad
                        hy = ill_y + math.sin(ang) * hex_rad
                        hex_pts.append((hx, hy))
                    draw.polygon(hex_pts, outline=INK_NAVY, fill=WHITE)
                    draw.line([(hex_pts[0][0], hex_pts[0][1]), (hex_pts[0][0] + 25, hex_pts[0][1] - 15)], fill=ELECTRIC_BLUE, width=2)
                    draw.text((hex_pts[0][0] + 30, hex_pts[0][1] - 22), "OH", font=font_label, fill=ELECTRIC_BLUE)

                elif d_type == "robotics":
                    # Kinematic 2-Link Robotic Arm
                    base = (ill_x - 50, ill_y + 25)
                    joint1 = (ill_x - 10, ill_y - 20)
                    tool = (ill_x + 45, ill_y + 5)
                    draw.line([base, joint1], fill=INK_NAVY, width=3)
                    draw.line([joint1, tool], fill=ELECTRIC_BLUE, width=3)
                    draw.ellipse([base[0]-4, base[1]-4, base[0]+4, base[1]+4], fill=TEXT_MUTED)
                    draw.ellipse([joint1[0]-4, joint1[1]-4, joint1[0]+4, joint1[1]+4], fill=ELECTRIC_BLUE)
                    draw.ellipse([tool[0]-5, tool[1]-5, tool[0]+5, tool[1]+5], fill=INK_NAVY)

                elif d_type == "manifold":
                    # Coordinate Tensor Grid
                    for r in range(-3, 4):
                        draw.line([(ill_x - 60, ill_y + r * 10), (ill_x + 60, ill_y + r * 10)], fill=(226, 232, 240), width=1)
                        draw.line([(ill_x + r * 18, ill_y - 30), (ill_x + r * 18, ill_y + 30)], fill=(226, 232, 240), width=1)
                    draw.ellipse([ill_x - 30, ill_y - 15, ill_x + 30, ill_y + 15], outline=ELECTRIC_BLUE, width=2)

                elif d_type == "truss":
                    # Structural FEA Truss Grid
                    nodes = [
                        (ill_x - 60, ill_y + 25), (ill_x, ill_y + 25), (ill_x + 60, ill_y + 25),
                        (ill_x - 30, ill_y - 20), (ill_x + 30, ill_y - 20)
                    ]
                    bars = [(0, 1), (1, 2), (3, 4), (0, 3), (1, 3), (1, 4), (2, 4)]
                    for n1, n2 in bars:
                        draw.line([nodes[n1], nodes[n2]], fill=BORDER_MIST if n1 != 3 else ELECTRIC_BLUE, width=2)
                    for n in nodes:
                        draw.ellipse([n[0]-3, n[1]-3, n[0]+3, n[1]+3], fill=INK_NAVY)

        # Editorial Typography Overlays
        # Phrase 1: "Questions cross disciplines." (10s - 30s)
        alpha1 = get_fade_alpha(t, 10.0, 12.0, 28.0, 30.0)
        if alpha1 > 0:
            col1 = blend_color(BG_WARM_WHITE, INK_NAVY, alpha1)
            draw_text_centered(draw, "Questions cross disciplines.", 45, WIDTH, font_head, fill=col1)
            
        # Phrase 2: "Research should, too." (35s - 55s)
        alpha2 = get_fade_alpha(t, 35.0, 37.0, 53.0, 55.0)
        if alpha2 > 0:
            col2 = blend_color(BG_WARM_WHITE, INK_NAVY, alpha2)
            draw_text_centered(draw, "Research should, too.", 45, WIDTH, font_head, fill=col2)

        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 05 rendered successfully.")

if __name__ == "__main__":
    render_scene05()
