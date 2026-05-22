# export_openapi.py
# Lance ce script une fois pour générer docs/openapi.json
# Usage : python export_openapi.py

import json
from api.main import app

with open("docs/openapi.json", "w", encoding="utf-8") as f:
    json.dump(app.openapi(), f, ensure_ascii=False, indent=2)

print("docs/openapi.json généré.")