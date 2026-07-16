#!/usr/bin/env python3
"""
Effectue le tirage au sort des gagnants de la tombola DFCO - Golden Coast.
Stockage SQLite et tirage sécurisé avec le module secrets.
"""

import os
import json
import secrets
import sqlite3
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "tombola.db")


def load_participants():
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT ticket_id, email, name FROM tickets WHERE used = 1"
        ).fetchall()
        return [dict(r) for r in rows]


def draw_winners(count=3):
    participants = load_participants()

    if not participants:
        print("❌ Aucun participant enregistré.")
        return

    if count > len(participants):
        print(f"⚠️ Nombre de gagnants ({count}) supérieur au nombre de participants ({len(participants)}).")
        count = len(participants)

    winners = secrets.SystemRandom().sample(participants, count)

    print(f"\n🎉 Tirage au sort DFCO - Golden Coast ({datetime.now().strftime('%d/%m/%Y %H:%M')})")
    print(f"Nombre de participants : {len(participants)}")
    print(f"Nombre de gagnants : {count}\n")

    for i, winner in enumerate(winners, 1):
        print(f"{i}. 🏆 Ticket {winner['ticket_id']}")
        print(f"   Email : {winner['email']}")
        print(f"   Nom   : {winner.get('name') or 'Non renseigné'}\n")

    # Sauvegarde des gagnants
    winners_file = os.path.join(BASE_DIR, "winners.json")
    with open(winners_file, "w", encoding="utf-8") as f:
        json.dump(winners, f, indent=2, ensure_ascii=False)

    print(f"💾 Résultats sauvegardés dans : {winners_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tirage au sort de la tombola DFCO")
    parser.add_argument("--count", type=int, default=3, help="Nombre de gagnants (défaut: 3)")
    args = parser.parse_args()
    draw_winners(args.count)
