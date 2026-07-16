#!/usr/bin/env python3
"""
Application web de participation à la tombola DFCO - Golden Coast.
Collecte les emails des supporters et les associe à un numéro de ticket.
Stockage en SQLite pour éviter les problèmes de concurrence.
"""

import os
import re
import time
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, make_response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dfco-golden-coast-tombola-2024")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "tombola.db")

# Authentification basique pour l'admin
ADMIN_USERNAME = os.environ.get("ADMIN_USER")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASS")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("Les variables d'environnement ADMIN_USER et ADMIN_PASS sont obligatoires.")

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Rate limiting simple en mémoire (par IP)
IP_TRACKER = {}
COOLDOWN_SECONDS = 10


def get_client_ip():
    """Récupère l'IP réelle du client, même derrière un proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def clean_ip_tracker():
    """Supprime les entrées de rate limiting trop anciennes."""
    now = time.time()
    expired = [ip for ip, ts in IP_TRACKER.items() if now - ts > COOLDOWN_SECONDS * 10]
    for ip in expired:
        del IP_TRACKER[ip]


def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
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


def ticket_exists(ticket_id):
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
        return row is not None


def register_participant(ticket_id, email, name, rgpd):
    if not ticket_exists(ticket_id):
        return False, "Numéro de ticket invalide."

    with get_db() as conn:
        row = conn.execute(
            "SELECT used FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
        if row["used"]:
            return False, "Ce ticket a déjà été utilisé."

        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE tickets SET used = 1, email = ?, name = ?, rgpd_consent = ?, registered_at = ? WHERE ticket_id = ?",
            (email, name, 1 if rgpd else 0, now, ticket_id)
        )
    return True, "Participation enregistrée avec succès !"


def get_participants():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT ticket_id, email, name FROM tickets WHERE used = 1 ORDER BY registered_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def get_total_tickets():
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as total FROM tickets").fetchone()
        return row["total"]


def get_all_participants():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT ticket_id, email, name, rgpd_consent, registered_at FROM tickets WHERE used = 1 ORDER BY registered_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            response = make_response("Authentification requise", 401)
            response.headers["WWW-Authenticate"] = 'Basic realm="Admin DFCO"'
            return response
        return f(*args, **kwargs)
    return decorated


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/", methods=["GET", "POST"])
def index():
    ticket_id = request.args.get("ticket", "").upper().strip()
    message = None
    error = None

    if request.method == "POST":
        clean_ip_tracker()
        ip = get_client_ip()
        now = time.time()

        if ip in IP_TRACKER and (now - IP_TRACKER[ip]) < COOLDOWN_SECONDS:
            error = "Veuillez patienter quelques secondes avant de réessayer."
        else:
            ticket_id = request.form.get("ticket_id", "").upper().strip()
            email = request.form.get("email", "").strip().lower()
            name = request.form.get("name", "").strip()
            rgpd = request.form.get("rgpd") == "on"

            if not ticket_id or not email:
                error = "Merci de renseigner le numéro de ticket et l'email."
            elif not EMAIL_REGEX.match(email):
                error = "Merci de saisir un email valide."
            elif not rgpd:
                error = "Vous devez accepter les conditions et la politique de confidentialité."
            else:
                success, msg = register_participant(ticket_id, email, name, rgpd)
                if success:
                    message = msg
                    IP_TRACKER[ip] = now
                else:
                    error = msg

    return render_template("index.html", ticket_id=ticket_id, message=message, error=error)


@app.route("/admin")
@admin_required
def admin():
    participants = get_participants()
    total = get_total_tickets()
    return render_template("admin.html", participants=participants, total=total)


@app.route("/admin/export")
@admin_required
def export_participants():
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ticket_id", "email", "name", "rgpd_consent", "registered_at"])
    for p in get_all_participants():
        writer.writerow([p["ticket_id"], p["email"], p["name"], p["rgpd_consent"], p["registered_at"]])

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=participants_dfco.csv"
    return response


with app.app_context():
    init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
