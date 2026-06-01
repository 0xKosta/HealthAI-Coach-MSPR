#!/usr/bin/env python3
"""
HealthAI Coach — Sauvegarde et restauration PostgreSQL (MSPR 3)

Prérequis : pg_dump et pg_restore dans le PATH
  - Windows : installer PostgreSQL client ou « psql » via winget/choco
  - macOS : brew install libpq && brew link --force libpq

Usage :
    python scripts/backup_db.py backup
    python scripts/backup_db.py restore backups/healthai_YYYYMMDD_HHMMSS.dump
    python scripts/backup_db.py restore --latest
    python scripts/backup_db.py list

Lit DATABASE_URL depuis .env (même variable que l'ETL / l'API).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BACKUPS_DIR = ROOT / "backups"

SQLALCHEMY_PREFIXES = (
    "postgresql+psycopg2://",
    "postgresql+asyncpg://",
    "postgres+psycopg2://",
)


def _pg_uri_from_env() -> str:
    load_dotenv(ROOT / ".env")
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        sys.exit(
            "ERREUR : DATABASE_URL absent. Copiez env.example vers .env et renseignez Supabase."
        )
    for prefix in SQLALCHEMY_PREFIXES:
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix) :]
    if url.startswith(("postgresql://", "postgres://")):
        return url.replace("postgres://", "postgresql://", 1)
    sys.exit(f"ERREUR : format DATABASE_URL non reconnu : {url[:40]}...")


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        sys.exit(
            f"ERREUR : '{name}' introuvable.\n"
            "Installez les outils client PostgreSQL (pg_dump / pg_restore).\n"
            "Windows : https://www.postgresql.org/download/windows/\n"
            "          ou : winget install PostgreSQL.PostgreSQL\n"
            "macOS   : brew install libpq"
        )
    return path


def cmd_backup() -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = BACKUPS_DIR / f"healthai_{ts}.dump"
    uri = _pg_uri_from_env()
    pg_dump = _require_tool("pg_dump")

    print(f"Sauvegarde vers {out} ...")
    subprocess.run(
        [pg_dump, "-Fc", "--no-owner", "--no-acl", "-f", str(out), uri],
        check=True,
    )
    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"OK — {out.name} ({size_mb:.2f} Mo)")
    return out


def _resolve_dump_file(arg: str | None, latest: bool) -> Path:
    if latest:
        dumps = sorted(BACKUPS_DIR.glob("healthai_*.dump"), key=lambda p: p.stat().st_mtime)
        if not dumps:
            sys.exit(f"ERREUR : aucun fichier dans {BACKUPS_DIR}")
        return dumps[-1]
    if not arg:
        sys.exit("ERREUR : indiquez un fichier .dump ou --latest")
    path = Path(arg)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        sys.exit(f"ERREUR : fichier introuvable : {path}")
    return path


def cmd_restore(dump: Path, clean: bool) -> None:
    uri = _pg_uri_from_env()
    pg_restore = _require_tool("pg_restore")

    print(f"Restauration depuis {dump} ...")
    if clean:
        print(
            "Mode --clean : suppression des objets existants avant restauration "
            "(schéma public concerné par le dump)."
        )

    cmd = [
        pg_restore,
        "-d",
        uri,
        "--no-owner",
        "--no-acl",
        "--if-exists",
        "-v",
    ]
    if clean:
        cmd.append("--clean")
    cmd.append(str(dump))

    # pg_restore peut retourner des warnings (objets déjà absents) → code 1
    result = subprocess.run(cmd)
    if result.returncode not in (0, 1):
        sys.exit(result.returncode)
    print("Restauration terminée.")


def cmd_list() -> None:
    if not BACKUPS_DIR.exists():
        print("(aucun dossier backups)")
        return
    dumps = sorted(BACKUPS_DIR.glob("healthai_*.dump"), key=lambda p: p.stat().st_mtime)
    if not dumps:
        print("(aucune sauvegarde)")
        return
    for p in dumps:
        mb = p.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {p.name}  —  {mb:.2f} Mo  —  {mtime}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup / restore PostgreSQL HealthAI Coach")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("backup", help="Créer une sauvegarde .dump dans backups/")

    p_restore = sub.add_parser("restore", help="Restaurer depuis un fichier .dump")
    p_restore.add_argument("file", nargs="?", help="Chemin vers healthai_*.dump")
    p_restore.add_argument(
        "--latest",
        action="store_true",
        help="Utiliser la sauvegarde la plus récente",
    )
    p_restore.add_argument(
        "--no-clean",
        action="store_true",
        help="Ne pas supprimer les objets avant restauration (fusion partielle)",
    )

    sub.add_parser("list", help="Lister les sauvegardes disponibles")

    args = parser.parse_args()

    if args.command == "backup":
        cmd_backup()
    elif args.command == "list":
        cmd_list()
    elif args.command == "restore":
        dump = _resolve_dump_file(args.file, args.latest)
        cmd_restore(dump, clean=not args.no_clean)


if __name__ == "__main__":
    main()
