import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
url = os.getenv("DATABASE_URL").replace("postgresql+psycopg2://", "postgresql://")
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='exercises' AND table_schema='public' ORDER BY ordinal_position")
print([r[0] for r in cur.fetchall()])
conn.close()
