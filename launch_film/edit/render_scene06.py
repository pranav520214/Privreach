"""Render Scene 06: THE LAUNCH / END CARD (04:30 - 05:00 | 30.0s = 720 Frames @ 24 fps)"""

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

TOTAL_FRAMES = 720
FPS = 24
WIDTH = 1920
HEIGHT = 1080

def render_scene06():
    out_dir = r"E:\PrivreachOS\launch_film\scenes\06_end_card"
    out_mp4 = os.path.join(out_dir, "scene06.mp4")
    print(f"[*] Rendering Scene 06: The Launch (720 frames) -> {out_mp4}...")
    
    # Load official logo
    logo_path = r"E:\PrivreachOS\launch_film\assets\brand\logo.png"
    logo_img = Image.open(logo_path).convert("RGBA")
    
    writer = create_video_writer(out_mp4, WIDTH, HEIGHT, FPS)
    
    font_brand = get_font(64, "bold")
    font_concept = get_font(28, "bold")
    font_sub = get_font(22, "regular")
    font_pill = get_font(16, "bold")
    font_label = get_font(13, "bold")
    font_url = get_font(18, "mono")

    cx, cy = WIDTH // 2, HEIGHT // 2

    for f_idx in range(TOTAL_FRAMES):
        t = f_idx / FPS
        
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_WARM_WHITE)
        draw = ImageDraw.Draw(img)
        
        # Grid settles into faint whisper
        grid_alpha = max(1.0 - t / 12.0, 0.4)
        draw_grid(draw, WIDTH, HEIGHT, step=80, alpha_factor=grid_alpha)

        # Subtle collapsing convergence lines in first 6 seconds
        if t < 6.0:
            c_prog = t / 6.0
            for ox, oy in [(-300, -200), (300, -200), (-300, 200), (300, 200)]:
                sp = (cx + ox, cy + oy)
                ep = (int(sp[0] + (cx - sp[0]) * c_prog), int(sp[1] + (cy - sp[1]) * c_prog))
                draw.line([sp, ep], fill=(226, 232, 240), width=1)

        # Central Master Brand Card Fade-In (peaks at t >= 7.0s)
        card_alpha = min(max((t - 2.5) / 4.0, 0.0), 1.0)
        
        card_w = 780
        card_h = 620
        bx0 = cx - card_w // 2
        by0 = cy - card_h // 2 - 10
        bx1 = bx0 + card_w
        by1 = by0 + card_h
        
        if card_alpha > 0.05:
            # Card Container
            c_fill = blend_color(BG_WARM_WHITE, WHITE, card_alpha)
            draw_card(draw, (bx0, by0, bx1, by1), fill=c_fill, radius=20, shadow=True)
            
            # 1. Official Logo Emblem
            logo_size = 140
            scaled_logo = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            lx = cx - logo_size // 2
            ly = by0 + 45
            
            logo_mask = scaled_logo.split()[3]
            if card_alpha < 0.99:
                logo_mask = Image.eval(logo_mask, lambda a: int(a * card_alpha))
            img.paste(scaled_logo, (lx, ly), logo_mask)
            
            # 2. PRIVREACH Wordmark
            c_navy = blend_color(BG_WARM_WHITE, INK_NAVY, card_alpha)
            draw_text_centered(draw, "PRIVREACH", ly + logo_size + 24, WIDTH, font_brand, fill=c_navy)
            
            # 3. RESEARCH, CONNECTED. (Campaign Concept)
            c_blue = blend_color(BG_WARM_WHITE, ELECTRIC_BLUE, card_alpha)
            draw_text_centered(draw, "RESEARCH, CONNECTED.", ly + logo_size + 105, WIDTH, font_concept, fill=c_blue)
            
            # 4. Supporting Brand Line
            c_sub = blend_color(BG_WARM_WHITE, TEXT_MUTED, card_alpha)
            draw_text_centered(draw, "Your Private Research Operating Environment.", ly + logo_size + 152, WIDTH, font_sub, fill=c_sub)
            
            # Thin divider
            draw.line([(cx - 160, ly + logo_size + 195), (cx + 160, ly + logo_size + 195)], fill=BORDER_MIST, width=1)
            
            # 5. Call To Action & Official GitHub Link
            pill_y0 = ly + logo_size + 225
            pill_y1 = pill_y0 + 55
            pill_w = 460
            px0 = cx - pill_w // 2
            px1 = cx + pill_w // 2
            
            # GitHub Badge Pill
            draw.rounded_rectangle([px0, pill_y0, px1, pill_y1], radius=28, fill=PALE_BLUE, outline=ELECTRIC_BLUE, width=1)
            draw.text((cx - 175, pill_y0 + 10), "Explore the project on GitHub:", font=font_label, fill=TEXT_MUTED)
            draw.text((cx - 175, pill_y0 + 26), "github.com/pranav520214/Privreach", font=font_url, fill=ELECTRIC_BLUE)

        # Frame holds in clean stillness from t=22.0s to 30.0s (04:52 - 05:00)

        writer.stdin.write(img.tobytes())

    writer.stdin.close()
    writer.wait()
    print("[OK] Scene 06 rendered successfully.")

if __name__ == "__main__":
    render_scene06()
