# HealthAI Coach - Frontend

Interface web du projet **HealthAI Coach** (Vue 3, Vite, Tailwind).  
Elle consomme l'API FastAPI sur `http://localhost:8000` (variable `VITE_API_BASE_URL`).

---

## Stack technique

| Outil | Version | Rôle |
|---|---|---|
| Vue 3 | ^3.4 | Framework (Composition API, `<script setup>`) |
| Vite | ^5.2 | Bundler et dev server |
| Tailwind CSS | ^3.4 | Styles utilitaires |
| Pinia | ^2.1 | État global (auth, utilisateur sélectionné, statut API) |
| Vue Router | ^4.3 | SPA + guards JWT / admin |
| ApexCharts | ^5.10 | Graphiques biométriques |
| Axios | ^1.6 | HTTP vers l'API |
| vite-plugin-pwa | ^1.3 | Service Worker + manifest |

---

## Prérequis

- **Node.js** ≥ 18, **npm** ≥ 9
- **Backend** sur `http://localhost:8000` (`uvicorn api.main:app --reload` depuis la racine du repo)

Si l'API est arrêtée, l'app affiche un écran **« Serveur déconnecté »** (ping `/health` + détection des erreurs réseau).

---

## Installation et commandes

```bash
cd front-end
npm install
```

| Commande | Description |
|---|---|
| `npm run dev` | Dev — `http://localhost:3000` |
| `npm run build` | Build production → `dist/` |
| `npm run preview` | Preview du build — `http://localhost:4173` |
| `npm test` | Tests unitaires front (Vitest) — logique profil IA & statut API |

> Le Service Worker PWA est **désactivé en `dev`**. Tester l'installation PWA : `npm run build && npm run preview`.

### Tests front (Vitest)

```bash
npm test
```

Couvre la logique métier UI critique (`useProfileCompletion`, détection panne réseau). Les parcours complets (login, nutrition) restent en recette manuelle / E2E prévus MSPR3.

---

## Authentification

- Connexion / inscription : `/login`, `/register` (JWT dans `localStorage`, clé `healthai_token`)
- Profil santé utilisateur : `GET` / `PUT` **`/auth/me/profile`**
- Compte (email, plan, rôle) : **`/auth/me`**, admin → **`/auth/admin/users`**
- Routes protégées : guard `requiresAuth` ; back-office : `requiresAdmin`

Stores Pinia : `authStore` (session), `userStore` (utilisateur affiché en admin), `apiStatusStore` (API joignable ou non).

---

## PWA

| Élément | Détail |
|---|---|
| Manifest | `standalone`, icônes 192 / 512 |
| Service Worker | Workbox (`vite-plugin-pwa`) |
| Cache API | `NetworkFirst` sur `/api/` (TTL 5 min) |

Voir section « Tester la PWA » : build + preview + Chrome DevTools → Application.

---

## Structure du projet

```
front-end/
├── public/                    # Favicon, PWA, logos SVG
├── src/
│   ├── assets/main.css        # Tailwind + .card, .btn-primary, .input…
│   ├── components/
│   │   ├── layout/            # Navbar, AdminUserTabs
│   │   ├── admin/             # AiRequestHistoryPanel
│   │   └── ui/                # AIAdviceCard, ErrorAlert, ProfileAiGate,
│   │                            # ServerUnavailableView, PlanBadge…
│   ├── composables/           # useProfileCompletion, useAiAccess, useDisplayName…
│   ├── router/                # index.js, redirect.js, transition.js
│   ├── services/api.js        # Axios + authAPI, coachAPI, aiRequestsAPI…
│   ├── stores/
│   │   ├── authStore.js
│   │   ├── userStore.js
│   │   └── apiStatusStore.js
│   ├── views/                 # Voir « Pages » ci-dessous
│   ├── App.vue
│   └── main.js
├── vite.config.js             # port 3000, plugin PWA
└── tailwind.config.js
```

---

## Pages

### Authentification (publiques)
- **`/login`**, **`/register`** — JWT, redirection vers dashboard ou admin

### Utilisateur (`/dashboard/:userId/…`)
- **Dashboard** — profil, stats, conseil IA (`POST /coach/advice`), verrouillage si profil incomplet
- **Nutrition** — onglets **photo repas** (`/coach/analyze-photo`) et **plan repas** (`/coach/meal-plan`), historique IA Premium
- **Workout** — `POST /coach/workout-plan`
- **Trends** — métriques + `POST /coach/biometric-trend`
- **Profile** — `PUT /auth/me/profile`, validation biométrique temps réel
- **`/exercises`** — catalogue `GET /exercises/`
- **`/no-profile`** — compte sans profil santé lié

### Admin (`/admin/…`)
- **Liste utilisateurs** — `TrendsUsersView`, filtres, édition compte (email, plan, rôle)
- **Création utilisateur** — `AdminUserCreateView`
- **Fiches user** — même vues que l'utilisateur (dashboard, nutrition, workout, trends, profile) avec onglets admin + double historique IA sur Nutrition

---

## Indisponibilité API

- Au démarrage : vérification périodique de **`GET /health`**
- Toute requête axios sans réponse réseau → écran plein **`ServerUnavailableView`**
- Bouton **Réessayer** relance le health check

---

## Charte graphique

Palette dans `tailwind.config.js` :

| Token | Usage |
|---|---|
| `brand-primary` | Navbar, titres |
| `brand-accent` | Actions, focus |
| `brand-light` | Fond général |
| `brand-error` | Erreurs |

Typo : **Inter** (Google Fonts).

---

## Endpoints API utilisés (principal)

| Méthode | Endpoint | Usage |
|---|---|---|
| `GET` | `/health` | Disponibilité serveur |
| `POST` | `/auth/login`, `/auth/register` | Session |
| `GET` / `PUT` | `/auth/me/profile` | Profil santé |
| `GET` | `/users/{id}` | Profil (admin ou soi) |
| `GET` | `/metrics/` | Trends |
| `GET` | `/exercises/` | Catalogue |
| `GET` | `/ai-requests/` | Historique IA (Premium / admin) |
| `POST` | `/coach/advice` | Dashboard |
| `POST` | `/coach/analyze-photo` | Nutrition (photo) |
| `POST` | `/coach/meal-plan` | Nutrition (plan repas) |
| `POST` | `/coach/workout-plan` | Workout |
| `POST` | `/coach/biometric-trend` | Trends |

Règles biométriques et quotas IA : [`../docs/validation-biometrique.md`](../docs/validation-biometrique.md).

CORS backend : `http://localhost:3000` et `http://localhost:4173`.

---

## Conventions

- Composition API + `<script setup>`
- Appels HTTP **uniquement** via `src/services/api.js`
- États **loading** / **error** gérés dans les vues
- Composants `ui/` sans logique métier lourde

Benchmark framework : [`../benchmark-frontend.md`](../benchmark-frontend.md) (racine du repo).
