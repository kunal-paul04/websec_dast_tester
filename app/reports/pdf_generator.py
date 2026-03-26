"""
pdf_generator.py
================
Generates a styled PDF security report using ReportLab's Platypus engine.
Design mirrors the Bootstrap report.html — dark header, color-coded test
cards, stat boxes, tables, and a footer on every page.
"""

import os
import io
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.flowables import HRFlowable


# ─────────────────────────────────────────────
#  COLOR PALETTE  (mirrors the Bootstrap theme)
# ─────────────────────────────────────────────
C_NAVY       = colors.HexColor("#1e3a5f")   # navbar / header bg
C_BLUE       = colors.HexColor("#2563eb")   # header gradient end
C_ACCENT     = colors.HexColor("#38bdf8")   # highlight / links
C_GREEN      = colors.HexColor("#198754")   # PASS
C_RED        = colors.HexColor("#dc3545")   # FAIL
C_ORANGE     = colors.HexColor("#fd7e14")   # SKIPPED
C_AMBER      = colors.HexColor("#fbbf24")   # warning text
C_LIGHT_BG   = colors.HexColor("#f0f2f5")   # page background
C_CARD_BG    = colors.HexColor("#ffffff")
C_STAT_BG    = colors.HexColor("#f8f9fa")
C_BORDER     = colors.HexColor("#e9ecef")
C_TEXT       = colors.HexColor("#1e293b")
C_MUTED      = colors.HexColor("#6c757d")
C_WHITE      = colors.white

STATUS_COLOR = {"PASS": C_GREEN, "FAIL": C_RED, "SKIPPED": C_ORANGE}
STATUS_BG    = {
    "PASS":    colors.HexColor("#f0fff4"),
    "FAIL":    colors.HexColor("#fff0f0"),
    "SKIPPED": colors.HexColor("#fff8ec"),
}

TEST_ICONS = {
    "CORS":             "CORS",
    "HEADER_SECURITY":  "HEADERS",
    "SQL_INJECTION":    "SQLi",
    "LOAD_TEST":        "LOAD",
}


# ─────────────────────────────────────────────
#  STYLE FACTORY
# ─────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        # Report title on cover header
        "report_title": S("ReportTitle",
            fontName="Helvetica-Bold", fontSize=22,
            textColor=C_WHITE, leading=28, spaceAfter=4),

        "report_sub": S("ReportSub",
            fontName="Helvetica", fontSize=10,
            textColor=colors.HexColor("#93c5fd"), leading=14),

        "url_label": S("UrlLabel",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=colors.HexColor("#93c5fd"),
            spaceAfter=2),

        "url_value": S("UrlValue",
            fontName="Helvetica", fontSize=9,
            textColor=C_WHITE, leading=13),

        # Section label (small caps above content)
        "section_label": S("SectionLabel",
            fontName="Helvetica-Bold", fontSize=7,
            textColor=C_MUTED, leading=10,
            spaceBefore=10, spaceAfter=4),

        # Test card heading
        "test_name": S("TestName",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=C_TEXT, leading=14),

        "test_badge": S("TestBadge",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_WHITE, alignment=TA_CENTER),

        # Body text inside cards
        "body": S("Body",
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT, leading=14, spaceAfter=3),

        "body_muted": S("BodyMuted",
            fontName="Helvetica", fontSize=8,
            textColor=C_MUTED, leading=12),

        # Bullet item
        "bullet": S("Bullet",
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT, leading=13,
            leftIndent=12, spaceAfter=2),

        "bullet_red": S("BulletRed",
            fontName="Helvetica", fontSize=9,
            textColor=C_RED, leading=13,
            leftIndent=12, spaceAfter=2),

        "bullet_green": S("BulletGreen",
            fontName="Helvetica", fontSize=9,
            textColor=C_GREEN, leading=13,
            leftIndent=12, spaceAfter=2),

        # Stat box value
        "stat_value": S("StatValue",
            fontName="Helvetica-Bold", fontSize=18,
            textColor=C_BLUE, leading=22, alignment=TA_CENTER),

        "stat_label": S("StatLabel",
            fontName="Helvetica", fontSize=7,
            textColor=C_MUTED, leading=10, alignment=TA_CENTER),

        # Table header cell
        "th": S("TH",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_MUTED, leading=10),

        "td": S("TD",
            fontName="Helvetica", fontSize=8,
            textColor=C_TEXT, leading=11),

        "td_mono": S("TDMono",
            fontName="Courier", fontSize=7.5,
            textColor=C_TEXT, leading=11),

        "td_green": S("TDGreen",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_GREEN, leading=11),

        "td_red": S("TDRed",
            fontName="Helvetica-Bold", fontSize=8,
            textColor=C_RED, leading=11),

        # Footer
        "footer": S("Footer",
            fontName="Helvetica", fontSize=7.5,
            textColor=C_MUTED, alignment=TA_CENTER),
    }


# ─────────────────────────────────────────────
#  PAGE TEMPLATE  (header stripe + footer)
# ─────────────────────────────────────────────
def _make_page_decorator(url, scan_date):
    """Returns an onPage callback that draws the top navbar stripe and footer."""
    def decorate(canvas, doc):
        W, H = A4
        canvas.saveState()

        # ── Top navbar stripe ──
        canvas.setFillColor(C_NAVY)
        canvas.rect(0, H - 28, W, 28, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(C_WHITE)
        canvas.drawString(1.5*cm, H - 19, "WebSec Tester")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#93c5fd"))
        canvas.drawRightString(W - 1.5*cm, H - 19, f"Page {doc.page}")

        # ── Bottom footer ──
        canvas.setFillColor(C_BORDER)
        canvas.rect(0, 0, W, 22, fill=1, stroke=0)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(1.5*cm, 7, f"Target: {url}")
        canvas.drawRightString(W - 1.5*cm, 7, f"Generated: {scan_date}  |  WebSec Tester")

        canvas.restoreState()

    return decorate


# ─────────────────────────────────────────────
#  HELPER BUILDERS
# ─────────────────────────────────────────────
def _hr(color=C_BORDER, thickness=0.5):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6, spaceBefore=2)


def _status_badge(status, ST):
    """Small colored pill showing PASS / FAIL / SKIPPED."""
    color = STATUS_COLOR.get(status, C_MUTED)
    label = {"PASS": "PASS", "FAIL": "FAIL", "SKIPPED": "SKIPPED"}.get(status, status)
    badge = Table(
        [[Paragraph(f"  {label}  ", ST["test_badge"])]],
        colWidths=[2*cm]
    )
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), color),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [color]),
    ]))
    return badge


def _card_header(test_name, status, ST):
    """
    Colored header row for each test card.
    Left border color = status color, background = light tint.
    """
    s_color = STATUS_COLOR.get(status, C_MUTED)
    s_bg    = STATUS_BG.get(status, colors.HexColor("#f8f9fa"))
    icon    = TEST_ICONS.get(test_name, test_name)
    label   = test_name.replace("_", " ").title()

    left_col  = Paragraph(f"<b>{icon} &nbsp; {label}</b>", ST["test_name"])
    right_col = _status_badge(status, ST)

    t = Table([[left_col, right_col]], colWidths=[13*cm, 3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), s_bg),
        ("LEFTPADDING",   (0,0), (0,-1), 10),
        ("RIGHTPADDING",  (-1,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",         (-1,0),(-1,-1), "RIGHT"),
        ("LINEBEFORE",    (0,0), (0,-1), 4, s_color),
    ]))
    return t


def _stat_row(stats, ST):
    """
    Horizontal row of stat boxes: [(label, value, color), ...]
    """
    cells = []
    for label, value, color in stats:
        val_style = ParagraphStyle("sv", fontName="Helvetica-Bold",
                                   fontSize=16, textColor=color,
                                   leading=20, alignment=TA_CENTER)
        lbl_style = ParagraphStyle("sl", fontName="Helvetica", fontSize=7,
                                   textColor=C_MUTED, leading=10, alignment=TA_CENTER)
        inner = Table(
            [[Paragraph(str(value), val_style)],
             [Paragraph(label, lbl_style)]],
            colWidths=[3.5*cm]
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), C_STAT_BG),
            ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
            ("TOPPADDING",    (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ]))
        cells.append(inner)

    n = len(cells)
    t = Table([cells], colWidths=[3.8*cm] * n)
    t.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0), (-1,-1), 4),
        ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))
    return t


def _kv_table(rows, ST):
    """Two-column key/value table with alternating row backgrounds."""
    data = [[Paragraph("Header", ST["th"]), Paragraph("Value", ST["th"])]]
    for k, v in rows:
        data.append([
            Paragraph(str(k), ST["td"]),
            Paragraph(str(v) if v else "Not Set", ST["td_mono"]),
        ])
    t = Table(data, colWidths=[5.5*cm, 10.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_STAT_BG),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [C_WHITE, C_STAT_BG]),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.25, C_BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  8),
        ("TEXTCOLOR",     (0,0), (-1,0),  C_MUTED),
    ]))
    return t


def _bullet_list(items, ST, style_key="bullet_red", prefix="x "):
    """Returns a list of Paragraph flowables for a bullet list."""
    out = []
    for item in items:
        out.append(Paragraph(f"{prefix}{item}", ST[style_key]))
    return out


# ─────────────────────────────────────────────
#  COVER HEADER BLOCK
# ─────────────────────────────────────────────
def _cover_header(url, scan_date, results, ST):
    """Big gradient-style header table at the top of page 1."""

    # Counts
    total   = len(results)
    passed  = sum(1 for r in results if r.get("status") == "PASS")
    failed  = sum(1 for r in results if r.get("status") == "FAIL")
    skipped = sum(1 for r in results if r.get("status") == "SKIPPED")

    # Left: title + URL
    title_block = [
        [Paragraph("Security Scan Report", ST["report_title"])],
        [Paragraph("WebSec Tester — Automated Security Analysis", ST["report_sub"])],
        [Spacer(1, 8)],
        [Paragraph("TARGET URL", ST["url_label"])],
        [Paragraph(url, ST["url_value"])],
        [Spacer(1, 4)],
        [Paragraph(f"Scan Date: {scan_date}", ST["url_label"])],
    ]
    left = Table(title_block, colWidths=[11*cm])
    left.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0), (-1,-1), 2),
    ]))

    # Right: summary counts
    def count_cell(value, label, color):
        vs = ParagraphStyle("cv", fontName="Helvetica-Bold", fontSize=22,
                            textColor=color, leading=26, alignment=TA_CENTER)
        ls = ParagraphStyle("cl", fontName="Helvetica", fontSize=7.5,
                            textColor=colors.HexColor("#bfdbfe"),
                            leading=10, alignment=TA_CENTER)
        t = Table([[Paragraph(str(value), vs)], [Paragraph(label, ls)]],
                  colWidths=[2.2*cm])
        t.setStyle(TableStyle([
            ("TOPPADDING",   (0,0),(-1,-1), 2),
            ("BOTTOMPADDING",(0,0),(-1,-1), 2),
        ]))
        return t

    right_cells = [
        count_cell(total,   "TOTAL",   C_WHITE),
        count_cell(passed,  "PASSED",  colors.HexColor("#4ade80")),
        count_cell(failed,  "FAILED",  colors.HexColor("#f87171")),
        count_cell(skipped, "SKIPPED", colors.HexColor("#fbbf24")),
    ]
    right = Table([right_cells], colWidths=[2.4*cm]*4)
    right.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("VALIGN",       (0,0),(-1,-1), "MIDDLE"),
    ]))

    # Outer wrapper
    outer = Table([[left, right]], colWidths=[11*cm, 9.6*cm])
    outer.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_NAVY),
        ("TOPPADDING",    (0,0), (-1,-1), 20),
        ("BOTTOMPADDING", (0,0), (-1,-1), 20),
        ("LEFTPADDING",   (0,0), (0,-1),  20),
        ("RIGHTPADDING",  (-1,0),(-1,-1), 16),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        # Blue bottom accent line
        ("LINEBELOW",     (0,0), (-1,-1), 3, C_ACCENT),
    ]))
    return outer


# ─────────────────────────────────────────────
#  PER-TEST CARD BUILDERS
# ─────────────────────────────────────────────
def _build_cors(r, ST):
    items = []
    if r.get("issues"):
        items.append(Paragraph("Issues Found", ST["section_label"]))
        items += _bullet_list(r["issues"], ST, "bullet_red", "x  ")

    if r.get("details"):
        items.append(Spacer(1, 6))
        items.append(Paragraph("Response Headers", ST["section_label"]))
        items.append(_kv_table(r["details"].items(), ST))
    return items


def _build_headers(r, ST):
    items = []
    if r.get("missing_headers"):
        items.append(Paragraph("Missing Security Headers", ST["section_label"]))
        items += _bullet_list(r["missing_headers"], ST, "bullet_red", "x  ")

    if r.get("present_headers"):
        items.append(Spacer(1, 6))
        items.append(Paragraph("Present Headers", ST["section_label"]))
        rows = [(k, v) for k, v in r["present_headers"].items()]
        items.append(_kv_table(rows, ST))
    return items


def _build_sqli(r, ST):
    items = []
    if r.get("findings"):
        items.append(Paragraph("Findings", ST["section_label"]))
        items += _bullet_list(r["findings"], ST, "bullet_red", "x  ")
    else:
        items.append(Paragraph(
            "No SQL Injection vulnerabilities detected.", ST["bullet_green"]))

    if r.get("details"):
        items.append(Spacer(1, 6))
        items.append(Paragraph("Debug Details", ST["section_label"]))
        items += _bullet_list(r["details"], ST, "bullet", "-  ")
    return items


def _build_load(r, ST):
    items = []

    stats = [
        ("Total Requests",   r.get("total_requests",      "-"), C_BLUE),
        ("Successful",       r.get("successful_requests", "-"), C_GREEN),
        ("Failed",           r.get("failed_requests",     "-"), C_RED),
        ("Avg Latency (s)",  r.get("avg_latency",         "-"), colors.HexColor("#f59e0b")),
    ]
    items.append(_stat_row(stats, ST))

    if r.get("graph"):
        img_path = "app" + r["graph"]
        if os.path.exists(img_path):
            items.append(Spacer(1, 10))
            items.append(Paragraph("Latency Graph", ST["section_label"]))
            items.append(Image(img_path, width=14*cm, height=7*cm))
    return items


# ─────────────────────────────────────────────
#  MAIN ENTRY POINT
# ─────────────────────────────────────────────
def generate_pdf_report(results, url, filename="websec_scan_analysis_report.pdf"):
    """
    Generate a styled PDF report.

    Args:
        results  : list of test result dicts
        url      : scanned URL string
        filename : output filename (saved inside app/static/)

    Returns:
        str: URL path to the PDF e.g. "/static/websec_scan_analysis_report.pdf"
    """
    path      = f"app/static/{filename}"
    scan_date = datetime.now().strftime("%Y-%m-%d  %H:%M:%S UTC")
    ST        = _styles()
    decorator = _make_page_decorator(url, scan_date)

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.5*cm,
        rightMargin=1.5*cm,
        topMargin=1.8*cm,      # room for navbar stripe
        bottomMargin=1.5*cm,   # room for footer
        title=f"WebSec Report — {url}",
        author="WebSec Tester",
    )

    story = []

    # ── 1. Cover header ──────────────────────────────────────
    story.append(_cover_header(url, scan_date, results, ST))
    story.append(Spacer(1, 0.6*cm))

    # ── 2. Test result cards ─────────────────────────────────
    BUILDERS = {
        "CORS":            _build_cors,
        "HEADER_SECURITY": _build_headers,
        "SQL_INJECTION":   _build_sqli,
        "LOAD_TEST":       _build_load,
    }

    for r in results:
        test_name = r.get("test", "UNKNOWN")
        status    = r.get("status", "SKIPPED")

        card_items = []

        # Card header bar
        card_items.append(_card_header(test_name, status, ST))

        # Inner padding wrapper
        inner_items = []

        # Error alert
        if r.get("error"):
            err_t = Table(
                [[Paragraph(f"Error: {r['error']}", ST["bullet_red"])]],
                colWidths=[14.5*cm]
            )
            err_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#fff0f0")),
                ("BOX",           (0,0),(-1,-1), 0.5, C_RED),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(-1,-1), 6),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ]))
            inner_items.append(err_t)
            inner_items.append(Spacer(1, 6))

        # Test-specific content
        builder = BUILDERS.get(test_name)
        if builder:
            inner_items += builder(r, ST)
        else:
            inner_items.append(
                Paragraph("No detailed data available for this test.", ST["body_muted"]))

        # Wrap inner content in a white padded table
        if inner_items:
            rows = [[item] for item in inner_items]
            body_t = Table(rows, colWidths=[14.5*cm])
            body_t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0), (-1,-1), C_WHITE),
                ("LEFTPADDING",   (0,0), (-1,-1), 10),
                ("RIGHTPADDING",  (0,0), (-1,-1), 10),
                ("TOPPADDING",    (0,0), (0,0),   10),
                ("BOTTOMPADDING", (0,-1),(-1,-1), 12),
                ("TOPPADDING",    (0,1), (-1,-1), 2),
                ("BOTTOMPADDING", (0,0), (-1,-2), 2),
            ]))
            card_items.append(body_t)

        # Outer card border
        card_rows = [[item] for item in card_items]
        card_t = Table(card_rows, colWidths=[16*cm])
        card_t.setStyle(TableStyle([
            ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [C_WHITE]),
        ]))

        story.append(KeepTogether(card_t))
        story.append(Spacer(1, 0.5*cm))

    # ── 3. Footer note ───────────────────────────────────────
    story.append(_hr(C_BORDER, 0.5))
    story.append(Paragraph(
        "This report was generated automatically by WebSec Tester. "
        "For authorized security testing only. Results are indicative — "
        "always validate findings manually.",
        ST["footer"]
    ))

    # Build with page decorator
    doc.build(story, onFirstPage=decorator, onLaterPages=decorator)

    return f"/static/{filename}"
