"""
HealthAI Coach — Traduction des instructions_en -> instructions_fr
Ecrase le contenu actuel de instructions_fr (qui est une copie de l'anglais)
par une vraie traduction francaise.

Usage :
    python translate_instructions_fr.py
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
    raise RuntimeError("DATABASE_URL non defini dans .env")


def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )


print("Connexion a Supabase...")
conn = get_connection()
cur = conn.cursor()

# Recupere les lignes ou instructions_fr est identique a instructions_en
# (= pas encore traduit, juste une copie du SQL)
cur.execute("""
    SELECT id, instructions
    FROM exercises
    WHERE instructions IS NOT NULL
      AND instructions != ''
      AND (instructions_fr IS NULL OR instructions_fr = '')
    ORDER BY id
""")
rows = cur.fetchall()
total = len(rows)
print(f"{total} instructions a traduire.")

if total == 0:
    print("Rien a faire — instructions_fr est deja traduit.")
    cur.close()
    conn.close()
    sys.exit(0)

translator = GoogleTranslator(source='en', target='fr')
errors = 0
translated = 0

for i, (exercise_id, text_en) in enumerate(rows, start=1):
    try:
        # Google Translate limite a 5000 caracteres par requete
        text_fr = translator.translate(text_en[:4900])

        # Reconnexion si besoin
        if conn.closed:
            conn = get_connection()
            cur = conn.cursor()

        cur.execute(
            "UPDATE exercises SET instructions_fr = %s WHERE id = %s",
            (text_fr, exercise_id)
        )
        translated += 1

        if i % 20 == 0:
            conn.commit()
            print(f"  {i}/{total} traduits...", flush=True)

        time.sleep(0.08)

    except (psycopg2.InterfaceError, psycopg2.OperationalError):
        print(f"  Reconnexion... (id={exercise_id})", flush=True)
        try:
            conn = get_connection()
            cur = conn.cursor()
            text_fr_retry = translator.translate(text_en[:4900])
            cur.execute(
                "UPDATE exercises SET instructions_fr = %s WHERE id = %s",
                (text_fr_retry, exercise_id)
            )
            translated += 1
        except Exception as e2:
            errors += 1
            print(f"  [ERREUR] id={exercise_id} : {e2}")

    except Exception as e:
        errors += 1
        print(f"  [ERREUR] id={exercise_id} : {e}")

try:
    conn.commit()
except Exception:
    pass

cur.close()
conn.close()

print(f"\nTermine : {translated}/{total} instructions traduites. {errors} erreurs.")
