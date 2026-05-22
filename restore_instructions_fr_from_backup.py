"""
Restaure instructions_fr dans Supabase depuis le fichier de sauvegarde JSON.
Correspondance par 'name' (insensible à la casse).

Usage:
    python restore_instructions_fr_from_backup.py
"""

import json
import os
import sys
import psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
load_dotenv()

BACKUP_PATH = r"C:\Users\Jean-Charles\Documents\Cour\MSPR\MSPR_1\exercises_202605211116.json"

DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg2://", "postgresql://")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL non défini dans .env")

print(f"Lecture du backup : {BACKUP_PATH}")
with open(BACKUP_PATH, encoding="utf-8") as f:
    data = json.load(f)

exercises = data["exercises"]
print(f"  → {len(exercises)} exercices dans le backup.")

# Index backup par name (lowercase)
backup_by_name = {
    ex["name"].strip().lower(): ex.get("instructions_fr")
    for ex in exercises
    if ex.get("instructions_fr")
}
print(f"  → {len(backup_by_name)} avec instructions_fr non nulles.")

print("\nConnexion à Supabase...")
conn = psycopg2.connect(DATABASE_URL, keepalives=1, keepalives_idle=30)
cur = conn.cursor()

# Récupérer les exercices en base sans instructions_fr
cur.execute("""
    SELECT id, name FROM exercises
    WHERE instructions_fr IS NULL OR instructions_fr = ''
    ORDER BY id
""")
rows = cur.fetchall()
print(f"  → {len(rows)} exercices sans instructions_fr en base.")

updated = 0
not_found = 0

for exercise_id, name in rows:
    key = name.strip().lower()
    instructions_fr = backup_by_name.get(key)
    if instructions_fr:
        cur.execute(
            "UPDATE exercises SET instructions_fr = %s WHERE id = %s",
            (instructions_fr, exercise_id)
        )
        updated += 1
    else:
        not_found += 1

conn.commit()

print(f"\n✓ Restauration terminée :")
print(f"  - {updated} instructions_fr restaurées depuis le backup")
print(f"  - {not_found} exercices non trouvés dans le backup (seront traduits par le script)")

cur.close()
conn.close()
print("\nTerminé.")
