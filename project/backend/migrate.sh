#!/usr/bin/env bash
set -euo pipefail

case "${1:-}" in
  generate)
    alembic revision --autogenerate -m "${2:-init}"
    ;;
  migrate)
    alembic upgrade head
    ;;
  *)
    echo "Usage:"
    echo "  ./migrate.sh generate \"init\"   # alembic revision --autogenerate -m \"init\""
    echo "  ./migrate.sh migrate            # alembic upgrade head"
    exit 1
    ;;
esac
