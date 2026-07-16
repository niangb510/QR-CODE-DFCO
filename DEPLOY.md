# 🚀 Déploiement sur Render

Ce document explique comment déployer l'application de tombola DFCO sur Render avec une URL publique.

## Prérequis

- Un compte Render (gratuit) : https://render.com
- Le projet dans le dossier `QRCODE` sur ton ordinateur

## Étapes

### 1. Pousser le projet sur GitHub

Render déploie automatiquement depuis un dépôt Git. Crée un dépôt GitHub et pousse le contenu du dossier `QRCODE` :

```bash
cd /Users/niangnbaye/Desktop/QRCODE
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TON_UTILISATEUR/ton-repo.git
git push -u origin main
```

### 2. Créer un service Web sur Render

1. Connecte-toi sur [Render](https://render.com).
2. Clique sur **New +** → **Web Service**.
3. Choisis ton dépôt GitHub.
4. Remplis les champs :
   - **Name** : `tombola-dfco`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
5. Clique sur **Advanced** et ajoute les variables d'environnement :
   - `ADMIN_USER` : ton identifiant admin
   - `ADMIN_PASS` : ton mot de passe admin
   - `SECRET_KEY` : une clé secrète longue et aléatoire
6. Clique sur **Create Web Service**.

### 3. Récupérer l'URL publique

Une fois le déploiement terminé, Render te donne une URL publique du type :

```
https://tombola-dfco.onrender.com
```

### 4. Régénérer les tickets avec l'URL publique

Sur ton ordinateur local, dans le dossier `QRCODE`, exécute :

```bash
python3 generate_tickets.py --count 100 --url https://tombola-dfco.onrender.com
```

Le fichier `tickets_tombola.pdf` contiendra alors des QR codes pointant vers l'application en ligne.

### 5. Imprimer et distribuer les tickets

Imprime le fichier `tickets_tombola.pdf` et distribue les tickets lors de l'événement Golden Coast.

## ⚠️ Important : persistance SQLite sur Render

**Le tier gratuit de Render utilise un disque éphémère.** Cela signifie que si le service redémarre (déploiement, inactivité, etc.), les données de `tombola.db` seront perdues.

### Workflow recommandé pour l'événement

1. **Génère les tickets localement** avec l'URL publique de Render.
2. **Déploie l'application sur Render** sans pousser `tombola.db` (elle est dans `.gitignore`).
3. **Uploade la base `tombola.db` initiale** sur Render via le shell du service, ou utilise le bouton "Upload File" dans le dashboard.
4. **Pendant l'événement**, exporte régulièrement les participants via `/admin/export` en CSV.
5. **Après l'événement**, fais immédiatement un export CSV et un tirage au sort.
6. **Ne redéploie pas** l'application pendant l'événement.

**Le tier gratuit de Render utilise un disque éphémère.** Cela signifie que si le service redémarre (déploiement, inactivité, etc.), les données de `tombola.db` seront perdues.

### Recommandations pour l'événement

1. **Avant l'événement** : génère les tickets avec l'URL publique et télécharge la base `tombola.db` initiale depuis Render (via le shell Render) ou garde une copie locale.
2. **Pendant l'événement** : exporte régulièrement les participants via `/admin/export` en CSV.
3. **Après l'événement** : fais immédiatement un export CSV et un tirage au sort.
4. **Évite les redémarrages** : ne redéploie pas l'application pendant l'événement.

### Alternative plus robuste

Pour une persistance durable, utilise une base de données PostgreSQL (Render en propose une gratuite) et adapte `app.py`. Cependant, pour un événement d'une journée avec export régulier, SQLite sur Render est généralement suffisant.

## Dépannage

- **L'application ne démarre pas** : vérifie les logs dans le dashboard Render.
- **Les QR codes ne fonctionnent pas** : assure-toi que l'URL passée à `generate_tickets.py` correspond bien à l'URL publique de Render.
- **Accès admin refusé** : vérifie que les variables d'environnement `ADMIN_USER` et `ADMIN_PASS` sont correctement définies.
