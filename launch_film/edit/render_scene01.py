"""Render Scene 01: THE FRAGMENTATION (00:00 - 00:30 | 720 Frames @ 24 fps)"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw
from render_utils import (
    BG_WARM_WHITE, WHITE, INK_NAVY, ELECTRIC_BLUE, BORDER_MIST,
    TEXT_MUTED, TEXT_SUBTLE, SOFT_SLATE, PALE_BLUE,
    get_font, draw_grid, draw_card, draw_text_centered,
    get_fade_alpha, blend_color, create_video_writer
)

TOTAL_FRAMES = 720
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene01():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\01_fragmentation"
    out_mp4 = os.path.join(out_dir, "scene01.mp4")
    print(f"[*] Rendering Scene 01: The Fragmentation (720 frames) -> {out_mp4}...")
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_head = get_font(48, "regular")
    font_sub = get_font(20, "light")
    font_math = get_font(22, "bold")
    font_label = get_font(13, "bold")
    font_code = get_font(13, "mono")
    font_body = get_font(14, "regular")

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        # Base canvas
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        
        # Stately camera pull-back
        # Scale decreases from 1.05 to 1.00
        pullback = 1.05 - 0.05 * (t / 30.0)
        
        # Microscopic architectural grid
        draw_grid(draw, WIDTH, HEIGHT, step=80)
        
        # Floating Disconnected Artifacts
        # Slight drift physics before t=25s, then micro-alignment at t >= 25s
        align_factor = min(max((t - 25.0) / 4.0, 0.0), 1.0)
        
        # 1. Card A: Mathematical Equation Fragment (Top Left)
        ca_drift_x = math.sin(t * 0.4) * 12.0 * (1.0 - align_factor)
        ca_drift_y = math.cos(t * 0.3) * 8.0 * (1.0 - align_factor)
        ca_box = (
            int(180 + ca_drift_x),
            int(160 + ca_drift_y),
            int(540 + ca_drift_x),
            int(360 + ca_drift_y)
        )
        draw_card(draw, ca_box, radius=10)
        draw.text((ca_box[0] + 20, ca_box[1] + 18), "GOVERNING AERODYNAMICS", font=font_label, fill=TEXT_MUTED)
        draw.text((ca_box[0] + 20, ca_box[1] + 46), "C_L = 2·L / (ρ·v²·S)", font=font_math, fill=INK_NAVY)
        draw.text((ca_box[0] + 20, ca_box[1] + 95), "• Lift Force: L = 12,500 N", font=font_code, fill=TEXT_MUTED)
        draw.text((ca_box[0] + 20, ca_box[1] + 122), "• Density: ρ = 1.225 kg/m³", font=font_code, fill=TEXT_MUTED)
        draw.text((ca_box[0] + 20, ca_box[1] + 149), "• Velocity: v = 68.0 m/s", font=font_code, fill=TEXT_MUTED)
        
        # 2. Card B: Academic Paper Fragment (Top Right)
        cb_drift_x = -math.sin(t * 0.35) * 10.0 * (1.0 - align_factor)
        cb_drift_y = math.sin(t * 0.45) * 9.0 * (1.0 - align_factor)
        cb_box = (
            int(1360 + cb_drift_x),
            int(140 + cb_drift_y),
            int(1760 + cb_drift_x),
            int(380 + cb_drift_y)
        )
        draw_card(draw, cb_box, radius=10)
        draw.text((cb_box[0] + 20, cb_box[1] + 18), "DOCUMENT CITATION [p. 1]", font=font_label, fill=ELECTRIC_BLUE)
        draw.text((cb_box[0] + 20, cb_box[1] + 46), "NACA 64-416 Airfoil Study", font=font_math, fill=INK_NAVY)
        draw.text((cb_box[0] + 20, cb_box[1] + 85), "Abstract: Subsonic cruise efficiency", font=font_body, fill=TEXT_MUTED)
        draw.text((cb_box[0] + 20, cb_box[1] + 110), "demands boundary layer control...", font=font_body, fill=TEXT_MUTED)
        draw.rectangle([cb_box[0] + 20, cb_box[1] + 145, cb_box[0] + 260, cb_box[1] + 147], fill=BORDER_MIST)
        draw.rectangle([cb_box[0] + 20, cb_box[1] + 160, cb_box[0] + 210, cb_box[1] + 162], fill=BORDER_MIST)
        
        # 3. Card C: Experimental Tabular Telemetry (Bottom Left)
        cc_drift_x = math.cos(t * 0.3) * 14.0 * (1.0 - align_factor)
        cc_drift_y = -math.sin(t * 0.25) * 8.0 * (1.0 - align_factor)
        cc_box = (
            int(160 + cc_drift_x),
            int(680 + cc_drift_y),
            int(580 + cc_drift_x),
            int(920 + cc_drift_y)
        )
        draw_card(draw, cc_box, radius=10)
        draw.text((cc_box[0] + 20, cc_box[1] + 18), "ISOLATED DATASET // RUN_409", font=font_label, fill=TEXT_MUTED)
        draw.text((cc_box[0] + 20, cc_box[1] + 48), "AoA     Mach    Re        Cl", font=font_code, fill=INK_NAVY)
        draw.text((cc_box[0] + 20, cc_box[1] + 75), "0.0°    0.78    6.5e6     0.280", font=font_code, fill=TEXT_MUTED)
        draw.text((cc_box[0] + 20, cc_box[1] + 102), "4.5°    0.78    6.5e6     0.542", font=font_code, fill=TEXT_MUTED)
        draw.text((cc_box[0] + 20, cc_box[1] + 129), "14.2°   0.78    6.5e6     1.045 [Stall]", font=font_code, fill=TEXT_MUTED)
        
        # 4. Card D: Disconnected Knowledge Graph (Bottom Right)
        cd_drift_x = -math.cos(t * 0.4) * 12.0 * (1.0 - align_factor)
        cd_drift_y = -math.cos(t * 0.35) * 10.0 * (1.0 - align_factor)
        cd_box = (
            int(1320 + cd_drift_x),
            int(660 + cd_drift_y),
            int(1740 + cd_drift_x),
            int(920 + cd_drift_y)
        )
        draw_card(draw, cd_box, radius=10)
        draw.text((cd_box[0] + 20, cd_box[1] + 18), "UNLINKED TOPOLOGY", font=font_label, fill=TEXT_MUTED)
        
        # Disconnected Nodes
        nodes = [(cd_box[0] + 60, cd_box[1] + 90), (cd_box[0] + 180, cd_box[1] + 65), (cd_box[0] + 120, cd_box[1] + 160), (cd_box[0] + 290, cd_box[1] + 130)]
        for nx, ny in nodes:
            draw.ellipse([nx - 8, ny - 8, nx + 8, ny + 8], fill=WHITE, outline=ELECTRIC_BLUE, width=2)
            draw.text((nx + 12, ny - 6), "Entity", font=font_code, fill=INK_NAVY)
        # Broken edges
        draw.line([nodes[0], (nodes[0][0] + 45, nodes[0][1] - 8)], fill=BORDER_MIST, width=2)
        draw.line([nodes[1], (nodes[1][0] - 20, nodes[1][1] + 35)], fill=BORDER_MIST, width=2)
        
        # 5. Incomplete Connection Tendril Lines (Gaps)
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        # Lines reaching from each card towards center, but stopping short
        gap_prog = 0.55 + 0.35 * align_factor # closes gap when blue point activates
        
        # Line from Card A towards center
        p_a = (ca_box[2], ca_box[3] - 40)
        p_a_end = (int(p_a[0] + (center_x - p_a[0]) * gap_prog), int(p_a[1] + (center_y - p_a[1]) * gap_prog))
        draw.line([p_a, p_a_end], fill=BORDER_MIST if align_factor < 0.5 else ELECTRIC_BLUE, width=1)
        draw.ellipse([p_a_end[0]-3, p_a_end[1]-3, p_a_end[0]+3, p_a_end[1]+3], fill=ELECTRIC_BLUE if align_factor > 0.5 else BORDER_MIST)
        
        # Line from Card B towards center
        p_b = (cb_box[0], cb_box[3] - 40)
        p_b_end = (int(p_b[0] + (center_x - p_b[0]) * gap_prog), int(p_b[1] + (center_y - p_b[1]) * gap_prog))
        draw.line([p_b, p_b_end], fill=BORDER_MIST if align_factor < 0.5 else ELECTRIC_BLUE, width=1)
        draw.ellipse([p_b_end[0]-3, p_b_end[1]-3, p_b_end[0]+3, p_b_end[1]+3], fill=ELECTRIC_BLUE if align_factor > 0.5 else BORDER_MIST)
        
        # Line from Card C towards center
        p_c = (cc_box[2], cc_box[1] + 50)
        p_c_end = (int(p_c[0] + (center_x - p_c[0]) * gap_prog), int(p_c[1] + (center_y - p_c[1]) * gap_prog))
        draw.line([p_c, p_c_end], fill=BORDER_MIST if align_factor < 0.5 else ELECTRIC_BLUE, width=1)
        draw.ellipse([p_c_end[0]-3, p_c_end[1]-3, p_c_end[0]+3, p_c_end[1]+3], fill=ELECTRIC_BLUE if align_factor > 0.5 else BORDER_MIST)
        
        # Line from Card D towards center
        p_d = (cd_box[0], cd_box[1] + 50)
        p_d_end = (int(p_d[0] + (center_x - p_d[0]) * gap_prog), int(p_d[1] + (center_y - p_d[1]) * gap_prog))
        draw.line([p_d, p_d_end], fill=BORDER_MIST if align_factor < 0.5 else ELECTRIC_BLUE, width=1)
        draw.ellipse([p_d_end[0]-3, p_d_end[1]-3, p_d_end[0]+3, p_d_end[1]+3], fill=ELECTRIC_BLUE if align_factor > 0.5 else BORDER_MIST)

        # 6. Center Blue Point Reveal (At t >= 25.0s)
        if t >= 25.0:
            pt_t = t - 25.0
            pt_alpha = min(pt_t / 1.5, 1.0)
            pt_radius = int(5 + 2 * math.sin(pt_t * 6.0))
            # Glowing rings
            for r_ring in [24, 48, 72]:
                ring_rad = int(r_ring * (pt_t * 0.8))
                if ring_rad > 0 and ring_rad < 140:
                    draw.ellipse([center_x - ring_rad, center_y - ring_rad, center_x + ring_rad, center_y + ring_rad], outline=(191, 219, 254), width=1)
            draw.ellipse([center_x - pt_radius, center_y - pt_radius, center_x + pt_radius, center_y + pt_radius], fill=ELECTRIC_BLUE)

        # 7. Editorial Typography Overlays
        # Phrase 1: "Knowledge is everywhere." (04s - 12s)
        alpha1 = get_fade_alpha(t, 4.0, 5.5, 10.5, 12.0)
        if alpha1 > 0:
            col1 = blend_color(BG_WARM_WHITE, INK_NAVY, alpha1)
            draw_text_centered(draw, "Knowledge is everywhere.", 480, WIDTH, font_head, fill=col1)
            
        # Phrase 2: "Context is not." (15s - 24s)
        alpha2 = get_fade_alpha(t, 15.0, 16.5, 22.5, 24.0)
        if alpha2 > 0:
            col2 = blend_color(BG_WARM_WHITE, INK_NAVY, alpha2)
            draw_text_centered(draw, "Context is not.", 480, WIDTH, font_head, fill=col2)

        # Write frame to pipe
        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 01 rendered successfully.")

if __name__ == "__main__":
    render_scene01()
