#!/bin/bash
set -e

echo "=== DocuScan AI ==="

cd "$(dirname "$0")/docker"

case "${1:-up}" in
  up)
    echo "Lancement de tous les services..."
    docker compose up --build -d
    echo ""
    echo "Services disponibles :"
    echo "  Frontend  → http://localhost:5173"
    echo "  Backend   → http://localhost:8000"
    echo "  Airflow   → http://localhost:8080 (admin/admin)"
    echo "  MongoDB   → localhost:27017"
    echo "  HDFS      → http://localhost:9870"
    echo ""
    echo "Logs : docker compose logs -f"
    ;;
  down)
    echo "Arret de tous les services..."
    docker compose down
    ;;
  restart)
    echo "Redemarrage..."
    docker compose down
    docker compose up --build -d
    ;;
  logs)
    docker compose logs -f ${2:-}
    ;;
  status)
    docker compose ps
    ;;
  clean)
    echo "Arret + suppression des volumes..."
    docker compose down -v
    ;;
  *)
    echo "Usage: ./start.sh [up|down|restart|logs|status|clean]"
    echo ""
    echo "  up       Lancer tous les services (defaut)"
    echo "  down     Arreter tous les services"
    echo "  restart  Redemarrer tous les services"
    echo "  logs     Afficher les logs (optionnel: nom du service)"
    echo "  status   Afficher l'etat des containers"
    echo "  clean    Arreter et supprimer les volumes"
    ;;
esac
