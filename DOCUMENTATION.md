# Documentation de Déploiement – Facty

Ce guide explique comment déployer l’application Facty :
- **Frontend** (React/Next.js + Tailwind) sur Vercel
- **Backend** (Python/FastAPI/Uvicorn) sur Render.com

---

## 1. Prérequis
- Un compte [Vercel](https://vercel.com/) (pour le frontend)
- Un compte [Render.com](https://render.com/) (pour le backend)
- Un compte [Hugging Face](https://huggingface.co/) et un token API valide
- Git installé sur votre machine

---

## 2. Déploiement du Backend (FastAPI sur Render.com)

### a. Préparer le dépôt
1. Placez tout le code backend dans le dossier `backend/`.
2. Vérifiez que le fichier `requirements.txt` contient toutes les dépendances nécessaires :
   - fastapi
   - uvicorn
   - python-dotenv
   - requests
   - pydantic
3. *(Optionnel, pour les tests en local)* Ajoutez un fichier `.env` dans `backend/` avec :
   ```env
   HF_API_TOKEN=VOTRE_TOKEN_HUGGINGFACE
   ```
   **Ne commitez jamais ce fichier sur GitHub.**
4. Sur Render.com, ajoutez la variable d’environnement `HF_API_TOKEN` dans l’interface du service (onglet Environment).

### b. Créer le service sur Render.com
1. Connectez votre dépôt GitHub à Render.com.
2. Cliquez sur "New Web Service".
3. Sélectionnez le dossier `backend/` comme racine du service.
4. **Build Command** :
   ```bash
   pip install -r requirements.txt
   ```
5. **Start Command** :
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 10000
   ```
6. Ajoutez la variable d’environnement `HF_API_TOKEN` dans l’interface Render (onglet Environment).
7. Déployez le service.
8. Notez l’URL publique de votre backend (ex : `https://facty-backend.onrender.com`).

---

## 3. Déploiement du Frontend (Next.js sur Vercel)

### a. Préparer le projet
1. Placez tout le code frontend dans le dossier `frontend/`.
2. Vérifiez que le fichier `package.json` et `tailwind.config.js` sont présents.
3. Ajoutez un fichier `.env.local` dans `frontend/` :
   ```env
   NEXT_PUBLIC_API_URL=https://facty-backend.onrender.com
   ```
   (Remplacez l’URL par celle de votre backend Render)

### b. Déployer sur Vercel
1. Connectez votre dépôt GitHub à Vercel.
2. Cliquez sur "New Project" et sélectionnez le dossier `frontend/`.
3. Vercel détecte automatiquement Next.js et configure le build.
4. Ajoutez la variable d’environnement `NEXT_PUBLIC_API_URL` dans les paramètres Vercel (onglet Environment Variables).
5. Déployez le projet.
6. L’URL publique de votre frontend sera du type `https://facty.vercel.app`.

---

## 4. Résumé des variables d’environnement

- **Backend (Render.com)** :
  - `HF_API_TOKEN` (clé Hugging Face)
- **Frontend (Vercel)** :
  - `NEXT_PUBLIC_API_URL` (URL du backend)

---

## 5. Conseils
- Ne jamais commiter vos fichiers `.env` dans Git !
- Pour tester en local, lancez le backend (`uvicorn app:app --reload`) et le frontend (`npm run dev`) avec les bons fichiers `.env`.
- Vérifiez que le CORS est bien activé sur le backend pour accepter les requêtes du frontend.

---

*Facty – Pour les enfants curieux !*
