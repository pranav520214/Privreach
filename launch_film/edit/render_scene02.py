"""Render Scene 02: THE REVEAL (00:30 - 01:10 | 40.0s = 960 Frames @ 24 fps)"""

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

TOTAL_FRAMES = 960
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene02():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\02_reveal"
    out_mp4 = os.path.join(out_dir, "scene02.mp4")
    print(f"[*] Rendering Scene 02: The Reveal (960 frames) -> {out_mp4}...")
    
    # Load official logo
    logo_path = r"E:\PrivreachOS\launch_film\assets\brand\logo.png"
    logo_img = Image.open(logo_path).convert("RGBA")
    
    # Load workstation capture for transition
    workstation_path = r"E:\PrivreachOS\launch_film\assets\product_captures\full_workstation.png"
    ws_img = Image.open(workstation_path).convert("RGB")
    ws_aspect = ws_img.width / ws_img.height
    ws_target_w = 1600
    ws_target_h = int(ws_target_w / ws_aspect)
    ws_img_resized = ws_img.resize((ws_target_w, ws_target_h), Image.Resampling.LANCZOS)
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_intro = get_font(52, "regular")
    font_brand = get_font(54, "bold")
    font_tagline = get_font(22, "regular")
    font_sub = get_font(18, "light")

    cx, cy = WIDTH // 2, HEIGHT // 2

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        draw_grid(draw, WIDTH, HEIGHT, step=80)
        
        # 1. Part A (0s - 16s): Geometric Convergence & Coordinate Alignment
        if t < 18.0:
            conv_prog = min(t / 14.0, 1.0)
            
            # Radiating geometric axes
            axis_len = int(240 * conv_prog)
            draw.line([(cx - axis_len, cy), (cx + axis_len, cy)], fill=(203, 213, 225), width=1)
            draw.line([(cx, cy - axis_len), (cx, cy + axis_len)], fill=(203, 213, 225), width=1)
            
            # Caliper ticks
            for step in range(40, axis_len, 40):
                draw.line([(cx + step, cy - 4), (cx + step, cy + 4)], fill=ELECTRIC_BLUE, width=1)
                draw.line([(cx - step, cy - 4), (cx - step, cy + 4)], fill=ELECTRIC_BLUE, width=1)
                draw.line([(cx - 4, cy + step), (cx + 4, cy + step)], fill=ELECTRIC_BLUE, width=1)
                draw.line([(cx - 4, cy - step), (cx + 4, cy - step)], fill=ELECTRIC_BLUE, width=1)
            
            # Converging polygon frames
            n_sides = 8
            rad = 70 + 30 * (1.0 - conv_prog)
            pts = []
            for i in range(n_sides):
                angle = i * (2 * math.pi / n_sides) + t * 0.1
                px = cx + math.cos(angle) * rad
                py = cy + math.sin(angle) * rad
                pts.append((px, py))
            draw.polygon(pts, outline=(191, 219, 254), width=1)
            
            # Converging lines from 4 corners
            for ox, oy in [(-500, -300), (500, -300), (-500, 300), (500, 300)]:
                start_p = (cx + ox, cy + oy)
                cur_x = int(start_p[0] + (cx - start_p[0]) * conv_prog)
                cur_y = int(start_p[1] + (cy - start_p[1]) * conv_prog)
                draw.line([start_p, (cur_x, cur_y)], fill=(226, 232, 240), width=1)
            
            # Central Electric Blue Anchor
            draw.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=ELECTRIC_BLUE)
            
            # Typography: "Introducing Privreach."
            alpha_intro = get_fade_alpha(t, 2.0, 4.0, 14.5, 16.5)
            if alpha_intro > 0:
                col = blend_color(BG_WARM_WHITE, INK_NAVY, alpha_intro)
                draw_text_centered(draw, "Introducing Privreach.", 320, WIDTH, font_intro, fill=col)

        # 2. Part B (16s - 32s): Logo & Brand Typography Reveal
        if t >= 14.0 and t < 34.0:
            logo_alpha = min((t - 14.0) / 3.0, 1.0)
            if t > 30.0:
                logo_alpha = max(1.0 - (t - 30.0) / 3.0, 0.0)
            
            # Draw Logo Emblem
            logo_size = 140
            scaled_logo = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Alpha compositing logo
            lx = cx - logo_size // 2
            ly = cy - logo_size // 2 - 80
            
            # Card background for logo
            card_box = (cx - 360, cy - 200, cx + 360, cy + 200)
            c_fill = blend_color(BG_WARM_WHITE, WHITE, logo_alpha)
            draw_card(draw, card_box, fill=c_fill, radius=16)
            
            # Paste logo
            if logo_alpha > 0.1:
                logo_mask = scaled_logo.split()[3]
                if logo_alpha < 0.99:
                    logo_mask = Image.eval(logo_mask, lambda a: int(a * logo_alpha))
                img.paste(scaled_logo, (lx, ly), logo_mask)
            
            # Typography: PRIVREACH
            col_brand = blend_color(BG_WARM_WHITE, INK_NAVY, logo_alpha)
            draw_text_centered(draw, "PRIVREACH", ly + logo_size + 24, WIDTH, font_brand, fill=col_brand)
            
            # Supporting Brand Line
            col_tag = blend_color(BG_WARM_WHITE, ELECTRIC_BLUE, logo_alpha)
            draw_text_centered(draw, "Your Private Research Operating Environment.", ly + logo_size + 95, WIDTH, font_tagline, fill=col_tag)

        # 3. Part C (30s - 40s): Forward Glide into Authentic Workstation Interface
        if t >= 30.0:
            ws_prog = min((t - 30.0) / 8.0, 1.0)
            # Smooth scale from 0.85 -> 1.00
            scale = 0.85 + 0.15 * ws_prog
            ws_w = int(ws_target_w * scale)
            ws_h = int(ws_target_h * scale)
            cur_ws = ws_img_resized.resize((ws_w, ws_h), Image.Resampling.LANCZOS)
            
            ws_x = cx - ws_w // 2
            ws_y = cy - ws_h // 2 + int(40 * (1.0 - ws_prog))
            
            # Ambient elevation container
            ws_box = (ws_x - 6, ws_y - 6, ws_x + ws_w + 6, ws_y + ws_h + 6)
            draw_card(draw, ws_box, fill=WHITE, border=BORDER_MIST, radius=12, shadow=True)
            
            img.paste(cur_ws, (ws_x, ws_y))
            
            # Top Window Header Banner
            draw.rectangle([ws_x, ws_y, ws_x + ws_w, ws_y + 32], fill=(241, 245, 249))
            # Mac/Win window control dots
            for i, c_dot in enumerate([(239, 68, 68), (245, 158, 11), (16, 185, 129)]):
                draw.ellipse([ws_x + 16 + i * 16, ws_y + 11, ws_x + 26 + i * 16, ws_y + 21], fill=c_dot)
            draw.text((ws_x + 75, ws_y + 7), "Privreach OS — Native Research Workstation", font=font_sub, fill=INK_NAVY)

        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 02 rendered successfully.")

if __name__ == "__main__":
    render_scene02()
