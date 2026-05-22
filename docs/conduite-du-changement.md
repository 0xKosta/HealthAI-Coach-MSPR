# Documentation — Conduite du Changement
## Projet HealthAI Coach — MSPR Bloc 1 & 2

---

## Sommaire

1. [Contexte et périmètre du changement](#1-contexte-et-périmètre-du-changement)
2. [Analyse des impacts](#2-analyse-des-impacts)
3. [Cartographie des parties prenantes](#3-cartographie-des-parties-prenantes)
4. [Plan de communication](#4-plan-de-communication)
5. [Plan de formation](#5-plan-de-formation)
6. [Gestion des résistances](#6-gestion-des-résistances)
7. [Indicateurs de succès (KPIs)](#7-indicateurs-de-succès-kpis)
8. [Planning de déploiement](#8-planning-de-déploiement)
9. [Gestion des risques](#9-gestion-des-risques)
10. [Gouvernance et suivi post-déploiement](#10-gouvernance-et-suivi-post-déploiement)

---

## 1. Contexte et périmètre du changement

### 1.1 Présentation du projet

**HealthAI Coach** est une plateforme numérique de coaching santé personnalisé. Elle repose sur l'exploitation de données réelles issues de sources publiques (Kaggle, GitHub) et sur un moteur d'intelligence artificielle (OpenAI GPT-4o) pour fournir à chaque utilisateur des recommandations adaptées en matière de nutrition, d'entraînement physique et de suivi biométrique.

| Dimension | Détail |
|-----------|--------|
| **Type de projet** | Transformation digitale — introduction d'un outil IA dans le domaine santé/bien-être |
| **Périmètre technique** | Pipeline ETL, base de données PostgreSQL (Supabase), API REST FastAPI, interface web Vue 3 PWA |
| **Périmètre fonctionnel** | Suivi nutritionnel, gestion des entraînements, analyse biométrique, conseil IA personnalisé |
| **Portée organisationnelle** | Équipe projet (4 membres), utilisateurs finaux, responsables pédagogiques |

### 1.2 Pourquoi ce changement ?

L'approche traditionnelle du coaching santé (consultations ponctuelles, journaux papier, tableurs) présente plusieurs limites :

- **Données fragmentées** : aucune vision consolidée de l'alimentation, de l'activité physique et des métriques biométriques.
- **Manque de personnalisation** : les recommandations génériques ne tiennent pas compte du profil individuel (âge, IMC, niveau d'expérience, objectif).
- **Réactivité faible** : l'analyse manuelle des données est lente et sujette aux biais humains.
- **Accessibilité limitée** : les outils existants nécessitent souvent l'intervention d'un professionnel de santé.

HealthAI Coach répond à ces enjeux en proposant une solution **automatisée, intelligente, accessible 24h/24** via une PWA installable sur tout appareil.

### 1.3 Situation actuelle vs. situation cible

| Critère | Avant (AS-IS) | Après (TO-BE) |
|---------|---------------|---------------|
| Collecte des données | Manuelle, fragmentée | Automatisée via pipeline ETL quotidien |
| Stockage | Fichiers locaux, tableurs | Base PostgreSQL centralisée (Supabase) |
| Analyse | Humaine, ponctuelle | Temps réel + IA (GPT-4o) |
| Conseil nutritionnel | Générique | Personnalisé selon le profil et l'historique |
| Suivi activité physique | Journal papier ou application tierce | Tableau de bord intégré avec graphiques |
| Accessibilité | Limitée (PC, heures ouvrées) | Omnicanal — PWA installable, mobile-first |
| Analyse photo repas | Impossible | Détection visuelle des macronutriments (IA vision) |

---

## 2. Analyse des impacts

### 2.1 Impacts organisationnels

| Domaine impacté | Nature de l'impact | Niveau |
|-----------------|--------------------|--------|
| Processus de suivi santé | Transformation complète du flux de collecte et d'analyse | **Fort** |
| Rôles et responsabilités | Introduction de rôles DevOps/Data pour maintenir l'ETL et la BDD | **Moyen** |
| Culture de travail | Passage à une culture data-driven et IA-assisted | **Moyen** |
| Outils utilisés | Remplacement d'outils disparates par une plateforme unique | **Fort** |

### 2.2 Impacts techniques

| Composant | Impact |
|-----------|--------|
| **Pipeline ETL** | Automatisation quotidienne via GitHub Actions — supervision requise |
| **Base de données** | Schéma évolutif (7 tables) — migrations à gérer en cas d'évolution |
| **API FastAPI** | Nouveau point d'intégration — documentation OpenAPI disponible |
| **Frontend Vue 3 PWA** | Nouvelle interface utilisateur — courbe d'apprentissage modérée |
| **Intégration OpenAI** | Dépendance à un service tiers payant — gestion des quotas et coûts |

### 2.3 Impacts sur les données

- **Qualité** : les données Kaggle sont nettoyées et validées lors de l'ETL ; un rapport qualité est généré à chaque run.
- **Confidentialité** : les profils utilisateurs contiennent des données de santé sensibles (poids, BMI, BPM) — conformité RGPD à assurer.
- **Intégrité** : l'ETL est idempotent (TRUNCATE + reload) — risque de perte temporaire de données lors d'un run raté.
- **Disponibilité** : dépendance à Supabase (SaaS) — SLA à surveiller.

---

## 3. Cartographie des parties prenantes

### 3.1 Identification des parties prenantes

| Partie prenante | Rôle | Intérêt | Influence |
|-----------------|------|---------|-----------|
| **Équipe projet** (4 membres) | Développeurs / Propriétaires du changement | Très élevé | Très élevée |
| **Responsables pédagogiques MSPR** | Commanditaires / Évaluateurs | Élevé | Élevée |
| **Utilisateurs finaux** (sportifs, personnes en reconversion alimentaire) | Bénéficiaires directs | Élevé | Moyenne |
| **Administrateurs système** | Maintenance infrastructure Supabase + CI | Moyen | Élevée |
| **OpenAI (prestataire IA)** | Fournisseur du moteur IA | Faible | Élevée |
| **Kaggle / ExerciseDB** | Fournisseurs de données | Faible | Moyenne |

### 3.2 Matrice Intérêt / Influence

```
         INFLUENCE
           Élevée │ Responsables pédagogiques │ Équipe projet
                  │ Administrateurs système   │
           ───────┼───────────────────────────┼──────────────
           Faible │ OpenAI, Kaggle            │ Utilisateurs
                  └───────────────────────────┴──────────────
                        Faible                   Élevé
                                       INTÉRÊT
```

**Stratégies par quadrant :**
- **Fort intérêt + forte influence** (équipe projet) : impliquer activement, décisions collégiales.
- **Fort intérêt + faible influence** (utilisateurs) : consulter, recueillir les retours, intégrer dans les sprints.
- **Faible intérêt + forte influence** (responsables pédagogiques, admins) : tenir informés régulièrement, impliquer sur les jalons clés.
- **Faible intérêt + faible influence** (fournisseurs externes) : surveiller, gérer les dépendances contractuelles.

### 3.3 Analyse RACI — Activités clés du changement

| Activité | Équipe projet | Resp. pédagogiques | Admins système | Utilisateurs |
|----------|--------------|--------------------|----------------|--------------|
| Définition des besoins | **R/A** | C | I | C |
| Développement ETL | **R/A** | I | C | — |
| Configuration Supabase | **R/A** | I | **C** | — |
| Développement API | **R/A** | I | I | — |
| Développement Frontend | **R/A** | I | I | C |
| Tests et validation | **R/A** | C | C | **C** |
| Déploiement production | **R/A** | I | **C** | I |
| Communication/formation | **R/A** | I | I | **R** |
| Suivi post-déploiement | **R/A** | C | C | C |

*R = Responsable, A = Approbateur, C = Consulté, I = Informé*

---

## 4. Plan de communication

### 4.1 Principes directeurs

- **Transparence** : partager l'avancement réel, y compris les difficultés rencontrées.
- **Régularité** : communication planifiée pour éviter les zones d'incertitude.
- **Adaptation** : adapter le message et le canal à chaque public.
- **Bidirectionnalité** : intégrer les retours des utilisateurs dans le cycle de développement.

### 4.2 Plan de communication détaillé

| Message | Cible | Canal | Fréquence | Responsable |
|---------|-------|-------|-----------|-------------|
| Lancement du projet — vision et objectifs | Toutes parties prenantes | Réunion kick-off + email | Unique (J0) | Chef de projet |
| Avancement des développements | Équipe projet | Daily stand-up / Réunion hebdo | Hebdomadaire | Équipe |
| Jalons atteints (MVP, démo, prod) | Responsables pédagogiques | Email + présentation | À chaque jalon | Chef de projet |
| Disponibilité des nouvelles fonctionnalités | Utilisateurs finaux | Notification in-app, email | À chaque release | Développeur Frontend |
| Incidents / maintenances planifiées | Utilisateurs + Admins | Email + bannière in-app | Ad hoc | Administrateur |
| Rapport de qualité ETL | Équipe + Admins | Rapport automatique CI/CD | Quotidien (automatisé) | Pipeline CI |
| Bilan mensuel — KPIs | Toutes parties prenantes | Dashboard Metabase + rapport | Mensuel | Data Analyst |

### 4.3 Messages clés par public

**Pour les utilisateurs finaux :**
> « HealthAI Coach vous offre un coach santé personnalisé accessible à tout moment. En quelques secondes, obtenez des conseils nutritionnels, un programme d'entraînement sur mesure et une analyse de vos tendances biométriques — tout cela grâce à l'intelligence artificielle. »

**Pour les responsables pédagogiques :**
> « Le projet démontre la maîtrise de l'ensemble de la chaîne de valeur data : collecte, transformation, modélisation, exposition via API et visualisation. Il intègre les bonnes pratiques DevOps (CI/CD, tests automatisés) et une approche éthique des données de santé. »

**Pour l'équipe technique :**
> « L'architecture modulaire (ETL / BDD / API / Frontend) garantit l'évolutivité. Chaque composant est testable et déployable indépendamment. La documentation technique (OpenAPI, modèle de données, requêtes Metabase) assure la maintenabilité. »

---

## 5. Plan de formation

### 5.1 Besoins en formation identifiés

| Public | Besoin | Niveau actuel | Objectif |
|--------|--------|--------------|---------|
| Utilisateurs finaux | Utilisation de l'interface web/PWA | Variable (novice à avancé) | Autonomie complète sur les 5 modules |
| Administrateurs système | Gestion Supabase, surveillance CI/CD, gestion des secrets GitHub | Intermédiaire | Maintenance autonome |
| Nouveaux développeurs (onboarding) | Architecture du projet, conventions de code, déploiement local | Débutant | Contribution active en < 2 jours |

### 5.2 Programme de formation — Utilisateurs finaux

**Module 1 — Prise en main (30 min)**
- Installation de la PWA sur mobile/desktop
- Création et configuration du profil utilisateur
- Navigation dans le dashboard principal

**Module 2 — Nutrition (45 min)**
- Saisie d'un journal alimentaire
- Analyse photo d'un repas (fonctionnalité IA vision)
- Interprétation des macronutriments et conseils générés

**Module 3 — Entraînement (45 min)**
- Génération d'un programme hebdomadaire personnalisé
- Consultation du catalogue d'exercices (filtres, GIFs, vidéos)
- Enregistrement d'une séance

**Module 4 — Suivi biométrique (30 min)**
- Saisie des métriques (poids, sommeil, BPM)
- Lecture des graphiques de tendances (ApexCharts)
- Demande d'analyse IA sur 30 jours

**Module 5 — Coach IA (20 min)**
- Formulation d'une demande de conseil
- Compréhension des recommandations générées
- Limites et bon usage de l'IA (non-substitution à un professionnel de santé)

### 5.3 Programme de formation — Administrateurs système

| Thème | Durée | Support |
|-------|-------|---------|
| Architecture globale du projet | 1h | Diagramme d'architecture + README |
| Configuration Supabase (init.sql, secrets) | 1h30 | Guide `docs/modele-donnees.md` + SQL Editor |
| Surveillance pipeline ETL (GitHub Actions) | 1h | `.github/workflows/etl.yml` commenté |
| Gestion des incidents ETL (logs, artefacts) | 1h | Procédure de reprise sur incident |
| Rotation des secrets et clés API | 30 min | Checklist sécurité |

### 5.4 Guide d'onboarding — Nouveaux développeurs

```markdown
Jour 1 — Matin (3h)
├── Lecture du README principal et du README frontend
├── Clonage du dépôt + configuration de l'environnement (.env depuis env.example)
├── Installation des dépendances Python (pip install -r requirements.txt)
└── Lancement et exploration de l'API (uvicorn + Swagger UI)

Jour 1 — Après-midi (3h)
├── Lancement du frontend (npm install && npm run dev)
├── Exploration des 5 vues
└── Lecture de docs/openapi.json et docs/modele-donnees.md

Jour 2 — Matin (3h)
├── Exécution des tests (pytest tests/ -v --cov)
├── Lecture du pipeline ETL (etl/pipeline.py)
└── Compréhension du schéma BDD (db/init.sql)

Jour 2 — Après-midi (3h)
├── Premier ticket de contribution (bug fix ou amélioration mineure)
└── Code review avec un membre de l'équipe
```

---

## 6. Gestion des résistances

### 6.1 Résistances anticipées

| Résistance | Public | Cause probable | Stratégie de réponse |
|------------|--------|----------------|----------------------|
| « Je ne fais pas confiance à l'IA pour mes données de santé » | Utilisateurs finaux | Manque de transparence sur le traitement des données | Publier une politique de confidentialité claire, expliquer que l'IA assiste sans remplacer un professionnel |
| « L'outil est trop complexe à utiliser » | Utilisateurs peu technophiles | Interface perçue comme technique | UX simplifiée, tutoriels vidéo intégrés, mode guidé |
| « Les données sources ne sont pas fiables » | Responsables pédagogiques | Questions sur la qualité des données Kaggle | Présenter les rapports qualité ETL, documenter les règles de transformation |
| « Le pipeline ETL peut corrompre la base » | Administrateurs | Opération TRUNCATE idempotente risquée | Mettre en place des sauvegardes Supabase avant chaque run, fenêtres de maintenance définies |
| « Dépendance à OpenAI — et si le service est indisponible ? » | Équipe technique | Risque de disponibilité d'un tiers | Implémenter un fallback (message d'erreur gracieux, mode dégradé sans IA) |
| « Les coûts OpenAI peuvent exploser » | Responsables projet | Facturation à l'usage | Mise en place de limites de dépenses dans le tableau de bord OpenAI, quotas par utilisateur |

### 6.2 Approche de gestion du changement

La conduite du changement s'appuie sur le **modèle ADKAR** :

| Phase ADKAR | Actions mises en œuvre |
|-------------|------------------------|
| **A** — Awareness (Prise de conscience) | Réunion de lancement, email de présentation, démo vidéo |
| **D** — Desire (Désir de changement) | Mise en avant des bénéfices concrets (gain de temps, personnalisation), beta-test avec utilisateurs pilotes |
| **K** — Knowledge (Connaissance) | Plan de formation (cf. section 5), documentation technique complète |
| **A** — Ability (Capacité) | Support utilisateur (FAQ, guide de démarrage rapide), environnement de test sandbox |
| **R** — Reinforcement (Ancrage) | Suivi des KPIs, retours utilisateurs intégrés dans les sprints, communication des succès |

---

## 7. Indicateurs de succès (KPIs)

### 7.1 KPIs techniques

| Indicateur | Cible | Fréquence de mesure |
|------------|-------|---------------------|
| Taux de succès du pipeline ETL | ≥ 95 % des runs sans erreur | Quotidien (GitHub Actions) |
| Couverture de tests automatisés | ≥ 80 % (actuellement 73 %) | À chaque push |
| Temps de réponse API (p95) | < 500 ms (hors appels IA) | Hebdomadaire |
| Disponibilité de l'API | ≥ 99 % | Mensuel |
| Temps de réponse coach IA | < 5 secondes | Hebdomadaire |

### 7.2 KPIs d'adoption

| Indicateur | Cible (J+30) | Cible (J+90) |
|------------|--------------|--------------|
| Nombre d'utilisateurs actifs | ≥ 10 | ≥ 50 |
| Taux d'installation de la PWA | ≥ 30 % des visiteurs | ≥ 50 % |
| Nombre de conseils IA générés/semaine | ≥ 20 | ≥ 100 |
| Taux de retour sur l'application (J+7) | ≥ 40 % | ≥ 60 % |
| Nombre d'analyses photo repas/semaine | ≥ 5 | ≥ 30 |

### 7.3 KPIs qualité des données

| Indicateur | Cible |
|------------|-------|
| Taux de complétude des profils utilisateurs | ≥ 90 % |
| Taux d'anomalies détectées par l'ETL | < 5 % des lignes chargées |
| Fraîcheur des données (délai max depuis la source) | ≤ 24 heures |

### 7.4 KPIs satisfaction

| Indicateur | Méthode | Cible |
|------------|---------|-------|
| Score de satisfaction utilisateur (CSAT) | Enquête in-app (J+30, J+90) | ≥ 4/5 |
| Net Promoter Score (NPS) | Enquête email (J+90) | ≥ 30 |
| Taux de complétion des formations | Suivi présentiel/LMS | ≥ 85 % |

---

## 8. Planning de déploiement

### 8.1 Phases du projet

```
Phase 1 — Initialisation (Semaines 1-2)
├── Définition des besoins et architecture
├── Configuration Supabase et schéma BDD (init.sql)
├── Mise en place du dépôt Git et CI/CD (GitHub Actions)
└── Kick-off avec toutes les parties prenantes

Phase 2 — Développement (Semaines 3-8)
├── Sprint 1 (S3-S4) : Pipeline ETL + chargement initial des données
├── Sprint 2 (S5-S6) : API FastAPI — CRUD utilisateurs, nutrition, exercices
├── Sprint 3 (S7-S8) : API coach IA + frontend Vue 3 (Dashboard, Nutrition)
└── Tests unitaires et d'intégration en continu

Phase 3 — Intégration & Tests (Semaines 9-10)
├── Tests end-to-end (API + Frontend)
├── Tests de charge (quota OpenAI, performance Supabase)
├── Correction des écarts de schéma (workout_type, experience_level)
├── Revue de sécurité (secrets, CORS, RGPD)
└── Formation des administrateurs système

Phase 4 — Déploiement & Formation (Semaines 11-12)
├── Déploiement de l'API (Render / Railway / VPS)
├── Déploiement du Frontend (Vercel / Netlify)
├── Formation utilisateurs finaux (pilotes)
└── Communication de lancement

Phase 5 — Suivi & Amélioration (Semaines 13-16)
├── Collecte des retours utilisateurs (J+15, J+30)
├── Analyse des KPIs
├── Corrections bugs et optimisations (patch releases)
└── Bilan de conduite du changement
```

### 8.2 Jalons clés

| Jalon | Date cible | Critère de succès |
|-------|------------|-------------------|
| **M0** — Kick-off | Semaine 1 | Toutes les parties prenantes alignées sur les objectifs |
| **M1** — Données chargées en BDD | Fin semaine 4 | ETL s'exécute sans erreur, données valides dans Supabase |
| **M2** — API fonctionnelle | Fin semaine 6 | Tous les endpoints CRUD testés, couverture ≥ 75 % |
| **M3** — MVP complet | Fin semaine 8 | Coach IA opérationnel, frontend 5 vues navigables |
| **M4** — Validation qualité | Fin semaine 10 | 0 bug critique, schéma BDD cohérent, sécurité validée |
| **M5** — Go Live | Semaine 12 | Application accessible en production, utilisateurs pilotes onboardés |
| **M6** — Bilan J+30 | Semaine 16 | KPIs d'adoption et satisfaction mesurés, plan d'amélioration établi |

---

## 9. Gestion des risques

### 9.1 Registre des risques

| # | Risque | Probabilité | Impact | Score | Mitigation |
|---|--------|-------------|--------|-------|------------|
| R1 | Indisponibilité de l'API OpenAI | Faible | Élevé | **Moyen** | Fallback message d'erreur gracieux, mode dégradé sans IA |
| R2 | Dépassement du quota OpenAI (coût) | Moyen | Moyen | **Moyen** | Limite de dépenses dans le dashboard OpenAI, cache des réponses fréquentes |
| R3 | Échec du pipeline ETL quotidien | Moyen | Élevé | **Élevé** | Alertes GitHub Actions, restauration depuis sauvegarde Supabase, ETL idempotent |
| R4 | Indisponibilité de Supabase | Faible | Très élevé | **Élevé** | Sauvegardes quotidiennes automatiques, monitoring Supabase status page |
| R5 | Fuite de données personnelles de santé | Très faible | Très élevé | **Élevé** | Variables d'environnement pour les secrets, HTTPS, politique RGPD, pas de logs de données sensibles |
| R6 | Suppression d'un dataset Kaggle source | Faible | Élevé | **Moyen** | Archiver les fichiers CSV bruts en dehors de Kaggle, versionnage des données |
| R7 | Rupture de l'API ExerciseDB (GitHub) | Moyen | Moyen | **Moyen** | Snapshot local du fichier JSON, URL de fallback |
| R8 | Résistance des utilisateurs à l'IA | Moyen | Moyen | **Moyen** | Communication transparente, consentement explicite, option de désactivation des conseils IA |
| R9 | Écart de schéma BDD (workout_type / experience_level) | Élevé | Moyen | **Élevé** | Aligner init.sql, models.py et l'ETL en sprint 3 ; tâche prioritaire |
| R10 | Port frontend non documenté correctement (5173 vs 3000) | Élevé | Faible | **Faible** | Corriger le README, fixer le port dans vite.config.js |

### 9.2 Plan de reprise sur incident ETL

```
1. Détection : alerte email GitHub Actions (run failed)
2. Diagnostic : consulter les logs dans l'artefact "logs/" (conservé 7 jours)
3. Identification de la cause :
   ├── Erreur réseau (Kaggle / ExerciseDB) → réessayer manuellement via workflow_dispatch
   ├── Erreur BDD (Supabase) → vérifier la connectivité, quota Supabase
   └── Erreur de transformation → corriger le code ETL, push sur main
4. Restauration : si données corrompues → restaurer depuis sauvegarde Supabase
5. Validation : vérifier l'intégrité via les requêtes Q16/Q17 (queries.sql)
6. Post-mortem : documenter l'incident et mettre à jour ce registre des risques
```

---

## 10. Gouvernance et suivi post-déploiement

### 10.1 Organisation de la gouvernance

| Instance | Composition | Fréquence | Rôle |
|----------|-------------|-----------|------|
| **Comité de pilotage** | Chef de projet + Responsables pédagogiques | Mensuel | Validation des KPIs, arbitrage des priorités |
| **Réunion d'équipe technique** | 4 développeurs | Hebdomadaire | Suivi des développements, gestion des incidents |
| **Revue utilisateurs** | Équipe projet + utilisateurs pilotes | Mensuel (J+30, J+60, J+90) | Collecte des retours, priorisation des améliorations |
| **Revue sécurité** | Chef de projet + Administrateur | Trimestriel | Audit des secrets, permissions, logs d'accès |

### 10.2 Processus d'amélioration continue

```
Cycle mensuel d'amélioration :

Collecte → Analyse → Priorisation → Développement → Déploiement → Mesure
   │                                                                    │
   └────────────────────── Boucle de feedback ─────────────────────────┘
```

**Sources de feedback :**
- Enquêtes de satisfaction in-app (CSAT, NPS)
- Tickets support / signalements bugs
- Métriques d'usage (analytics frontend)
- Rapports qualité ETL automatisés
- Dashboard Metabase (19 requêtes analytiques)

### 10.3 Critères de clôture du projet de changement

Le projet de conduite du changement sera considéré comme **terminé avec succès** lorsque :

- [ ] 100 % des utilisateurs pilotes ont suivi la formation et sont autonomes
- [ ] Les KPIs d'adoption J+90 sont atteints (≥ 50 utilisateurs actifs)
- [ ] Le score de satisfaction CSAT est ≥ 4/5
- [ ] 0 incident critique non résolu en base de données
- [ ] Le pipeline ETL présente un taux de succès ≥ 95 % sur 30 jours consécutifs
- [ ] La documentation technique est complète et à jour (README, OpenAPI, modèle de données)
- [ ] Les écarts de schéma BDD identifiés ont été corrigés et validés
- [ ] Une procédure de maintenance et de mise à jour est formalisée et transmise aux administrateurs

---

## Annexes

### Annexe A — Architecture technique du projet

```
┌─────────────────────────────────────────────────────────────┐
│                      Sources de données                      │
│  Kaggle Nutrition CSV │ Kaggle Gym CSV │ ExerciseDB JSON     │
└──────────────┬────────────────┬────────────────┬────────────┘
               │                │                │
               └────────────────▼────────────────┘
                         ┌──────────────┐
                         │  Pipeline ETL │
                         │ (Python CI/CD)│
                         └──────┬───────┘
                                │
                    ┌───────────▼──────────┐
                    │  PostgreSQL Supabase  │
                    │   (7 tables, index)   │
                    └───────────┬──────────┘
                                │
                    ┌───────────▼──────────┐
                    │    API FastAPI :8000  │
                    │  CRUD + Coach GPT-4o  │
                    └─────────┬────────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
   ┌───────────▼───────────┐    ┌────────────▼────────────┐
   │  Frontend Vue 3 PWA   │    │   Dashboard Metabase     │
   │    (5 vues, :3000)    │    │  (19 requêtes analytics) │
   └───────────────────────┘    └─────────────────────────┘
```

### Annexe B — Glossaire

| Terme | Définition |
|-------|------------|
| **ETL** | Extract, Transform, Load — processus automatisé d'ingestion et de transformation des données |
| **PWA** | Progressive Web App — application web installable comme une app native |
| **ADKAR** | Modèle de conduite du changement (Awareness, Desire, Knowledge, Ability, Reinforcement) |
| **RACI** | Matrice de responsabilités (Responsible, Accountable, Consulted, Informed) |
| **GPT-4o** | Modèle de langage multimodal d'OpenAI utilisé pour le coaching IA |
| **Supabase** | Plateforme de base de données PostgreSQL managée (DBaaS) |
| **CI/CD** | Intégration Continue / Déploiement Continu — automatisation des tests et déploiements |
| **RGPD** | Règlement Général sur la Protection des Données (UE 2016/679) |
| **BMI / IMC** | Body Mass Index — indicateur de corpulence calculé à partir du poids et de la taille |
| **CSAT** | Customer Satisfaction Score — indicateur de satisfaction client |
| **NPS** | Net Promoter Score — indicateur de recommandation |

### Annexe C — Contacts et responsabilités

| Rôle | Responsabilité principale |
|------|--------------------------|
| **Chef de projet** | Pilotage global, communication parties prenantes, validation des jalons |
| **Développeur ETL (Rôle A)** | Pipeline d'ingestion, qualité des données, CI GitHub Actions |
| **Développeur BDD (Rôle B)** | Schéma PostgreSQL, migrations, requêtes Metabase |
| **Développeur API (Rôle C)** | FastAPI, intégration OpenAI, tests automatisés |
| **Développeur Frontend (Rôle D)** | Vue 3 PWA, expérience utilisateur, déploiement frontend |

---

*Document rédigé dans le cadre du projet académique **HealthAI Coach — MSPR Bloc 1 & 2**.*
*Dernière mise à jour : Mai 2026*
