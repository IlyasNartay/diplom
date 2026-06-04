param(
  [Parameter(Mandatory = $true)][string]$Domain,
  [Parameter(Mandatory = $true)][string]$Email,
  [string]$EnvFile = "..\\.env.prod"
)

$ErrorActionPreference = "Stop"

docker compose `
  --env-file $EnvFile `
  -f ..\\docker-compose.yml `
  -f ..\\docker-compose.prod.yml `
  run --rm certbot certonly `
  --webroot -w /var/www/certbot `
  -d $Domain `
  -m $Email `
  --agree-tos `
  --no-eff-email

docker compose `
  --env-file $EnvFile `
  -f ..\\docker-compose.yml `
  -f ..\\docker-compose.prod.yml `
  restart nginx
