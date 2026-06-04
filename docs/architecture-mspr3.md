# Architecture système — MSPR3

## Vue d'ensemble

```mermaid
flowchart TB
  subgraph client [Clients]
    PWA[PWA Vue 3 Vite]
  end
  subgraph docker [Docker Compose]
    NGINX[nginx front :8080]
    API[FastAPI :8000]
    PG[(PostgreSQL)]
    PROM[Prometheus :9090]
    GRAF[Grafana :3001]
  end
  subgraph external [Externe optionnel]
    OPENAI[OpenAI API]
    SUPA[Supabase Cloud]
  end
  PWA --> NGINX
  PWA --> API
  NGINX --> API
  API --> PG
  API -.-> OPENAI
  PROM --> API
  GRAF --> PROM
  API -.-> SUPA
```

## Composants

| Composant | Technologie | Responsabilité |
|-----------|-------------|----------------|
| PWA | Vue 3, Pinia, Tailwind | UI coaching + feed social |
| API | FastAPI, SQLAlchemy 2 | REST, JWT, upload médias |
| BDD | PostgreSQL 16 | Persistance |
| IA | OpenAI GPT-4o / mini | Coach (mock offline possible) |
| ETL | pandas, GitHub Actions | Jeux de données Kaggle |
| Monitoring | Prometheus + Grafana | Métriques HTTP |

## Modèle de données — social

```mermaid
erDiagram
  user_auth ||--o{ posts : author
  posts ||--o{ post_likes : ""
  user_auth ||--o{ post_likes : user
  posts ||--o{ post_comments : ""
  user_auth ||--o{ post_comments : author
  user_auth ||--o| users : profile
```

Tables clés : `user_auth`, `posts`, `post_likes`, `post_comments` (migration `007`).

## Déploiement

- **Démo locale** : Docker Compose profils `full` / `offline` / `performance`
- **Développement** : Supabase + uvicorn + `npm run dev`
- **CI** : pytest + build + build images

## Schéma réseau (démo)

```
Navigateur → :8080 (nginx) → fichiers statiques PWA
Navigateur → :8000 (API) → PostgreSQL :5432
Prometheus → :8000/metrics
```

## Sécurité

- Authentification JWT (bcrypt, HS256)
- CORS configurable
- Upload médias : types MIME whitelist, 50 Mo max
- RGPD : `DELETE /auth/me` cascade

Voir aussi [`modele-donnees.md`](modele-donnees.md) et [`deploiement.md`](deploiement.md).
