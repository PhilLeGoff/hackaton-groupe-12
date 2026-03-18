#!/usr/bin/env pwsh
param(
    [string]$Command = "up",
    [string]$Service = ""
)

Write-Host "=== DocuScan AI ===" -ForegroundColor Cyan

# Aller dans le dossier docker
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir/docker"

function RunDockerCompose {
    param([string[]]$Args)

    $output = & docker compose @Args 2>&1
    $exit = $LASTEXITCODE

    if ($exit -ne 0 -or $output -match "Usage:") {
        Write-Host "❌ ERREUR Docker Compose :" -ForegroundColor Red
        Write-Host $output -ForegroundColor Red
        Write-Host "Arrêt du script." -ForegroundColor Red
        exit 1
    }

    return $output
}

switch ($Command) {

    "up" {
        Write-Host "Lancement de tous les services..." -ForegroundColor Green

        RunDockerCompose @("up", "--build", "-d")

        Write-Host ""
        Write-Host "Services disponibles :" -ForegroundColor Yellow
        Write-Host "  Frontend  → http://localhost:5173"
        Write-Host "  Backend   → http://localhost:8000"
        Write-Host "  Airflow   → http://localhost:8080 (admin/admin)"
        Write-Host "  MongoDB   → localhost:27017"
        Write-Host "  HDFS      → http://localhost:9870"
        Write-Host ""
        Write-Host "Logs : docker compose logs -f"
    }

    "down" {
        Write-Host "Arrêt de tous les services..." -ForegroundColor Red
        RunDockerCompose @("down")
    }

    "restart" {
        Write-Host "Redémarrage..." -ForegroundColor Yellow
        RunDockerCompose @("down")
        RunDockerCompose @("up", "--build", "-d")
    }

    "logs" {
        if ($Service -ne "") {
            RunDockerCompose @("logs", "-f", $Service)
        } else {
            RunDockerCompose @("logs", "-f")
        }
    }

    "status" {
        RunDockerCompose @("ps")
    }

    "clean" {
        Write-Host "Arrêt + suppression des volumes..." -ForegroundColor Red
        RunDockerCompose @("down", "-v")
    }

    default {
        Write-Host "Usage: ./start.ps1 [up|down|restart|logs|status|clean]" -ForegroundColor Yellow
    }
}
