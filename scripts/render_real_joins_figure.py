import os
from PIL import Image, ImageDraw, ImageFont

def make_real_joins_figure():
    os.makedirs("assets/images", exist_ok=True)

    # Load real photos
    p_join1 = Image.open("assets/real_tablets/P100089.jpg")  # AAS 102 + 205
    p_join2 = Image.open("assets/real_tablets/P131610.jpg")  # Louvre AO 5521 + 5522
    p_join3 = Image.open("assets/real_tablets/P285811.jpg")  # Geneva MAH 16064

    # Target canvas
    canvas_w = 1920
    canvas_h = 1080
    canvas = Image.new("RGB", (canvas_w, canvas_h), color=(15, 23, 42))  # Slate 900
    draw = ImageDraw.Draw(canvas)

    # Title header
    draw.rectangle([(0, 0), (canvas_w, 90)], fill=(30, 41, 59))
    draw.rectangle([(0, 88), (canvas_w, 92)], fill=(245, 158, 11))  # Amber line

    # Text headers
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_subtitle = ImageFont.truetype("arial.ttf", 20)
        font_card_title = ImageFont.truetype("arial.ttf", 22)
        font_card_desc = ImageFont.truetype("arial.ttf", 15)
        font_badge = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_title = font_subtitle = font_card_title = font_card_desc = font_badge = ImageFont.load_default()

    draw.text((40, 16), "NISABA EPIGRAPHIC RECONSTRUCTION ENGINE", fill=(245, 158, 11), font=font_title)
    draw.text((40, 58), "Ground-Truth Cross-Collection Physical & Virtual Joins from CDLI Archival Corpus", fill=(148, 163, 184), font=font_subtitle)

    # 3 Panels for the 3 real joined tablets
    panel_w = 580
    panel_h = 940
    panel_y = 115

    panels_info = [
        {
            "img": p_join1,
            "x": 40,
            "title": "AAS 102 + 205 (CDLI P100089)",
            "subtitle": "Excavation Frags CF 11 + CFC 149",
            "desc": "Physical join of two separate fragments. The upper fragment (CF 11) fits into the lower fragment (CFC 149). Nisaba k-mer alignment detects the fracture boundary across line breaks.",
            "status": "CERTIFIED PHYSICAL JOIN",
            "status_color": (34, 197, 94),
        },
        {
            "img": p_join2,
            "x": 670,
            "title": "Louvre AO 5521 + 5522 (CDLI P131610)",
            "subtitle": "Musée du Louvre, Paris (TCL 02, 5521+)",
            "desc": "Cross-catalog join of two tablets accessioned separately at the Louvre. Clear diagnostic fracture seam bisects obverse and reverse administrative text columns.",
            "status": "CERTIFIED MUSEUM JOIN",
            "status_color": (56, 189, 248),
        },
        {
            "img": p_join3,
            "x": 1300,
            "title": "MAH 16064 (CDLI P285811)",
            "subtitle": "Musée d'Art et d'Histoire, Geneva",
            "desc": "Long-distance virtual join candidate with British Museum BM 78942 (Atrahasis Epic Tablet III). Discovered by epigraphists, aligned computationally across 1,000 km distance.",
            "status": "VIRTUAL LONG-DISTANCE JOIN",
            "status_color": (168, 85, 247),
        }
    ]

    for p in panels_info:
        # Card background
        draw.rounded_rectangle([(p["x"], panel_y), (p["x"] + panel_w, panel_y + panel_h)], radius=12, fill=(30, 41, 59), outline=(51, 65, 85), width=2)

        # Badge
        badge_w = 230
        draw.rounded_rectangle([(p["x"] + 20, panel_y + 16), (p["x"] + 20 + badge_w, panel_y + 42)], radius=6, fill=(15, 23, 42), outline=p["status_color"], width=1)
        draw.text((p["x"] + 28, panel_y + 22), p["status"], fill=p["status_color"], font=font_badge)

        # Title & Subtitle
        draw.text((p["x"] + 20, panel_y + 54), p["title"], fill=(241, 245, 249), font=font_card_title)
        draw.text((p["x"] + 20, panel_y + 84), p["subtitle"], fill=(148, 163, 184), font=font_card_desc)

        # Image thumbnail
        im = p["img"].convert("RGB")
        # Scale to fit box 540 x 700 preserving aspect
        box_w, box_h = 540, 680
        im.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)
        img_x = p["x"] + 20 + (box_w - im.width) // 2
        img_y = panel_y + 115 + (box_h - im.height) // 2
        canvas.paste(im, (img_x, img_y))

        # Description text below image
        desc_lines = []
        words = p["desc"].split()
        cur_line = []
        for w in words:
            if len(" ".join(cur_line + [w])) > 58:
                desc_lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            desc_lines.append(" ".join(cur_line))

        for idx, dl in enumerate(desc_lines[:3]):
            draw.text((p["x"] + 20, panel_y + 815 + (idx * 22)), dl, fill=(203, 213, 225), font=font_card_desc)

    out_path = "assets/images/real_tablet_joins_showcase.png"
    canvas.save(out_path, quality=95)
    print(f"Generated {out_path} ({os.path.getsize(out_path):,} bytes)")

if __name__ == "__main__":
    make_real_joins_figure()
