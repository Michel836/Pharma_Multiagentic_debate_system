#!/bin/bash

# Script de setup pour le système Pharma MultiAgent
echo "🚀 Configuration du système Pharma MultiAgent..."

# Vérifier les prérequis
check_requirements() {
    echo "📋 Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose n'est pas installé"
        exit 1
    fi
    
    # Vérifier Python (optionnel pour dev local)
    if command -v python3 &> /dev/null; then
        echo "✅ Python 3 détecté: $(python3 --version)"
    fi
    
    # Vérifier Node.js (optionnel pour dev local)
    if command -v node &> /dev/null; then
        echo "✅ Node.js détecté: $(node --version)"
    fi
    
    echo "✅ Prérequis vérifiés"
}

# Créer les répertoires nécessaires
setup_directories() {
    echo "📁 Création des répertoires..."
    
    mkdir -p backend/logs
    mkdir -p backend/data
    mkdir -p nginx/certs
    mkdir -p frontend/build
    
    echo "✅ Répertoires créés"
}

# Configurer les variables d'environnement
setup_env() {
    echo "⚙️  Configuration des variables d'environnement..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "📝 Fichier .env créé à partir de .env.example"
        echo "⚠️  IMPORTANT: Configurez votre clé API Gemini dans .env"
    else
        echo "✅ Fichier .env existant trouvé"
    fi
}

# Télécharger les modèles Ollama
setup_ollama_models() {
    echo "🤖 Configuration des modèles Ollama..."
    
    # Démarrer Ollama en arrière-plan
    docker-compose up -d ollama
    
    # Attendre que Ollama soit prêt
    echo "⏳ Attente du démarrage d'Ollama..."
    sleep 10
    
    # Télécharger les modèles essentiels
    echo "⬇️  Téléchargement des modèles LLM..."
    
    docker-compose exec ollama ollama pull llama3.2:8b
    docker-compose exec ollama ollama pull mistral:7b
    
    echo "✅ Modèles Ollama configurés"
}

# Initialiser la base de données
setup_database() {
    echo "💾 Initialisation de la base de données..."
    
    # Démarrer Redis
    docker-compose up -d redis
    
    echo "✅ Base de données initialisée"
}

# Construire les images Docker
build_images() {
    echo "🏗️  Construction des images Docker..."
    
    docker-compose build --no-cache
    
    echo "✅ Images Docker construites"
}

# Générer les certificats SSL (auto-signés pour dev)
setup_ssl() {
    echo "🔒 Génération des certificats SSL..."
    
    if [ ! -f nginx/certs/cert.pem ]; then
        openssl req -x509 -newkey rsa:4096 -nodes \
            -keyout nginx/certs/key.pem \
            -out nginx/certs/cert.pem \
            -days 365 \
            -subj "/C=FR/ST=Paris/L=Paris/O=Pharma/CN=localhost"
        
        echo "✅ Certificats SSL générés (auto-signés)"
    else
        echo "✅ Certificats SSL existants trouvés"
    fi
}

# Tester la configuration
test_setup() {
    echo "🧪 Test de la configuration..."
    
    # Démarrer tous les services
    docker-compose up -d
    
    # Attendre que les services soient prêts
    echo "⏳ Attente du démarrage des services..."
    sleep 30
    
    # Tester l'API backend
    if curl -f http://localhost:8000/api/health &> /dev/null; then
        echo "✅ Backend API fonctionnel"
    else
        echo "❌ Backend API non accessible"
    fi
    
    # Tester le frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        echo "✅ Frontend accessible"
    else
        echo "❌ Frontend non accessible"
    fi
    
    # Tester Ollama
    if curl -f http://localhost:11434/api/tags &> /dev/null; then
        echo "✅ Ollama accessible"
    else
        echo "❌ Ollama non accessible"
    fi
}

# Menu principal
main() {
    echo "🔬 Pharma MultiAgent - Script de Setup"
    echo "====================================="
    
    case "${1:-full}" in
        "requirements")
            check_requirements
            ;;
        "env")
            setup_env
            ;;
        "directories")
            setup_directories
            ;;
        "ollama")
            setup_ollama_models
            ;;
        "database")
            setup_database
            ;;
        "build")
            build_images
            ;;
        "ssl")
            setup_ssl
            ;;
        "test")
            test_setup
            ;;
        "full")
            check_requirements
            setup_directories
            setup_env
            setup_ssl
            build_images
            setup_database
            setup_ollama_models
            test_setup
            echo ""
            echo "🎉 Setup terminé!"
            echo "🌐 Frontend: http://localhost:3000"
            echo "🔧 Backend: http://localhost:8000"
            echo "🤖 Ollama: http://localhost:11434"
            echo ""
            echo "⚠️  N'oubliez pas de configurer votre clé API Gemini dans .env"
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  full         - Setup complet (défaut)"
            echo "  requirements - Vérifier les prérequis"
            echo "  env          - Configurer .env"
            echo "  directories  - Créer les répertoires"
            echo "  ollama       - Configurer Ollama"
            echo "  database     - Initialiser la DB"
            echo "  build        - Construire les images"
            echo "  ssl          - Générer les certificats"
            echo "  test         - Tester la configuration"
            echo "  help         - Afficher cette aide"
            ;;
        *)
            echo "❌ Commande inconnue: $1"
            echo "Utilisez '$0 help' pour voir les options disponibles"
            exit 1
            ;;
    esac
}

# Exécuter le script
main "$@"