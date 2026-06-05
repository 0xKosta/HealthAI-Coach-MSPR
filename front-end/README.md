# HealthAI Coach — Frontend

Interface **PWA** du projet HealthAI Coach (Vue 3, Vite, Tailwind).  
Consomme l'API FastAPI via `VITE_API_BASE_URL` (défaut `http://localhost:8000`).

| Mode | URL front | API |
|------|-----------|-----|
| **Dev** | http://localhost:3000 | `:8000` (uvicorn local ou Docker) |
| **Preview PWA** | http://localhost:4173 | `:8000` |
| **Docker MSPR3** | http://localhost:8080 | `:8000` (build nginx) |

Référence ports / comptes : [`../docs/reference-demo.md`](../docs/reference-demo.md).

---

## Stack technique

| Outil | Version | Rôle |
|---|---|---|
| Vue 3 | ^3.4 | Framework (Composition API, `<script setup>`) |
| Vite | ^5.2 | Bundler et dev server (port **3000**) |
| Tailwind CSS | ^3.4 | Styles utilitaires |
| Pinia | ^2.1 | État global (auth, utilisateur sélectionné, statut API) |
| Vue Router | ^4.3 | SPA + guards JWT / admin |
| ApexCharts | ^5.10 | Graphiques biométriques |
| Axios | ^1.6 | HTTP vers l'API |
| vite-plugin-pwa | ^1.3 | Service Worker + manifest installable |

---

## Prérequis

- **Node.js** ≥ 18, **npm** ≥ 9
- **Backend** sur `http://localhost:8000` :
  - dev local : `uvicorn api.main:app --reload` (racine du repo)
  - démo jury : `.\scripts\demo-up.ps1` → PWA `:8080` + API `:8000`

Si l'API est arrêtée, l'app affiche **« Serveur déconnecté »** (ping `/health` + détection erreurs réseau).

---

## Installation et commandes

```bash
cd front-end
npm install
```

| Commande | Description |
|---|---|
| `npm run dev` | Dev — http://localhost:3000 (PWA **non** installable) |
| `npm run build` | Build production → `dist/` |
| `npm run preview` | Preview du build — http://localhost:4173 (PWA testable) |
| `npm test` | Vitest — logique profil IA & statut API |
| `npm run test:watch` | Vitest en mode watch |

> Service Worker **désactivé en `dev`**. Installation PWA : `npm run build && npm run preview` ou stack Docker `:8080`.

### Build Docker

L'image front (`Dockerfile.front`) injecte `VITE_API_BASE_URL=http://localhost:8000` au build. Ne pas oublier de rebuild après changement d'URL API :

```bash
docker compose --profile full up -d --build
```

---

## Tests front (Vitest)

```bash
npm test
```

**7 tests** sur la logique UI critique :

| Fichier | Sujet |
|---------|--------|
| `useProfileCompletion.spec.js` | Accès coach IA selon profil complet |
| `apiStatus.spec.js` | Détection panne réseau / API down |

Parcours complets (login, nutrition, feed, PWA) : recette manuelle — voir [`../docs/plan-de-tests.md`](../docs/plan-de-tests.md).

---

## Authentification

- Connexion / inscription : `/login`, `/register` (JWT → `localStorage`, clé `healthai_token`)
- Profil santé : `GET` / `PUT` **`/auth/me/profile`**
- Compte (email, plan, rôle) : **`/auth/me`**
- Admin : **`/auth/admin/users`**, routes `requiresAdmin`
- Routes protégées : guard `requiresAuth`

Stores Pinia : `authStore`, `userStore` (contexte admin), `apiStatusStore`.

---

## PWA & mobile

| Élément | Détail |
|---|---|
| Manifest | `standalone`, icônes 192 / 512 |
| Service Worker | Workbox (`vite-plugin-pwa`) |
| Cache API | `NetworkFirst` sur `/api/` (TTL 5 min) |
| Bannière install | `PwaInstallBanner.vue` |
| Navigation tactile | Swipe horizontal entre vues (`useViewNav`) |

Doc complète : [`../docs/application-mobile-pwa.md`](../docs/application-mobile-pwa.md).

**Tester l'installation :** Chrome DevTools → Application → Manifest / Service Workers, ou Safari « Sur l'écran d'accueil ».

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
│   │                            # ServerUnavailableView, PlanBadge, PwaInstallBanner…
│   ├── composables/           # useProfileCompletion, useAiAccess, useViewNav…
│   ├── router/                # index.js, redirect.js, transition.js
│   ├── services/api.js        # authAPI, coachAPI, postsAPI, aiRequestsAPI…
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
- **`/login`**, **`/register`** — JWT, redirection dashboard ou admin

### Utilisateur (`/dashboard/:userId/…`)
- **Dashboard** — profil, stats, conseil IA (`POST /coach/advice`), verrou si profil incomplet
- **Nutrition** — photo repas (`/coach/analyze-photo`), plan repas (`/coach/meal-plan`), historique IA Premium
- **Workout** — `POST /coach/workout-plan`
- **Trends** — métriques + `POST /coach/biometric-trend`
- **Profile** — `PUT /auth/me/profile`, validation biométrique temps réel
- **Communauté** — **`/dashboard/:userId/feed`** (`FeedView.vue`) : feed, publication texte/média, likes, commentaires
- **`/exercises`** — catalogue `GET /exercises/`
- **`/no-profile`** — compte sans profil santé lié

Navigation : onglets Navbar + swipe entre Dashboard / Nutrition / Entraînement / Tendances ; onglet **Communauté** séparé.

### Admin (`/admin/…`)
- **Liste utilisateurs** — `TrendsUsersView`, filtres, édition compte (email, plan, rôle)
- **Création utilisateur** — `AdminUserCreateView`
- **Fiches user** — mêmes vues que l'utilisateur (dashboard, nutrition, workout, trends, profile) + onglets admin + historique IA sur Nutrition

---

## Indisponibilité API

- Au démarrage : vérification périodique **`GET /health`**
- Requête axios sans réponse réseau → **`ServerUnavailableView`**
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

## Endpoints API utilisés

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
| `GET` | `/posts/` | Feed social |
| `POST` | `/posts/` | Créer publication (multipart) |
| `POST` | `/posts/{id}/like` | Like / unlike |
| `GET` / `POST` | `/posts/{id}/comments` | Commentaires |
| `DELETE` | `/posts/{id}` | Supprimer sa publication |

Règles biométriques et quotas IA : [`../docs/validation-biometrique.md`](../docs/validation-biometrique.md).

**CORS backend** (`.env` / Docker) : `http://localhost:3000`, `http://localhost:4173`, `http://localhost:8080`.

---

## Conventions

- Composition API + `<script setup>`
- Appels HTTP **uniquement** via `src/services/api.js`
- États **loading** / **error** dans les vues
- Composants `ui/` sans logique métier lourde

Benchmark framework : [`../benchmark-frontend.md`](../benchmark-frontend.md) (racine du repo).
