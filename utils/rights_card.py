"""
utils/rights_card.py — Emergency Rights Card Generator

Generates a printable A5 PDF card of the user's rights.
Designed to be shown to a police officer or landlord.

Usage:
    from utils.rights_card import generate_rights_card
    pdf_bytes = generate_rights_card(response_dict, language="en")
    with open("rights_card.pdf", "wb") as f:
        f.write(pdf_bytes)

Or from command line to test:
    python utils/rights_card.py
"""

import io
from datetime import date
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ── Colour palette (matches the React UI) ────────────────────────────────────
TERRACOTTA   = colors.HexColor("#C1440E")
BROWN        = colors.HexColor("#2C1A0E")
CREAM        = colors.HexColor("#FAF7F2")
CREAM_DARK   = colors.HexColor("#F0EBE1")
BLUE_ACCENT  = colors.HexColor("#1A5BA6")
WHITE        = colors.white
LIGHT_GREY   = colors.HexColor("#E5D5C5")
FOREST       = colors.HexColor("#2D4A28")


# ── Styles ────────────────────────────────────────────────────────────────────

def make_styles():
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=WHITE,
            leading=28,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#F0EBE1"),
            leading=14,
            spaceAfter=0,
        ),
        "domain_label": ParagraphStyle(
            "domain_label",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=TERRACOTTA,
            leading=12,
            spaceAfter=0,
        ),
        "right_title": ParagraphStyle(
            "right_title",
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=BROWN,
            leading=15,
            spaceAfter=3,
        ),
        "right_plain": ParagraphStyle(
            "right_plain",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#5C3D2E"),
            leading=13,
            spaceAfter=2,
        ),
        "citation": ParagraphStyle(
            "citation",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=BLUE_ACCENT,
            leading=11,
            spaceAfter=0,
        ),
        "section_header": ParagraphStyle(
            "section_header",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=WHITE,
            leading=14,
            spaceAfter=0,
        ),
        "footer_main": ParagraphStyle(
            "footer_main",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#5C3D2E"),
            leading=11,
            spaceAfter=0,
        ),
        "footer_helpline": ParagraphStyle(
            "footer_helpline",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=TERRACOTTA,
            leading=18,
            spaceAfter=0,
        ),
        "action_text": ParagraphStyle(
            "action_text",
            fontName="Helvetica",
            fontSize=9,
            textColor=BROWN,
            leading=13,
            spaceAfter=0,
        ),
    }


# ── Header ────────────────────────────────────────────────────────────────────

def build_header(styles, domain: str, language: str) -> list:
    TITLE_TEXT = {
        "en": "YOUR RIGHTS",
        "hi": "आपके अधिकार",
        "kn": "ನಿಮ್ಮ ಹಕ್ಕುಗಳು",
        "ta": "உங்கள் உரிமைகள்",
        "te": "మీ హక్కులు",
    }
    SUBTITLE_TEXT = {
        "en": "This card states your legal rights under Indian law.",
        "hi": "यह कार्ड भारतीय कानून के तहत आपके अधिकार बताता है।",
        "kn": "ಈ ಕಾರ್ಡ್ ಭಾರತೀಯ ಕಾನೂನಿನ ಅಡಿಯಲ್ಲಿ ನಿಮ್ಮ ಕಾನೂನು ಹಕ್ಕುಗಳನ್ನು ತಿಳಿಸುತ್ತದೆ.",
        "ta": "இந்த அட்டை இந்திய சட்டத்தின் கீழ் உங்கள் சட்ட உரிமைகளை கூறுகிறது.",
        "te": "ఈ కార్డ్ భారతీయ చట్టం ప్రకారం మీ చట్టపరమైన హక్కులను తెలియజేస్తుంది.",
    }

    domain_display = domain.replace("_", " ").upper()
    title = TITLE_TEXT.get(language, TITLE_TEXT["en"])
    subtitle = SUBTITLE_TEXT.get(language, SUBTITLE_TEXT["en"])

    header_data = [[
        Paragraph("⚖ ADHIKAR", styles["subtitle"]),
        Paragraph(domain_display, styles["domain_label"]),
    ]]
    header_table = Table(header_data, colWidths=["70%", "30%"])
    header_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), BROWN),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))

    title_table = Table([[Paragraph(title, styles["title"])]], colWidths=["100%"])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BROWN),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))

    subtitle_table = Table([[Paragraph(subtitle, styles["subtitle"])]], colWidths=["100%"])
    subtitle_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BROWN),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))

    return [header_table, title_table, subtitle_table]


# ── Rights section ────────────────────────────────────────────────────────────

def build_rights_section(styles, rights: list, language: str) -> list:
    SECTION_TITLE = {
        "en": "YOUR RIGHTS",
        "hi": "आपके अधिकार",
        "kn": "ನಿಮ್ಮ ಹಕ್ಕುಗಳು",
        "ta": "உங்கள் உரிமைகள்",
        "te": "మీ హక్కులు",
    }
    section_title = SECTION_TITLE.get(language, "YOUR RIGHTS")
    elements = []

    header_table = Table(
        [[Paragraph(f"  {section_title}", styles["section_header"])]],
        colWidths=["100%"]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE_ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4))

    for i, right in enumerate(rights[:4]):
        num_style = ParagraphStyle(
            "num",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=WHITE,
            leading=16,
            alignment=1,
        )
        number_table = Table(
            [[Paragraph(f"<b>{i+1}</b>", num_style)]],
            colWidths=[7*mm], rowHeights=[7*mm]
        )
        number_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BLUE_ACCENT),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))

        right_content = [
            Paragraph(right.get("right", ""), styles["right_title"]),
            Paragraph(right.get("plain_language", ""), styles["right_plain"]),
            Paragraph(
                f"{right.get('source_act', '')} · {right.get('source_section', '')}",
                styles["citation"]
            ),
        ]

        right_row = Table([[number_table, right_content]], colWidths=[10*mm, None])
        right_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, 0), 12),
            ("RIGHTPADDING", (0, 0), (0, 0), 6),
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(right_row)

        if i < len(rights) - 1 and i < 3:
            elements.append(HRFlowable(
                width="100%", thickness=0.5,
                color=LIGHT_GREY, spaceAfter=0, spaceBefore=0
            ))

    return elements


# ── Actions section ───────────────────────────────────────────────────────────

def build_actions_section(styles, actions: list, language: str) -> list:
    SECTION_TITLE = {
        "en": "DO THIS NOW",
        "hi": "अभी यह करें",
        "kn": "ಈಗ ಇದನ್ನು ಮಾಡಿ",
        "ta": "இப்போது இதைச் செய்யுங்கள்",
        "te": "ఇప్పుడు ఇది చేయండి",
    }
    section_title = SECTION_TITLE.get(language, "DO THIS NOW")
    elements = [Spacer(1, 8)]

    header_table = Table(
        [[Paragraph(f"  {section_title}", styles["section_header"])]],
        colWidths=["100%"]
    )
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TERRACOTTA),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4))

    for i, action in enumerate(actions[:3]):
        action_text = f"<b>{i+1}.</b> {action.get('action', '')} — {action.get('what_to_do', '')}"
        row = Table(
            [[Paragraph(action_text, styles["action_text"])]],
            colWidths=["100%"]
        )
        row.setStyle(TableStyle([
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4ED")),
        ]))
        elements.append(row)

        if i < len(actions) - 1 and i < 2:
            elements.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#FED7AA"),
                spaceAfter=0, spaceBefore=0
            ))

    return elements


# ── Footer ────────────────────────────────────────────────────────────────────

def build_footer(styles, language: str) -> list:
    DISCLAIMER = {
        "en": "This is legal information, not legal advice.",
        "hi": "यह कानूनी जानकारी है, कानूनी सलाह नहीं।",
        "kn": "ಇದು ಕಾನೂನು ಮಾಹಿತಿ, ಕಾನೂನು ಸಲಹೆಯಲ್ಲ.",
        "ta": "இது சட்ட தகவல், சட்ட ஆலோசனை அல்ல.",
        "te": "ఇది చట్టపరమైన సమాచారం, న్యాయ సలహా కాదు.",
    }
    HELPLINE_LABEL = {
        "en": "Free Legal Aid Helpline",
        "hi": "मुफ्त कानूनी सहायता हेल्पलाइन",
        "kn": "ಉಚಿತ ಕಾನೂನು ಸಹಾಯ ಹೆಲ್ಪ್‌ಲೈನ್",
        "ta": "இலவச சட்ட உதவி ஹெல்ப்லைன்",
        "te": "ఉచిత న్యాయ సహాయ హెల్ప్‌లైన్",
    }

    today = date.today().strftime("%d %B %Y")
    disclaimer = DISCLAIMER.get(language, DISCLAIMER["en"])
    helpline_label = HELPLINE_LABEL.get(language, HELPLINE_LABEL["en"])

    elements = [Spacer(1, 10)]

    footer_data = [
        [
            Paragraph(f"adhikar  ·  {today}", styles["footer_main"]),
            Paragraph(helpline_label, styles["footer_main"]),
        ],
        [
            Paragraph(disclaimer, styles["footer_main"]),
            Paragraph("NALSA  15100", styles["footer_helpline"]),
        ],
    ]

    footer_table = Table(footer_data, colWidths=["55%", "45%"])
    footer_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM_DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEABOVE", (0, 0), (-1, 0), 1, LIGHT_GREY),
    ]))
    elements.append(footer_table)

    return elements


# ── Main generator ────────────────────────────────────────────────────────────

def generate_rights_card(response: dict, language: str = "en") -> bytes:
    """
    Generate an A5 PDF rights card from a ResponseSchema dict.

    Args:
        response: dict with rights[], actions[], domain, disclaimer
        language: language code (en/hi/kn/ta/te)

    Returns:
        PDF as bytes
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A5,
        leftMargin=0,
        rightMargin=0,
        topMargin=0,
        bottomMargin=0,
    )

    styles = make_styles()
    story = []

    domain = response.get("domain", "legal")
    rights = response.get("rights", [])
    actions = response.get("actions", [])

    story += build_header(styles, domain, language)
    story += build_rights_section(styles, rights, language)
    story += build_actions_section(styles, actions, language)
    story += build_footer(styles, language)

    doc.build(story)
    return buffer.getvalue()


# ── Test ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = {
        "domain": "police_fir",
        "rights": [
            {
                "right": "Right to know grounds of arrest",
                "source_act": "Code of Criminal Procedure, 1973",
                "source_section": "Section 50",
                "plain_language": "Police must tell you exactly why they are arresting you."
            },
            {
                "right": "Right to life and personal liberty",
                "source_act": "Constitution of India",
                "source_section": "Article 21",
                "plain_language": "You cannot be arrested without following fair legal procedure."
            },
            {
                "right": "Custodial rights — arrest memo and family notification",
                "source_act": "D.K. Basu Guidelines",
                "source_section": "Supreme Court 1997",
                "plain_language": "Police must prepare an arrest memo and let you inform your family."
            },
            {
                "right": "Protection against warrantless arrest",
                "source_act": "Code of Criminal Procedure, 1973",
                "source_section": "Section 41",
                "plain_language": "Police must have written reasons before arresting you without a warrant."
            },
        ],
        "actions": [
            {
                "action": "Ask for the reason for arrest",
                "what_to_do": "Calmly ask the officer to state and write down why you are being arrested.",
                "priority": 1,
                "requires_lawyer": False
            },
            {
                "action": "Inform a family member",
                "what_to_do": "Insist on your right to call a family member and tell them your location.",
                "priority": 2,
                "requires_lawyer": False
            },
            {
                "action": "Contact a lawyer",
                "what_to_do": "Call NALSA at 15100 for free legal aid if you cannot afford a lawyer.",
                "priority": 3,
                "requires_lawyer": True
            },
        ],
        "disclaimer": "This is legal information, not legal advice."
    }

    pdf = generate_rights_card(sample, language="en")
    with open("rights_card_test.pdf", "wb") as f:
        f.write(pdf)
    print(f"✓ Generated rights_card_test.pdf ({len(pdf):,} bytes)")
    print("Open the file to check the output.")
