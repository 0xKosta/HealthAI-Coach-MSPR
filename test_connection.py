# test_connection.py
# Fichier temporaire pour tester la connexion Supabase
# À supprimer après validation

from api.database import engine

try:
    with engine.connect() as conn:
        print("✅ Connexion Supabase OK")
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    print("Vérifie que DATABASE_URL est bien défini dans ton fichier .env")
