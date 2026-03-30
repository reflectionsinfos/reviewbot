# run_sql_proxy.ps1 - Run Cloud SQL Proxy to connect to the DB from local machine
param (
    [string]$ProjectID = "reviewbot-491619",
    [string]$Region = "us-central1",
    [string]$InstanceName = "reviewbot-db",
    [string]$Port = "5432"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Cloud SQL Proxy for $InstanceName..." -ForegroundColor Cyan
Write-Host "   (Make sure you have downloaded the cloud-sql-proxy binary)" -ForegroundColor Yellow
Write-Host "   Connection string: $ProjectID:$Region:$InstanceName" -ForegroundColor Gray

# Check if cloud-sql-proxy exists in path
if (-not (Get-Command "cloud-sql-proxy" -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: cloud-sql-proxy not found in PATH." -ForegroundColor Red
    Write-Host "   Download it from: https://cloud.google.com/sql/docs/postgres/sql-proxy#install"
    exit 1
}

cloud-sql-proxy "$ProjectID:$Region:$InstanceName" --port "$Port"
