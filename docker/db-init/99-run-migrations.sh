#!/bin/bash
set -e
echo "Applying additive migrations..."
for f in $(ls /migrations/*.sql 2>/dev/null | sort); do
  echo "  -> $f"
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$f"
done
echo "Migrations done."
