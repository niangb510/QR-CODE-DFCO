# 🎟️ Tombola DFCO - Golden Coast

Solution micro tombola par QR code pour le DFCO lors de l'événement Golden Coast.

## Objectifs

- Permettre aux supporters de participer à une tombola en scannant un QR code.
- Collecter les emails pour enrichir la base supporters.
- Tirer au sort les gagnants parmi les participants.

## Fichiers

| Fichier | Description |
|---------|-------------|
| `generate_tickets.py` | Génère les tickets PDF imprimables avec QR codes uniques |
| `app.py` | Application web Flask de collecte des emails (SQLite) |
| `draw_winners.py` | Script de tirage au sort des gagnants |
| `templates/index.html` | Formulaire de participation |
| `templates/admin.html` | Page d'administration protégée |
| `tombola.db` | Base de données SQLite des tickets et participants |
| `tickets_tombola.pdf` | Fichier PDF des tickets à imprimer |
| `winners.json` | Résultats du tirage au sort |

## Installation

Les dépendances Python sont : `qrcode`, `reportlab`, `flask`.

```bash
pip3 install qrcode[pil] reportlab flask
```

## Configuration

L'application utilise des variables d'environnement pour l'administration :

```bash
export ADMIN_USER="votre_utilisateur_admin"
export ADMIN_PASS="votre_mot_de_passe_admin"
export SECRET_KEY="une_cle_secrete_longue_et_aleatoire"
```

## Utilisation

### 1. Générer les tickets

```bash
python3 generate_tickets.py --count 100
```

Le fichier `tickets_tombola.pdf` est créé dans le dossier `QRCODE`, prêt à être imprimé.

Pour utiliser une URL de production :

```bash
python3 generate_tickets.py --count 100 --url https://votre-domaine.com
```

### 2. Lancer l'application web

```bash
python3 app.py
```

L'application est accessible à l'adresse : `http://localhost:5000`

### 3. Les supporters participent

- Ils scannent le QR code avec leur smartphone.
- Ils saisissent leur email sur le formulaire.
- Ils acceptent les conditions et la politique de confidentialité.
- Leur participation est enregistrée.

### 4. Consulter les participants

Accédez à `/admin` et connectez-vous avec les identifiants définis dans les variables d'environnement.

### 5. Tirage au sort

```bash
python3 draw_winners.py --count 3
```

## Déploiement sur Render

Pour déployer l'application sur Render avec une URL publique, consultez le fichier [DEPLOY.md](DEPLOY.md).

## Déploiement en production

Pour un usage réel, adaptez l'URL dans `generate_tickets.py` :

```python
BASE_URL = "https://votre-domaine.com"
```

Et lancez l'application sur un serveur web sécurisé (HTTPS) avec un serveur WSGI comme Gunicorn :

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Sécurité et RGPD

- Les emails sont collectés avec consentement explicite via la case RGPD du formulaire.
- La page d'administration est protégée par authentification HTTP Basic.
- Les identifiants admin et la clé secrète sont configurables par variables d'environnement.
- Conservez les données de manière sécurisée et limitez leur durée de conservation.
