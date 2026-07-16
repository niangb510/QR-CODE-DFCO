#!/usr/bin/env python3
"""
Génère des tickets de tombola imprimables avec QR codes uniques.
DFCO - Golden Coast
"""

import os
import uuid
import sqlite3
import qrcode
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.lib.utils import ImageReader

# Configuration
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TICKETS_DIR = os.path.join(OUTPUT_DIR, "tickets")
DB_FILE = os.path.join(OUTPUT_DIR, "tombola.db")

# URL de participation (à adapter selon l'hébergement)
BASE_URL = "http://localhost:5000"

# Couleurs DFCO
DFCO_RED = colors.HexColor("#B40000")
DFCO_BLACK = colors.HexColor("#000000")
DFCO_GOLD = colors.HexColor("#D4AF37")

# Polices utilisées pour les tickets
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def register_fonts():
    """Enregistre les polices Unicode compatibles et met à jour les noms de polices."""
    global FONT_REGULAR, FONT_BOLD

    font_paths = [
        ('ArialUnicode', '/System/Library/Fonts/Supplemental/Arial.ttf'),
        ('ArialUnicode', '/Library/Fonts/Arial.ttf'),
        ('ArialUnicode', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
    ]
    bold_font_paths = [
        ('ArialUnicode-Bold', '/System/Library/Fonts/Supplemental/Arial Bold.ttf'),
        ('ArialUnicode-Bold', '/Library/Fonts/Arial Bold.ttf'),
        ('ArialUnicode-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
    ]

    for name, path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
            FONT_REGULAR = name
            break

    for name, path in bold_font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
            FONT_BOLD = name
            break


def generate_qr_code(ticket_id: str, base_url: str, size: int = 300) -> str:
    """Génère un QR code PNG pour un ticket donné."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    participation_url = f"{base_url}/?ticket={ticket_id}"
    qr.add_data(participation_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#B40000", back_color="white").convert('RGB')
    img_path = os.path.join(TICKETS_DIR, f"qr_{ticket_id}.png")
    img.save(img_path)
    return img_path


def draw_ticket(c: canvas.Canvas, ticket_id: str, qr_path: str, x: float, y: float, width: float, height: float):
    """Dessine un ticket sur le canevas PDF."""
    # Fond
    c.setFillColor(colors.white)
    c.rect(x, y, width, height, fill=1, stroke=1)

    # Bandeau supérieur
    c.setFillColor(DFCO_RED)
    c.rect(x, y + height - 1.2 * cm, width, 1.2 * cm, fill=1, stroke=0)

    # Titre
    c.setFillColor(colors.white)
    c.setFont(FONT_BOLD, 14)
    c.drawCentredString(x + width / 2, y + height - 0.85 * cm, "TOMBOLA DFCO - GOLDEN COAST")

    # Sous-titre
    c.setFillColor(DFCO_BLACK)
    c.setFont(FONT_REGULAR, 10)
    c.drawCentredString(x + width / 2, y + height - 1.8 * cm, "Scanne le QR code pour participer et gagner des lots du club")

    # QR code
    qr_size = 4.5 * cm
    qr_x = x + (width - qr_size) / 2
    qr_y = y + height - 6.8 * cm
    c.drawImage(ImageReader(qr_path), qr_x, qr_y, width=qr_size, height=qr_size)

    # Numéro de ticket
    c.setFillColor(DFCO_RED)
    c.setFont(FONT_BOLD, 12)
    c.drawCentredString(x + width / 2, y + height - 7.5 * cm, f"N° {ticket_id}")

    # Instructions
    c.setFillColor(DFCO_BLACK)
    c.setFont(FONT_REGULAR, 8)
    instructions = [
        "1. Scanne le QR code avec ton smartphone",
        "2. Saisis ton email sur le formulaire",
        "3. Valide ta participation au tirage au sort"
    ]
    for i, line in enumerate(instructions):
        c.drawCentredString(x + width / 2, y + height - 8.2 * cm - i * 0.4 * cm, line)

    # Footer
    c.setFillColor(DFCO_GOLD)
    c.setFont(FONT_REGULAR, 8)
    c.drawCentredString(x + width / 2, y + 0.4 * cm, "Collecte d'emails reservee a la base supporters DFCO")


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                used INTEGER DEFAULT 0,
                email TEXT,
                name TEXT,
                rgpd_consent INTEGER DEFAULT 0,
                created_at TEXT,
                registered_at TEXT
            )
        """)


def save_tickets_to_db(tickets):
    with sqlite3.connect(DB_FILE) as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO tickets (ticket_id, used, created_at) VALUES (?, 0, ?)",
            [(t["ticket_id"], date.today().isoformat()) for t in tickets]
        )


def generate_tickets(count: int = 100, base_url: str = BASE_URL):
    """Génère un fichier PDF avec les tickets et sauvegarde les données en SQLite."""
    os.makedirs(TICKETS_DIR, exist_ok=True)
    register_fonts()
    init_db()

    tickets_data = []
    pdf_path = os.path.join(OUTPUT_DIR, "tickets_tombola.pdf")
    c = canvas.Canvas(pdf_path, pagesize=A4)
    page_width, page_height = A4

    # Dimensions des tickets : 2 colonnes x 3 lignes par page A4
    ticket_width = 8.5 * cm
    ticket_height = 9.5 * cm
    margin_x = 1.5 * cm
    margin_y = 1.5 * cm
    gap_x = 1 * cm
    gap_y = 1 * cm

    positions = [
        (margin_x, page_height - margin_y - ticket_height),
        (margin_x + ticket_width + gap_x, page_height - margin_y - ticket_height),
        (margin_x, page_height - margin_y - 2 * ticket_height - gap_y),
        (margin_x + ticket_width + gap_x, page_height - margin_y - 2 * ticket_height - gap_y),
        (margin_x, page_height - margin_y - 3 * ticket_height - 2 * gap_y),
        (margin_x + ticket_width + gap_x, page_height - margin_y - 3 * ticket_height - 2 * gap_y),
    ]

    for i in range(count):
        ticket_id = str(uuid.uuid4())[:8].upper()
        qr_path = generate_qr_code(ticket_id, base_url)
        tickets_data.append({
            "ticket_id": ticket_id,
            "used": False,
            "participant_email": None,
            "participant_name": None
        })

        pos_idx = i % 6
        x, y = positions[pos_idx]
        draw_ticket(c, ticket_id, qr_path, x, y, ticket_width, ticket_height)

        if pos_idx == 5 and i != count - 1:
            c.showPage()

    c.save()
    save_tickets_to_db(tickets_data)

    print(f"✅ {count} tickets générés")
    print(f"📄 PDF : {pdf_path}")
    print(f"💾 Base de données : {DB_FILE}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Génère des tickets de tombola DFCO")
    parser.add_argument("--count", type=int, default=100, help="Nombre de tickets (défaut: 100)")
    parser.add_argument("--url", type=str, default=None, help="URL de participation (défaut: http://localhost:5000)")
    args = parser.parse_args()

    base_url = args.url or BASE_URL
    if "localhost" in base_url or "127.0.0.1" in base_url:
        print("⚠️  Attention : l'URL de participation est en localhost. Les QR codes ne fonctionneront pas depuis un smartphone externe.")
        print("    Utilisez --url https://votre-domaine.com pour un déploiement réel.")
    generate_tickets(args.count, base_url=base_url)
