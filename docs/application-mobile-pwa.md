# Application mobile — PWA HealthAI Coach (MSPR3)

## Choix technique

HealthAI Coach livre une **Progressive Web App (PWA)** installable sur **Android** et **iOS**, au lieu d'une application native App Store / Play Store.

| Critère | PWA | App native (Expo/RN) |
|---------|-----|----------------------|
| Coûts stores | Aucun | Frais + review |
| Codebase | Un seul (Vue 3 + Vite) | Projet mobile séparé |
| Déploiement | Immédiat (build web) | Publication store |
| Cas d'usage | Feed social, formulaires, dashboards | AR, NFC, hardware profond |

Validation formateur EPSI : la PWA est acceptée comme livrable « application mobile compatible Android et iOS ».

## Implémentation

- Plugin : `vite-plugin-pwa` ([`front-end/vite.config.js`](../front-end/vite.config.js))
- Manifest : `display: standalone`, icônes 192/512 maskable
- Service Worker : Workbox, cache API `NetworkFirst`
- Réseau social : route `/dashboard/:userId/feed` ([`FeedView.vue`](../front-end/src/views/FeedView.vue))
- API : `/posts` (publications, likes, commentaires, médias)

## Stockage des photos (hors Git)

Les images du feed sont enregistrées en **local** dans `media/posts/` pendant le développement. Ce dossier est **exclu de Git** (même règle que `media/ai-photos/`). Les métadonnées (URL, type) restent en base (`posts.media_url`). Un **serveur de stockage** (MinIO, S3, volume Docker persistant) sera branché en production.

## Installation sur mobile

### Android (Chrome)

1. Ouvrir `http://localhost:8080` (ou URL de démo)
2. Se connecter
3. Menu navigateur → **Installer l'application** ou bannière « Installer »
4. Lancer depuis l'icône — mode plein écran

### iOS (Safari)

1. Ouvrir le site dans Safari
2. Bouton **Partager** → **Sur l'écran d'accueil**
3. Confirmer — l'app s'ouvre en `standalone`

Composant d'aide : [`PwaInstallBanner.vue`](../front-end/src/components/ui/PwaInstallBanner.vue).

## Fonctionnalités sociales (PWA)

- Consulter le fil (`GET /posts/`)
- Publier texte + image (`POST /posts/`)
- Liker / retirer un like (`POST /posts/{id}/like`)
- Commenter (`POST /posts/{id}/comments`)
- Profil / déconnexion via lien **Profil**

## Hors ligne

- Assets statiques mis en cache par le Service Worker
- API : stratégie réseau d'abord ; en offline, message « Serveur déconnecté »
- Mode démo Docker offline : `OPENAI_MOCK=true` (coach IA en fallback)

## Références

- [PWA 2026 — installabilité](https://picovert.com/en/blog/pwa-guide-2026)
- EN 301 549 / WCAG 2.1 : labels, `aria-*` sur le feed et la connexion
