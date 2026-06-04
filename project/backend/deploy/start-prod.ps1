param(
  [string]$EnvFile = "..\\.env.prod"
)

$ErrorActionPreference = "Stop"

docker compose `
  --env-file $EnvFile `
  -f ..\\docker-compose.yml `
  -f ..\\docker-compose.prod.yml `
  up -d --build
