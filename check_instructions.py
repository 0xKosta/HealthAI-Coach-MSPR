import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("DATABASE_URL").replace("postgresql+psycopg2://", "postgresql://")
conn = psycopg2.connect(url)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM exercises")
print("Total exercices:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM exercises WHERE instructions_fr IS NULL")
print("instructions_fr NULL:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM exercises WHERE instructions IS NULL OR instructions = ''")
print("instructions (EN) vide/NULL:", cur.fetchone()[0])

cur.execute("""
    SELECT id, LEFT(instructions,50), instructions_fr
    FROM exercises WHERE instructions_fr IS NULL LIMIT 10
""")
print("\n--- Lignes avec instructions_fr NULL ---")
for row in cur.fetchall():
    print(f"  id={row[0]} | instructions='{row[1]}' | instructions_fr={row[2]}")

conn.close()
