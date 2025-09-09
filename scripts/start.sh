#!/bin/bash

# Script de démarrage pour le système Pharma MultiAgent
echo "🚀 Démarrage du système Pharma MultiAgent..."

# Configuration par défaut
MODE=${1:-"development"}
DETACHED=${2:-"false"}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [mode] [detached]"
    echo ""
    echo "Modes disponibles:"
    echo "  development  - Mode développement (défaut)"
    echo "  production   - Mode production"
    echo ""
    echo "Options:"
    echo "  detached     - Démarrer en arrière-plan"
    echo ""
    echo "Exemples:"
    echo "  $0                    # Dev mode, foreground"
    echo "  $0 production         # Prod mode, foreground"
    echo "  $0 development detached  # Dev mode, background"
}

# Vérifier les prérequis
check_prerequisites() {
    if [ ! -f .env ]; then
        echo "❌ Fichier .env manquant"
        echo "💡 Exécutez d'abord: ./scripts/setup.sh"
        exit 1
    fi
    
    if [ ! -d backend/logs ]; then
        echo "⚠️  Répertoires manquants, création automatique..."
        mkdir -p backend/logs backend/data nginx/certs
    fi
}

# Démarrer en mode développement
start_development() {
    echo "🔧 Démarrage en mode développement..."
    
    export ENVIRONMENT=development
    export DEBUG=true
    
    # Construire les images si nécessaire
    if [ ! "$(docker images -q pharma-multiagent-backend)" ]; then
        echo "🏗️  Construction des images Docker..."
        docker-compose build
    fi
    
    # Démarrer les services
    if [ "$DETACHED" = "detached" ]; then
        docker-compose -f docker-compose.yml up -d
        echo "✅ Services démarrés en arrière-plan"
        show_status
    else
        echo "▶️  Démarrage en mode interactif (Ctrl+C pour arrêter)"
        docker-compose -f docker-compose.yml up
    fi
}

# Démarrer en mode production
start_production() {
    echo "🏭 Démarrage en mode production..."
    
    export ENVIRONMENT=production
    export DEBUG=false
    
    # Vérifier les certificats SSL
    if [ ! -f nginx/certs/cert.pem ]; then
        echo "⚠️  Certificats SSL manquants, génération..."
        ./scripts/setup.sh ssl
    fi
    
    # Construire les images en mode production
    docker-compose build --no-cache
    
    # Démarrer les services
    if [ "$DETACHED" = "detached" ]; then
        docker-compose up -d
        echo "✅ Services de production démarrés"
        show_status
    else
        echo "▶️  Démarrage en mode production (Ctrl+C pour arrêter)"
        docker-compose up
    fi
}

# Afficher le statut des services
show_status() {
    echo ""
    echo "📊 Statut des services:"
    echo "======================="
    docker-compose ps
    
    echo ""
    echo "🌐 URLs d'accès:"
    echo "==============="
    echo "Frontend:     http://localhost:3000"
    echo "Backend API:  http://localhost:8000"
    echo "Docs API:     http://localhost:8000/docs"
    echo "Ollama:       http://localhost:11434"
    echo "Redis:        localhost:6379"
    
    if [ "$MODE" = "production" ]; then
        echo "HTTPS:        https://localhost"
    fi
    
    echo ""
    echo "📋 Commandes utiles:"
    echo "==================="
    echo "Voir les logs:     docker-compose logs -f [service]"
    echo "Arrêter:          docker-compose down"
    echo "Redémarrer:       docker-compose restart [service]"
    echo "Shell backend:    docker-compose exec backend bash"
    echo "Shell frontend:   docker-compose exec frontend sh"
}

# Vérifier la santé des services
health_check() {
    echo "🏥 Vérification de la santé des services..."
    
    sleep 10  # Attendre le démarrage
    
    # Backend
    if curl -f http://localhost:8000/api/health &>/dev/null; then
        echo "✅ Backend: OK"
    else
        echo "❌ Backend: KO"
    fi
    
    # Frontend
    if curl -f http://localhost:3000 &>/dev/null; then
        echo "✅ Frontend: OK"
    else
        echo "❌ Frontend: KO"
    fi
    
    # Ollama
    if curl -f http://localhost:11434/api/tags &>/dev/null; then
        echo "✅ Ollama: OK"
    else
        echo "❌ Ollama: KO"
    fi
    
    # Redis
    if docker-compose exec -T redis redis-cli ping &>/dev/null; then
        echo "✅ Redis: OK"
    else
        echo "❌ Redis: KO"
    fi
}

# Script principal
main() {
    case "$MODE" in
        "development"|"dev")
            check_prerequisites
            start_development
            ;;
        "production"|"prod")
            check_prerequisites
            start_production
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "❌ Mode inconnu: $MODE"
            show_help
            exit 1
            ;;
    esac
}

# Gestion des signaux
trap 'echo "🛑 Arrêt en cours..."; docker-compose down; exit 0' INT TERM

# Exécuter le script principal
main