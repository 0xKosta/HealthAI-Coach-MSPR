# HealthAI Coach — Frontend

Interface web du projet **HealthAI Coach**, développée avec Vue 3, Vite et Tailwind CSS.  
Elle consomme l'API FastAPI disponible sur `http://localhost:8000`.

---

## Stack technique

| Outil | Version | Rôle |
|---|---|---|
| Vue 3 | ^3.4 | Framework JavaScript (Composition API) |
| Vite | ^5.2 | Bundler et serveur de développement |
| Tailwind CSS | ^3.4 | Framework CSS utilitaire |
| Pinia | ^2.1 | Store global (sélection utilisateur) |
| Vue Router | ^4.3 | Routage client (SPA) |
| ApexCharts | ^5.10 | Graphiques biométriques |
| Axios | ^1.6 | Appels HTTP vers l'API |
| Google Material Symbols | CDN | Icônes d'interface |

---

## Prérequis

- **Node.js** ≥ 18
- **npm** ≥ 9
- Le **backend FastAPI** doit tourner sur `http://localhost:8000`

---

## Installation

```bash
# Depuis la racine du projet
cd front-end
npm install
```

## Lancer le serveur de développement

```bash
npm run dev
```

L'application est disponible sur **http://localhost:3000**

## Build de production

```bash
npm run build       # génère le dossier dist/
npm run preview     # prévisualise le build
```

---

## Structure du projet

```
front-end/
├── public/
│   ├── favicon.png              # Favicon (icône HealthAI Coach)
│   ├── logo-horizontal.png      # Logo complet (navbar desktop)
│   └── logo-icon.png            # Icône seule (navbar mobile)
├── src/
│   ├── assets/
│   │   └── main.css             # Tailwind + classes utilitaires globales
│   ├── components/
│   │   ├── layout/
│   │   │   └── Navbar.vue       # Navbar responsive (desktop + mobile)
│   │   └── ui/
│   │       ├── AIAdviceCard.vue # Carte réponse IA (fond bleu nuit)
│   │       ├── ErrorAlert.vue   # Alerte d'erreur
│   │       ├── LoadingSpinner.vue
│   │       ├── StatCard.vue     # Carte indicateur chiffré
│   │       └── UserSelector.vue # Dropdown sélection utilisateur
│   ├── router/
│   │   └── index.js             # Déclaration des 4 routes
│   ├── services/
│   │   └── api.js               # Tous les appels axios (users, coach, metrics…)
│   ├── stores/
│   │   └── userStore.js         # Store Pinia — utilisateur sélectionné
│   ├── views/
│   │   ├── DashboardView.vue    # Page principale — profil + conseil IA
│   │   ├── NutritionView.vue    # Analyse photo repas (vision IA)
│   │   ├── WorkoutView.vue      # Génération programme d'entraînement
│   │   └── TrendsView.vue       # Graphiques biométriques + tendances IA
│   ├── App.vue                  # Composant racine + layout
│   └── main.js                  # Point d'entrée (Pinia, Router, ApexCharts)
├── index.html
├── package.json
├── tailwind.config.js           # Palette charte graphique HealthAI Coach
├── vite.config.js
└── postcss.config.js
```

---

## Pages

### `/` — Dashboard
- Sélecteur d'utilisateur global (persistant sur toutes les pages)
- Carte profil : âge, IMC, poids, taille, masse grasse
- Indicateurs rapides : score santé, objectif, catégorie IMC
- Bouton **"Obtenir un conseil IA"** → appelle `POST /coach/advice`

### `/nutrition` — Analyse nutritionnelle
- Upload d'image par clic ou **drag & drop**
- Envoi en base64 → `POST /coach/analyze-photo`
- Affichage des aliments détectés + macros (calories, protéines, glucides, lipides)
- Conseil nutritionnel IA

### `/workout` — Programme d'entraînement
- Sélection de l'équipement disponible (6 options avec icônes Material)
- Sélection du nombre de jours par semaine (1 à 7)
- Génération via `POST /coach/workout-plan`
- Affichage du programme formaté

### `/trends` — Tendances biométriques
- KPIs : poids actuel, sommeil moyen, BPM repos, nombre d'entrées
- Graphique courbe de poids (30 jours)
- Graphique sommeil + BPM repos
- Analyse des tendances via `POST /coach/biometric-trend`

---

## Charte graphique

Palette définie dans `tailwind.config.js` :

| Token | Valeur | Usage |
|---|---|---|
| `brand-primary` | `#08104D` | Navbar, titres, zones structurantes |
| `brand-secondary` | `#123C69` | Navigation, blocs institutionnels |
| `brand-accent` | `#00B4D8` | Actions principales, focus, liens |
| `brand-success` | `#2DD4BF` | Validation, progression |
| `brand-light` | `#EEF6FF` | Arrière-plan général |
| `brand-neutral` | `#F4F7FB` | Cartes, surfaces UI, Dashboard |
| `brand-text` | `#111827` | Texte principal |
| `brand-warning` | `#F59E0B` | Alertes non bloquantes |
| `brand-error` | `#DC2626` | Erreurs, états critiques |

Typographie : **Inter** (400 / 600 / 700) — chargée via Google Fonts.

---

## Endpoints API utilisés

| Méthode | Endpoint | Page |
|---|---|---|
| `GET` | `/users/` | Toutes (sélecteur) |
| `GET` | `/users/{id}` | Dashboard |
| `GET` | `/metrics/` | Trends |
| `POST` | `/coach/advice` | Dashboard |
| `POST` | `/coach/analyze-photo` | Nutrition |
| `POST` | `/coach/workout-plan` | Workout |
| `POST` | `/coach/biometric-trend` | Trends |

> Le CORS est configuré côté backend pour accepter `http://localhost:3000`.

---

## Conventions de développement

- **Composition API** avec `<script setup>` sur tous les composants
- Appels API **centralisés** dans `src/services/api.js` — ne pas appeler axios directement dans les vues
- Chaque appel API gère ses états **loading** et **error** localement
- Les classes CSS réutilisables sont définies dans `main.css` (`.card`, `.btn-primary`, `.input`…)
- Aucune logique métier dans les composants UI (`ui/`)
