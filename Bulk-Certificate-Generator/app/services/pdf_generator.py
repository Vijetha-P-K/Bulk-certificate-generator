"""Renders a single certificate PDF."""
import json
import math
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.config import OUTPUT_DIR

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "certificate_template.json"
BASE_DIR = Path(__file__).resolve().parent.parent.parent

_template_cache = None
_signature_font_name = None
_signature_font_tried = False


class CertificateGenerationError(Exception):
    pass


def get_template() -> dict:
    global _template_cache
    if _template_cache is None:
        with TEMPLATE_PATH.open("r", encoding="utf-8") as fh:
            _template_cache = json.load(fh)
    return _template_cache


def _safe_filename(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    return safe or "recipient"


def _resolve_image(path_str: str):
    if not path_str:
        return None
    p = Path(path_str)
    if not p.is_absolute():
        p = BASE_DIR / p
    return p if p.is_file() else None


def _get_signature_font() -> str:
    global _signature_font_name, _signature_font_tried
    if _signature_font_tried:
        return _signature_font_name
    _signature_font_tried = True
    candidates = [
        "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
        "/System/Library/Fonts/Supplemental/SnellRoundhand.ttc",
        "/System/Library/Fonts/Supplemental/SnellRoundhand-BlackScript.otf",
        "/System/Library/Fonts/Supplemental/SignPainter.ttc",
        "/Library/Fonts/Bradley Hand Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        r"C:\Windows\Fonts\ITCKRIST.TTF",
        r"C:\Windows\Fonts\segoesc.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            try:
                pdfmetrics.registerFont(TTFont("SignatureFont", path))
                _signature_font_name = "SignatureFont"
                return _signature_font_name
            except Exception:
                continue
    _signature_font_name = "Times-Italic"
    return _signature_font_name


def _wrap_text(c, text, font, size, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _draw_star(c, cx, cy, size, color, points=5):
    c.setFillColor(color)
    angle = -math.pi / 2
    outer_r = size
    inner_r = size * 0.42
    p = c.beginPath()
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
        angle += math.pi / points
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _lighten(hex_color: str, amount: float = 0.35) -> colors.Color:
    c = colors.HexColor(hex_color)
    r = c.red + (1 - c.red) * amount
    g = c.green + (1 - c.green) * amount
    b = c.blue + (1 - c.blue) * amount
    return colors.Color(r, g, b)


def _darken(hex_color: str, amount: float = 0.35) -> colors.Color:
    c = colors.HexColor(hex_color)
    r = c.red * (1 - amount)
    g = c.green * (1 - amount)
    b = c.blue * (1 - amount)
    return colors.Color(r, g, b)


# ---------------------------------------------------------------------------
# Badge color levels
# ---------------------------------------------------------------------------
BADGE_LEVELS = {
    "bronze":   {"outer": "#B87333", "ring": "#7A3E1A", "inner": "#F5DCC4",
                 "ribbon": "#1F3B73", "star": "#B87333", "shadow": "#5C2D12"},
    "silver":   {"outer": "#BFC5CC", "ring": "#5A6470", "inner": "#EEF1F4",
                 "ribbon": "#1F3B73", "star": "#8A939D", "shadow": "#3A414A"},
    "gold":     {"outer": "#E5B80B", "ring": "#8A6A00", "inner": "#FBF3C8",
                 "ribbon": "#1F3B73", "star": "#E5B80B", "shadow": "#6B5400"},
    "platinum": {"outer": "#8FA4B8", "ring": "#3E4E5F", "inner": "#E8EEF4",
                 "ribbon": "#1F3B73", "star": "#8FA4B8", "shadow": "#27323D"},
}


def _draw_badge(c, cx, cy, radius, level="gold"):
    """
    Realistic metallic medal with radial gradient, scalloped edge,
    beveled rings, 3D star and folded navy ribbon tails.
    """
    pal = BADGE_LEVELS.get(str(level).lower(), BADGE_LEVELS["gold"])
    outer_hex = pal["outer"]
    outer = colors.HexColor(outer_hex)
    outer_light = _lighten(outer_hex, 0.55)
    outer_mid = _lighten(outer_hex, 0.15)
    outer_dark = _darken(outer_hex, 0.32)
    outer_deep = _darken(outer_hex, 0.55)

    ring = colors.HexColor(pal["ring"])
    inner = colors.HexColor(pal["inner"])
    inner_shade = _darken(pal["inner"], 0.10)

    ribbon = colors.HexColor(pal["ribbon"])
    ribbon_dark = _darken(pal["ribbon"], 0.35)
    ribbon_light = _lighten(pal["ribbon"], 0.20)

    star_c = colors.HexColor(pal["star"])
    star_light = _lighten(pal["star"], 0.55)
    shadow = colors.HexColor(pal["shadow"])

    # ===== 1. Ribbon tails (behind the medal) =====
    for side in (-1, 1):
        # main strip
        c.setFillColor(ribbon)
        p = c.beginPath()
        p.moveTo(cx + side * radius * 0.42, cy - radius * 0.55)
        p.lineTo(cx + side * radius * 0.28, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.02, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.02, cy - radius * 0.70)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # darker edge on outer side
        c.setFillColor(ribbon_dark)
        p = c.beginPath()
        p.moveTo(cx + side * radius * 0.42, cy - radius * 0.55)
        p.lineTo(cx + side * radius * 0.28, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.22, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.32, cy - radius * 0.68)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # folded V notch at the bottom
        c.setFillColor(ribbon_dark)
        p = c.beginPath()
        p.moveTo(cx + side * radius * 0.28, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.02, cy - radius * 2.10)
        p.lineTo(cx + side * radius * 0.15, cy - radius * 1.85)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

        # highlight strip
        c.setFillColor(ribbon_light)
        p = c.beginPath()
        p.moveTo(cx + side * radius * 0.05, cy - radius * 0.70)
        p.lineTo(cx + side * radius * 0.06, cy - radius * 2.05)
        p.lineTo(cx + side * radius * 0.02, cy - radius * 2.05)
        p.lineTo(cx + side * radius * 0.02, cy - radius * 0.70)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    # ===== 2. Outer scalloped rim =====
    n_pleats = 48
    base_r = radius * 0.94

    c.setFillColor(outer_dark)
    c.circle(cx, cy, base_r, fill=1, stroke=0)

    for i in range(n_pleats):
        ang = (2 * math.pi / n_pleats) * i
        dx = cx + math.cos(ang) * base_r
        dy = cy + math.sin(ang) * base_r
        shade_factor = (math.sin(ang - math.pi / 4) + 1) / 2
        r_c = outer_light.red * shade_factor + outer_dark.red * (1 - shade_factor)
        g_c = outer_light.green * shade_factor + outer_dark.green * (1 - shade_factor)
        b_c = outer_light.blue * shade_factor + outer_dark.blue * (1 - shade_factor)
        c.setFillColor(colors.Color(r_c, g_c, b_c))
        c.circle(dx, dy, radius * 0.085, fill=1, stroke=0)

    # ===== 3. Main disc with radial shading (wedge gradient) =====
    n_wedges = 60
    for i in range(n_wedges):
        a0 = (2 * math.pi / n_wedges) * i - math.pi / 2
        a1 = (2 * math.pi / n_wedges) * (i + 1) - math.pi / 2
        mid = (a0 + a1) / 2
        lum = (math.cos(mid + math.pi * 0.75) + 1) / 2
        r_c = outer_deep.red * (1 - lum) + outer_light.red * lum
        g_c = outer_deep.green * (1 - lum) + outer_light.green * lum
        b_c = outer_deep.blue * (1 - lum) + outer_light.blue * lum
        c.setFillColor(colors.Color(r_c, g_c, b_c))
        p = c.beginPath()
        p.moveTo(cx, cy)
        p.lineTo(cx + math.cos(a0) * radius * 0.82, cy + math.sin(a0) * radius * 0.82)
        p.lineTo(cx + math.cos(a1) * radius * 0.82, cy + math.sin(a1) * radius * 0.82)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    # ===== 4. Beveled inner ring =====
    c.setStrokeColor(shadow)
    c.setLineWidth(1.6)
    c.circle(cx, cy, radius * 0.80, fill=0, stroke=1)

    c.setStrokeColor(outer_light)
    c.setLineWidth(0.6)
    c.circle(cx, cy, radius * 0.77, fill=0, stroke=1)

    # ===== 5. Cream face with highlight =====
    c.setFillColor(inner)
    c.circle(cx, cy, radius * 0.72, fill=1, stroke=0)

    c.setFillColor(colors.Color(1, 1, 1, alpha=0.35))
    c.circle(cx - radius * 0.18, cy + radius * 0.18, radius * 0.42, fill=1, stroke=0)

    c.setStrokeColor(inner_shade)
    c.setLineWidth(0.7)
    c.circle(cx, cy, radius * 0.68, fill=0, stroke=1)

    # ===== 6. Dotted ring =====
    for i in range(32):
        ang = (2 * math.pi / 32) * i
        dx = cx + math.cos(ang) * radius * 0.58
        dy = cy + math.sin(ang) * radius * 0.58
        c.setFillColor(ring)
        c.circle(dx, dy, 0.85, fill=1, stroke=0)

    # ===== 7. 3D Star =====
    _draw_star(c, cx + radius * 0.02, cy - radius * 0.03, radius * 0.44, shadow)
    _draw_star(c, cx, cy, radius * 0.44, _darken(pal["star"], 0.20))
    _draw_star(c, cx, cy + radius * 0.015, radius * 0.36, star_c)
    _draw_star(c, cx - radius * 0.02, cy + radius * 0.05, radius * 0.20, star_light)

    # glossy spot
    c.setFillColor(colors.Color(1, 1, 1, alpha=0.55))
    c.circle(cx - radius * 0.13, cy + radius * 0.20, radius * 0.06, fill=1, stroke=0)


def _draw_shield_logo(c, cx, cy, size, navy, gold):
    w = size * 1.6
    h = size * 2.0
    top = cy + h / 2
    bottom = cy - h / 2
    left = cx - w / 2
    right = cx + w / 2
    shoulder = cy + h * 0.12

    p = c.beginPath()
    p.moveTo(left, top)
    p.lineTo(right, top)
    p.lineTo(right, shoulder)
    p.lineTo(cx, bottom)
    p.lineTo(left, shoulder)
    p.close()
    c.setFillColor(navy)
    c.drawPath(p, fill=1, stroke=0)

    inset = 3
    p2 = c.beginPath()
    p2.moveTo(left + inset, top - inset)
    p2.lineTo(right - inset, top - inset)
    p2.lineTo(right - inset, shoulder)
    p2.lineTo(cx, bottom + inset)
    p2.lineTo(left + inset, shoulder)
    p2.close()
    c.setStrokeColor(gold)
    c.setLineWidth(1.4)
    c.drawPath(p2, fill=0, stroke=1)

    c.setFillColor(colors.white)
    c.setFont("Times-Bold", size * 0.95)
    c.drawCentredString(cx, cy - size * 0.20, "RIO")

    _draw_star(c, cx, cy + h * 0.28, size * 0.16, gold)


def _draw_shaded_corner(c, x, y, size, color, corner):
    c.setFillColor(color)
    p = c.beginPath()
    if corner == "tl":
        p.moveTo(x, y); p.lineTo(x + size, y); p.lineTo(x, y - size)
    elif corner == "tr":
        p.moveTo(x, y); p.lineTo(x - size, y); p.lineTo(x, y - size)
    elif corner == "bl":
        p.moveTo(x, y); p.lineTo(x + size, y); p.lineTo(x, y + size)
    else:
        p.moveTo(x, y); p.lineTo(x - size, y); p.lineTo(x, y + size)
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_border(c, width, height, navy, gold):
    c.setStrokeColor(navy)
    c.setLineWidth(2)
    c.rect(16, 16, width - 32, height - 32)

    c.setStrokeColor(gold)
    c.setLineWidth(0.8)
    c.rect(24, 24, width - 48, height - 48)

    c.setStrokeColor(navy)
    c.setLineWidth(1)
    c.rect(30, 30, width - 60, height - 60)

    for (x, y) in [(16, 16), (width - 16, 16), (16, height - 16), (width - 16, height - 16)]:
        c.setFillColor(gold)
        d = 7
        p = c.beginPath()
        p.moveTo(x, y + d)
        p.lineTo(x + d, y)
        p.lineTo(x, y - d)
        p.lineTo(x - d, y)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    navy_shade = colors.Color(navy.red, navy.green, navy.blue, alpha=0.85)
    _draw_shaded_corner(c, 30, height - 30, 95, navy_shade, "tl")
    _draw_shaded_corner(c, width - 30, height - 30, 95, navy_shade, "tr")
    _draw_shaded_corner(c, 30, 30, 95, navy_shade, "bl")
    _draw_shaded_corner(c, width - 30, 30, 95, navy_shade, "br")


def _draw_signature(c, cx, base_y, sig_path, name, title, navy, muted):
    font = _get_signature_font()
    line_half = 95

    if sig_path:
        try:
            img = ImageReader(str(sig_path))
            iw, ih = img.getSize()
            target_h = 26
            target_w = target_h * (iw / ih)
            if target_w > line_half * 2:
                target_w = line_half * 2
                target_h = target_w * (ih / iw)
            c.drawImage(img, cx - target_w / 2, base_y + 8,
                        width=target_w, height=target_h, mask="auto")
        except Exception:
            pass
    else:
        c.setFillColor(navy)
        c.setFont(font, 22)
        c.drawCentredString(cx, base_y + 12, name)

    c.setStrokeColor(muted)
    c.setLineWidth(0.8)
    c.line(cx - line_half, base_y, cx + line_half, base_y)

    c.setFillColor(navy)
    c.setFont("Times-Bold", 11)
    c.drawCentredString(cx, base_y - 16, name)

    c.setFillColor(muted)
    c.setFont("Times-Roman", 9)
    c.drawCentredString(cx, base_y - 29, title)


def _render_pdf(file_path: Path, recipient_name, event_name, event_date):
    template = get_template()
    palette_hex = template["colors"]
    level = template.get("badge_level", "gold")

    navy = colors.HexColor(palette_hex["primary"])
    gold = colors.HexColor(palette_hex["accent"])
    text_color = colors.HexColor(palette_hex["text"])
    muted = colors.HexColor(palette_hex["muted"])

    page = landscape(A4)
    width, height = page

    c = canvas.Canvas(str(file_path), pagesize=page)
    c.setTitle(f"{template['title']} - {recipient_name}")
    c.setAuthor(template.get("org_name", "Bulk Certificate Generator"))
    c.setSubject(event_name)

    # --- Border ---
    _draw_border(c, width, height, navy, gold)

    # --- Institution name + logo on the same row ---
    org_name = template.get("org_name", "")
    org_y = height - 78
    if org_name:
        spaced = "  ".join(org_name.upper())
        c.setFont("Times-Bold", 20)
        name_w = c.stringWidth(spaced, "Times-Bold", 20)
        name_left = (width - name_w) / 2

        logo = _resolve_image(template.get("logo_path", ""))
        logo_cx = name_left - 45
        if logo is not None:
            try:
                img = ImageReader(str(logo))
                iw, ih = img.getSize()
                target_h = 46
                target_w = target_h * (iw / ih)
                c.drawImage(img, logo_cx - target_w / 2, org_y - target_h / 2 + 6,
                            width=target_w, height=target_h, mask="auto")
            except Exception:
                _draw_shield_logo(c, logo_cx, org_y + 6, 14, navy, gold)
        else:
            _draw_shield_logo(c, logo_cx, org_y + 6, 14, navy, gold)

        c.setFillColor(navy)
        c.setFont("Times-Bold", 20)
        c.drawCentredString(width / 2, org_y, spaced)

        line_half = min(name_w / 2 + 40, width / 2 - 100)
        c.setStrokeColor(gold)
        c.setLineWidth(1.2)
        c.line(width / 2 - line_half, org_y - 10, width / 2 + line_half, org_y - 10)

        c.setFillColor(gold)
        p = c.beginPath()
        p.moveTo(width / 2, org_y - 6)
        p.lineTo(width / 2 + 4, org_y - 10)
        p.lineTo(width / 2, org_y - 14)
        p.lineTo(width / 2 - 4, org_y - 10)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    # --- Badge RIGHT side ---
    badge_cx = width - 105
    badge_cy = height - 210
    _draw_badge(c, badge_cx, badge_cy, 42, level=level)

    # --- Title ---
    title_y = badge_cy + 12
    c.setFillColor(navy)
    c.setFont("Times-Bold", 30)
    c.drawCentredString(width / 2, title_y, template["title"].upper())

    sub_y = title_y - 38
    c.setFillColor(muted)
    c.setFont("Times-Italic", 13)
    c.drawCentredString(width / 2, sub_y, template["subtitle"])

    # --- Recipient name ---
    name = recipient_name.strip()
    size = 36
    while size > 18 and c.stringWidth(name, "Times-Bold", size) > width - 300:
        size -= 1

    name_y = sub_y - 52
    c.setFillColor(text_color)
    c.setFont("Times-Bold", size)
    c.drawCentredString(width / 2, name_y, name)

    half = min(c.stringWidth(name, "Times-Bold", size) / 2 + 30, width / 2 - 90)
    c.setStrokeColor(gold)
    c.setLineWidth(1)
    c.line(width / 2 - half, name_y - 12, width / 2 + half, name_y - 12)

    role = template.get("recipient_role", "Program Participant")
    role_y = name_y - 28
    c.setFillColor(muted)
    c.setFont("Times-Italic", 11)
    c.drawCentredString(width / 2, role_y, role)

    prefix_y = role_y - 32
    c.setFillColor(muted)
    c.setFont("Times-Roman", 12)
    c.drawCentredString(width / 2, prefix_y, template["body_prefix"])

    c.setFillColor(navy)
    c.setFont("Times-Bold", 19)
    lines = _wrap_text(c, event_name, "Times-Bold", 19, width - 280)
    ev_y = prefix_y - 26
    for line in lines[:2]:
        c.drawCentredString(width / 2, ev_y, line)
        ev_y -= 22

    # --- Date ---
    date_x = 145
    date_y = 82
    c.setFillColor(muted)
    c.setFont("Times-Italic", 10)
    c.drawCentredString(date_x, date_y + 18, "Date of Issue")
    c.setFillColor(navy)
    c.setFont("Times-Bold", 13)
    c.drawCentredString(date_x, date_y - 2, event_date)
    c.setStrokeColor(muted)
    c.setLineWidth(0.6)
    c.line(date_x - 55, date_y - 12, date_x + 55, date_y - 12)

    # --- Signatures ---
    sig_left = _resolve_image(template.get("signature_left_path", ""))
    _draw_signature(
        c, cx=width - 145, base_y=95, sig_path=sig_left,
        name=template.get("footer_left_name", ""),
        title=template.get("footer_left_title", ""),
        navy=navy, muted=muted,
    )

    if template.get("footer_right_name"):
        sig_right = _resolve_image(template.get("signature_right_path", ""))
        _draw_signature(
            c, cx=width / 2, base_y=95, sig_path=sig_right,
            name=template.get("footer_right_name", ""),
            title=template.get("footer_right_title", ""),
            navy=navy, muted=muted,
        )

    c.showPage()
    c.save()


def generate_certificate(*, job_id, certificate_id, recipient_name, event_name, event_date):
    if not recipient_name or not recipient_name.strip():
        raise CertificateGenerationError("Recipient name is empty")

    job_dir = OUTPUT_DIR / f"job_{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)

    filename = f"certificate_{certificate_id}_{_safe_filename(recipient_name)}.pdf"
    file_path = job_dir / filename

    try:
        _render_pdf(file_path, recipient_name, event_name, event_date)
    except Exception as exc:
        raise CertificateGenerationError(f"Failed to render PDF: {exc}") from exc

    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise CertificateGenerationError("Generated PDF is empty or missing")

    return str(file_path)