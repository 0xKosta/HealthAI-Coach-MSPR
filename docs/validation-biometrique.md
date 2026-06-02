# Validation biométrique du profil utilisateur

Documentation des règles métier appliquées au profil santé (`users`) et à l'accès aux fonctionnalités IA.

---

## 1. Règles métier

| Champ | Plage autorisée | Notes |
|-------|-----------------|-------|
| `age` | 18 – 100 ans | Null autorisé à l'inscription ; obligatoire pour l'IA |
| `height_cm` | 90 – 230 cm | Inclusif pour les personnes de petite taille |
| `weight_kg` | 20 – 300 kg | |
| `bmi` | 10 – 80 | **Calculé côté serveur** : `weight_kg / (height_m)²` — non modifiable manuellement |

**Justification MVP :** âge minimum 18 ans (cible adultes), plages hautes pour rejeter les saisies aberrantes.

---

## 2. Back-end

### Module central

`api/biometrics.py` — constantes, `compute_bmi()`, validateurs unitaires, `validate_user_biometrics()`, `collect_profile_issues()`.

### Schémas Pydantic

| Schéma | Rôle |
|--------|------|
| `_UserBiometricInput` | Validation stricte à l'écriture (POST/PUT) |
| `UserCreate` / `ProfileUpdateRequest` | Héritent de l'input |
| `UserResponse` | Lecture tolérante + champ `profile_issues: list[str]` |

Les données **legacy** en base (ex. `age = 0`) restent lisibles en GET ; les anomalies sont listées dans `profile_issues` sans erreur 500.

### Routes concernées

| Route | Comportement |
|-------|----------------|
| `POST /users/` | Validation + IMC recalculé |
| `PUT /users/{id}` | Idem |
| `PUT /auth/me/profile` | Idem pour le compte connecté |
| `POST /coach/*` | Refus **400** si profil incomplet ou biométrie invalide |

Erreurs de validation sur `/users` et `/auth/me/profile` : **HTTP 400** avec `detail` en français (handler dans `api/main.py`).

### Base de données

- `db/init.sql` — contraintes `CHECK` alignées sur les bornes ci-dessus
- Migration additive : `db/migrations/004_users_biometric_checks.sql`

```bash
psql -h <host> -U <user> -d <dbname> -f db/migrations/004_users_biometric_checks.sql
```

Autres migrations profil : `002_users_age_nullable.sql` (âge optionnel à l'inscription).

---

## 3. Front-end

### Composables

| Fichier | Rôle |
|---------|------|
| `useBiometricValidation.js` | Bornes, validation formulaire, `parseApiErrorDetail()` |
| `useProfileCompletion.js` | `blocksAiFeatures()`, `showProfileWelcomeBoard()`, `getProfileIssues()` (API + repli client) |

### Comportement UX

- **Profil incomplet** (champ manquant) ou **invalide** (`profile_issues` / validation locale) → fonctionnalités IA verrouillées
- **Dashboard** : bandeau « Bienvenue » ou « Profil à corriger » avec liste des erreurs
- **Nutrition / Entraînement / Tendances** : `ProfileAiGate` avec détail des problèmes
- **ProfileEditView** : min/max HTML, erreurs par champ, blocage à l'envoi

### Détection locale (repli)

Si l'API ne renvoie pas `profile_issues`, le front recalcule les anomalies (ex. âge 0) via les mêmes bornes que le serveur — évite un déblocage intempestif du conseil IA.

---

## 4. Tests

```bash
pytest tests/test_biometrics.py tests/test_routes.py -v
```

- Tests unitaires sur `api/biometrics.py` et `UserResponse` (données legacy)
- Tests API : création/mise à jour invalides → 400, IMC calculé à la création

---

## 5. Exemple de réponse GET

```json
{
  "id": 974,
  "name": "User_000974",
  "age": 0,
  "weight_kg": 75.0,
  "height_cm": 180.0,
  "bmi": 23.15,
  "goal": "sleep_improvement",
  "profile_issues": [
    "L'âge doit être compris entre 18 et 100 ans."
  ]
}
```

---

## 6. Fichiers modifiés (référence)

```
api/biometrics.py
api/schemas.py
api/models.py
api/main.py
api/routers/users.py
api/routers/auth.py
api/routers/coach.py
db/init.sql
db/migrations/004_users_biometric_checks.sql
front-end/src/composables/useBiometricValidation.js
front-end/src/composables/useProfileCompletion.js
front-end/src/components/ui/ProfileAiGate.vue
front-end/src/components/ui/ProfileDataWarning.vue
front-end/src/views/ProfileEditView.vue
front-end/src/views/DashboardView.vue
front-end/src/views/NutritionView.vue
front-end/src/views/WorkoutView.vue
front-end/src/views/TrendsView.vue
tests/test_biometrics.py
tests/conftest.py
```

Après modification des schémas API : `python export_openapi.py`
