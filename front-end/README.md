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
| vite-plugin-pwa | ^1.3 | Service Worker + manifest (PWA) |
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

---

## Commandes disponibles

| Commande | Description |
|---|---|
| `npm run dev` | Serveur de développement — `http://localhost:3000` |
| `npm run build` | Build de production (génère `dist/`) |
| `npm run preview` | Prévisualise le build de prod — `http://localhost:4173` |

> **Important :** le Service Worker PWA est **désactivé en mode `dev`** par conception (Vite).  
> Pour tester la PWA (installation, cache offline), utiliser `npm run build && npm run preview`.

---

## PWA — Progressive Web App

L'application est une PWA complète, installable sur desktop et mobile.

### Ce qui est en place

| Élément | Détail |
|---|---|
| Manifest | Nom, short name, description, icônes, `display: standalone`, `theme_color` |
| Service Worker | Généré par Workbox via `vite-plugin-pwa` |
| Cache statique | HTML, CSS, JS, images — précachés au premier chargement |
| Cache API | Stratégie `NetworkFirst` sur `/api/` (TTL 5 min, 50 entrées max) |
| Icônes | 192×192 et 512×512 (générées via [realfavicongenerator.net](https://realfavicongenerator.net)) |
| Support iOS | `apple-touch-icon`, balises meta `apple-mobile-web-app-*` |

### Tester la PWA

```bash
npm run build && npm run preview
```

Ensuite dans Chrome DevTools → **Application** :
- **Manifest** : vérifier nom, icônes, `display: standalone`
- **Service Workers** : doit afficher `activated and running`
- **Cache Storage** : liste les fichiers précachés

Le bouton d'installation apparaît dans la barre d'adresse Chrome une fois la PWA valide.

### Fonctionnement en production

Le build est à effectuer **une seule fois** par déploiement (ou à chaque modification du code).  
Le Service Worker persiste dans le navigateur et gère le cache automatiquement — aucune commande à relancer côté utilisateur.

---

## Structure du projet

```
front-end/
├── public/
│   ├── favicon.png              # Favicon navigateur
│   ├── favicon-96x96.png        # Favicon haute résolution
│   ├── apple-touch-icon.png     # Icône iOS (ajout écran d'accueil)
│   ├── pwa-192x192.png          # Icône PWA manifest
│   ├── pwa-512x512.png          # Icône PWA manifest (maskable)
│   ├── healthai-coach-logo-light-navbar-text-subtitle-big.svg  # Logo complet (navbar)
│   └── healthai-coach-icon-light-navbar.svg        # Icône seule (navbar mobile)
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
│   │       ├── ProfileAiGate.vue      # Blocage IA (profil incomplet / invalide)
│   │       ├── ProfileDataWarning.vue # Bandeau correction profil
│   │       ├── StatCard.vue     # Carte indicateur chiffré
│   │       └── UserSelector.vue # Dropdown sélection utilisateur
│   ├── composables/
│   │   ├── useBiometricValidation.js  # Bornes + validation formulaire profil
│   │   └── useProfileCompletion.js    # blocksAiFeatures, profile_issues…
│   ├── router/
│   │   └── index.js             # Déclaration des routes
│   ├── services/
│   │   └── api.js               # Tous les appels axios (users, coach, metrics…)
│   ├── stores/
│   │   └── userStore.js         # Store Pinia — utilisateur sélectionné
│   ├── views/
│   │   ├── DashboardView.vue    # Page principale — profil + conseil IA
│   │   ├── NutritionView.vue    # Analyse photo repas (vision IA)
│   │   ├── WorkoutView.vue      # Génération programme d'entraînement
│   │   ├── ExercisesView.vue    # Catalogue d'exercices
│   │   └── TrendsView.vue       # Graphiques biométriques + tendances IA
│   ├── App.vue                  # Composant racine + layout
│   └── main.js                  # Point d'entrée (Pinia, Router, ApexCharts)
├── index.html
├── package.json
├── tailwind.config.js           # Palette charte graphique HealthAI Coach
├── vite.config.js               # Config Vite + plugin PWA
└── postcss.config.js
```

---

## Pages

### `/dashboard/:userId` — Dashboard
- Carte profil : âge, IMC, poids, taille, masse grasse
- **Profil incomplet ou invalide** : bandeau d'accueil / correction avec liste des erreurs, stats et IA verrouillés
- Indicateurs rapides et conseil IA disponibles uniquement si `blocksAiFeatures(user)` est faux
- Bouton **« Obtenir un conseil IA »** → `POST /coach/advice` (refusé côté API si profil non conforme)

### `/dashboard/:userId/nutrition` — Analyse nutritionnelle
- `ProfileAiGate` si profil incomplet ou biométrie hors limites
- Upload d'image → `POST /coach/analyze-photo`

### `/dashboard/:userId/workout` — Programme d'entraînement
- `ProfileAiGate` si profil non prêt pour l'IA
- Génération via `POST /coach/workout-plan`

### `/dashboard/:userId/profile` — Édition profil santé
- Validation temps réel (âge 18–100, taille 90–230 cm, poids 20–300 kg, IMC 10–80)
- Erreurs par champ + blocage à l'envoi ; affichage des `profile_issues` retournés par l'API

### `/exercises` — Catalogue d'exercices
- Consultation du catalogue complet via `GET /exercises`

### `/dashboard/:userId/trends` — Tendances biométriques
- KPIs et graphiques (30 jours) — données `GET /metrics/`
- Analyse IA verrouillée si profil incomplet/invalide ; sinon `POST /coach/biometric-trend` après 7 jours de données

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
| `GET` | `/users/{id}` | Dashboard, Nutrition, Workout, Trends (`profile_issues`) |
| `GET` / `PUT` | `/auth/me/profile` | ProfileEditView |
| `GET` | `/metrics/` | Trends |
| `GET` | `/exercises/` | Exercises |
| `POST` | `/coach/advice` | Dashboard (profil valide requis) |
| `POST` | `/coach/analyze-photo` | Nutrition |
| `POST` | `/coach/workout-plan` | Workout |
| `POST` | `/coach/biometric-trend` | Trends |

Règles biométriques et verrouillage IA : [`../docs/validation-biometrique.md`](../docs/validation-biometrique.md).

> Le CORS est configuré côté backend pour accepter `http://localhost:3000` et `http://localhost:4173` (preview).

---

## Conventions de développement

- **Composition API** avec `<script setup>` sur tous les composants
- Appels API **centralisés** dans `src/services/api.js` — ne pas appeler axios directement dans les vues
- Chaque appel API gère ses états **loading** et **error** localement
- Les classes CSS réutilisables sont définies dans `main.css` (`.card`, `.btn-primary`, `.input`…)
- Aucune logique métier dans les composants UI (`ui/`)
