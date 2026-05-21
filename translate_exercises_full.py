"""
HealthAI Coach — Traduction complète EN -> FR de la table exercises
Ajoute les colonnes FR si elles n'existent pas, puis les remplit.

Colonnes traitées :
  - level_fr        : traduction fixe (3 valeurs seulement)
  - type_fr         : traduction par valeurs distinctes
  - muscle_group_fr : traduction par valeurs distinctes
  - equipment_fr    : traduction par valeurs distinctes
  - name_fr         : traduction ligne par ligne

Usage :
    python translate_exercises_full.py
"""

import os
import sys
import time
import psycopg2
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg2://", "postgresql://")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL non défini dans .env")

def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )

print("Connexion à Supabase...")
conn = get_connection()
cur = conn.cursor()

# ─── 1. Ajout des colonnes FR si elles n'existent pas ──────────────────────────

new_columns = [
    ("name_fr",         "VARCHAR(200)"),
    ("type_fr",         "VARCHAR(100)"),
    ("muscle_group_fr", "VARCHAR(100)"),
    ("equipment_fr",    "VARCHAR(100)"),
    ("level_fr",        "VARCHAR(50)"),
]

print("\n[1/5] Vérification et ajout des colonnes FR...")
for col_name, col_type in new_columns:
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = 'exercises'
          AND column_name  = %s
    """, (col_name,))
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE exercises ADD COLUMN {col_name} {col_type}")
        print(f"  + Colonne '{col_name}' ajoutée.")
    else:
        print(f"  ✓ Colonne '{col_name}' déjà présente.")

conn.commit()

# ─── 2. level_fr : traduction fixe (pas besoin d'API) ─────────────────────────

print("\n[2/5] Traduction de level_fr (valeurs fixes)...")
level_map = {
    'beginner':     'débutant',
    'intermediate': 'intermédiaire',
    'expert':       'expert',
}
for en, fr in level_map.items():
    cur.execute("""
        UPDATE exercises SET level_fr = %s
        WHERE level = %s AND (level_fr IS NULL OR level_fr = '')
    """, (fr, en))
conn.commit()
print("  ✓ level_fr rempli.")

# ─── Helper : traduction par valeurs distinctes ────────────────────────────────

def translate_distinct(column_en, column_fr, label):
    """Récupère toutes les valeurs distinctes, les traduit une seule fois, puis UPDATE."""
    print(f"\n[{label}] Traduction de {column_fr} (valeurs distinctes)...")
    cur.execute(f"""
        SELECT DISTINCT {column_en}
        FROM exercises
        WHERE {column_en} IS NOT NULL AND {column_en} != ''
          AND ({column_fr} IS NULL OR {column_fr} = '')
    """)
    distinct_values = [row[0] for row in cur.fetchall()]
    print(f"  {len(distinct_values)} valeur(s) distincte(s) à traduire.")

    translator = GoogleTranslator(source='en', target='fr')
    for value in distinct_values:
        try:
            translated = translator.translate(value)
            cur.execute(f"""
                UPDATE exercises SET {column_fr} = %s
                WHERE {column_en} = %s AND ({column_fr} IS NULL OR {column_fr} = '')
            """, (translated, value))
            print(f"  '{value}' → '{translated}'")
            time.sleep(0.1)
        except Exception as e:
            print(f"  [ERREUR] '{value}' : {e}")
    conn.commit()
    print(f"  ✓ {column_fr} rempli.")

# ─── 3. type_fr ────────────────────────────────────────────────────────────────
translate_distinct("type", "type_fr", "3/5")

# ─── 4. muscle_group_fr ────────────────────────────────────────────────────────
translate_distinct("muscle_group", "muscle_group_fr", "4/5")

# ─── 5. equipment_fr ───────────────────────────────────────────────────────────
translate_distinct("equipment", "equipment_fr", "5/5 (equipment)")

# ─── 6. name_fr : traduction ligne par ligne ───────────────────────────────────

print("\n[+] Traduction de name_fr (ligne par ligne)...")

# Vérifie si la colonne instructions s'appelle 'instructions' ou 'instructions_en'
cur.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'exercises'
      AND column_name IN ('instructions_en', 'instructions')
""")
instr_col = cur.fetchone()
instr_col = instr_col[0] if instr_col else 'instructions_en'

cur.execute("""
    SELECT id, name FROM exercises
    WHERE name IS NOT NULL AND name != ''
      AND (name_fr IS NULL OR name_fr = '')
    ORDER BY id
""")
rows = cur.fetchall()
total = len(rows)
print(f"  {total} exercices à traduire.")

translator = GoogleTranslator(source='en', target='fr')
errors = 0

for i, (exercise_id, name_en) in enumerate(rows, start=1):
    try:
        name_fr = translator.translate(name_en)

        # Reconnexion automatique si la connexion a été coupée
        if conn.closed:
            conn = get_connection()
            cur = conn.cursor()

        cur.execute(
            "UPDATE exercises SET name_fr = %s WHERE id = %s",
            (name_fr, exercise_id)
        )

        if i % 20 == 0:
            conn.commit()
            print(f"  {i}/{total} noms traduits...", flush=True)

        time.sleep(0.05)

    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        # Reconnexion sur coupure réseau
        print(f"  Reconnexion... (id={exercise_id})", flush=True)
        try:
            conn = get_connection()
            cur = conn.cursor()
            name_fr_retry = translator.translate(name_en)
            cur.execute(
                "UPDATE exercises SET name_fr = %s WHERE id = %s",
                (name_fr_retry, exercise_id)
            )
        except Exception as e2:
            errors += 1
            print(f"  [ERREUR] id={exercise_id} : {e2}")

    except Exception as e:
        errors += 1
        print(f"  [ERREUR] id={exercise_id} name='{name_en}' : {e}")

try:
    conn.commit()
except Exception:
    pass
print(f"  ✓ name_fr rempli ({total - errors}/{total} traduits, {errors} erreurs).")

# ─── Résumé final ──────────────────────────────────────────────────────────────

cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(name_fr) AS name_fr,
        COUNT(type_fr) AS type_fr,
        COUNT(muscle_group_fr) AS muscle_group_fr,
        COUNT(equipment_fr) AS equipment_fr,
        COUNT(level_fr) AS level_fr
    FROM exercises
""")
row = cur.fetchone()
print(f"""
─────────────────────────────────────
Résumé final (exercices remplis / total {row[0]})
  name_fr         : {row[1]}
  type_fr         : {row[2]}
  muscle_group_fr : {row[3]}
  equipment_fr    : {row[4]}
  level_fr        : {row[5]}
─────────────────────────────────────
""")

cur.close()
conn.close()
print("Terminé.")
