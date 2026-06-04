# Supervision et observabilité (MSPR3)

## Stack

| Outil | Rôle | Port local |
|-------|------|------------|
| Prometheus | Collecte métriques | 9090 |
| Grafana | Visualisation | 3001 |
| FastAPI Instrumentator | Exposition `/metrics` | 8000 |

Configuration Prometheus : [`docker/prometheus/prometheus.yml`](../docker/prometheus/prometheus.yml).

## Liste des données collectées

### Métriques HTTP (Prometheus — endpoint `/metrics`)

| Métrique | Type | Description |
|----------|------|-------------|
| `http_requests_total` | Counter | Nombre total de requêtes HTTP par method, status, handler |
| `http_request_duration_seconds` | Histogram | Latence des requêtes (buckets) |
| `http_request_size_bytes` | Summary | Taille des requêtes entrantes |
| `http_response_size_bytes` | Summary | Taille des réponses |

Labels typiques : `method`, `status`, `handler` (route FastAPI normalisée).

### Santé applicative

| Endpoint | Donnée |
|----------|--------|
| `GET /health` | `status`, `service` — probe liveness |

### Logs

| Source | Contenu |
|--------|---------|
| Conteneur `api` | Logs uvicorn/FastAPI (stdout Docker) |
| Conteneur `db` | Logs PostgreSQL |
| Pipeline ETL | GitHub Actions + `logs/` en cas d'échec |

### Métriques métier (extension possible)

Non exportées Prometheus aujourd'hui ; suivies en base :

- Nombre de publications (`posts`)
- Likes / commentaires (`post_likes`, `post_comments`)
- Requêtes IA (`ai_requests`) — quotas et historique

### Front-end (PWA)

| Signal | Mécanisme |
|--------|-----------|
| API joignable | `GET /health` polling (`apiStatusStore`) |
| Erreurs réseau | Intercepteur Axios → écran déconnecté |

## Alertes de démonstration (jury)

Pour la soutenance, illustrer :

1. Grafana connecté à Prometheus
2. Pic de trafic après navigation sur le feed
3. Code HTTP 4xx/5xx visibles sur `http_requests_total`

## Amélioration continue

- Alertmanager + règles Prometheus (latence > 2s, 5xx > seuil)
- Export logs centralisés (ELK / Loki)
- Dashboard Grafana dédié « Feed social » et « Coach IA »
