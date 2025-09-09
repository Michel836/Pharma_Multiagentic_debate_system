# Makefile pour le système Pharma MultiAgent
.PHONY: help setup start stop restart logs clean dev prod test lint format

# Variables par défaut
ENVIRONMENT ?= development
SERVICE ?= all

# Aide
help:
	@echo "🔬 Pharma MultiAgent - Commandes disponibles"
	@echo "============================================="
	@echo ""
	@echo "Setup et configuration:"
	@echo "  setup              - Configuration initiale complète"
	@echo "  setup-env          - Créer le fichier .env"
	@echo "  setup-ssl          - Générer les certificats SSL"
	@echo ""
	@echo "Démarrage et arrêt:"
	@echo "  start              - Démarrer en mode développement"
	@echo "  start-prod         - Démarrer en mode production"
	@echo "  stop               - Arrêter tous les services"
	@echo "  restart            - Redémarrer tous les services"
	@echo ""
	@echo "Développement:"
	@echo "  dev                - Mode développement avec hot reload"
	@echo "  logs               - Voir les logs (SERVICE=nom pour un service)"
	@echo "  shell-backend      - Shell interactif backend"
	@echo "  shell-frontend     - Shell interactif frontend"
	@echo ""
	@echo "Maintenance:"
	@echo "  build              - Construire les images Docker"
	@echo "  clean              - Nettoyer les containers et volumes"
	@echo "  prune              - Nettoyer Docker complètement"
	@echo ""
	@echo "Tests et qualité:"
	@echo "  test               - Exécuter les tests"
	@echo "  lint               - Linter le code"
	@echo "  format             - Formater le code"
	@echo ""
	@echo "Monitoring:"
	@echo "  status             - Statut des services"
	@echo "  health             - Vérification santé"
	@echo "  ps                 - Processus Docker"

# Configuration initiale
setup:
	@echo "🚀 Configuration initiale..."
	@chmod +x scripts/*.sh
	@./scripts/setup.sh full

setup-env:
	@echo "⚙️  Configuration environnement..."
	@./scripts/setup.sh env

setup-ssl:
	@echo "🔒 Génération certificats SSL..."
	@./scripts/setup.sh ssl

# Démarrage des services
start:
	@echo "▶️  Démarrage mode développement..."
	@./scripts/start.sh development detached

start-prod:
	@echo "▶️  Démarrage mode production..."
	@./scripts/start.sh production detached

dev:
	@echo "🔧 Mode développement interactif..."
	@./scripts/start.sh development

# Arrêt et redémarrage
stop:
	@echo "⏹️  Arrêt des services..."
	@docker-compose down

restart:
	@echo "🔄 Redémarrage des services..."
	@docker-compose restart $(SERVICE)

# Logs et debugging
logs:
ifeq ($(SERVICE), all)
	@docker-compose logs -f
else
	@docker-compose logs -f $(SERVICE)
endif

shell-backend:
	@docker-compose exec backend bash

shell-frontend:
	@docker-compose exec frontend sh

# Construction et nettoyage
build:
	@echo "🏗️  Construction des images..."
	@docker-compose build --no-cache

clean:
	@echo "🧹 Nettoyage des containers..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f

prune:
	@echo "🧹 Nettoyage Docker complet..."
	@docker-compose down -v --remove-orphans
	@docker system prune -af
	@docker volume prune -f

# Tests
test:
	@echo "🧪 Exécution des tests..."
	@docker-compose exec backend python -m pytest tests/ -v
	@docker-compose exec frontend npm test

test-backend:
	@docker-compose exec backend python -m pytest tests/ -v

test-frontend:
	@docker-compose exec frontend npm test

# Qualité de code
lint:
	@echo "🔍 Linting du code..."
	@docker-compose exec backend python -m flake8 .
	@docker-compose exec backend python -m black --check .
	@docker-compose exec frontend npm run lint

format:
	@echo "✨ Formatage du code..."
	@docker-compose exec backend python -m black .
	@docker-compose exec backend python -m isort .
	@docker-compose exec frontend npm run format

# Monitoring
status:
	@echo "📊 Statut des services..."
	@docker-compose ps

health:
	@echo "🏥 Vérification santé..."
	@./scripts/start.sh health

ps:
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Utilitaires avancés
backup:
	@echo "💾 Sauvegarde des données..."
	@mkdir -p backups
	@docker-compose exec backend tar -czf - /app/data | cat > backups/data_$(shell date +%Y%m%d_%H%M%S).tar.gz
	@echo "✅ Sauvegarde créée dans backups/"

restore:
	@echo "📥 Restauration des données..."
	@read -p "Fichier de sauvegarde: " backup_file && \
		cat $$backup_file | docker-compose exec -T backend tar -xzf - -C /

install-hooks:
	@echo "🎣 Installation des hooks Git..."
	@cp scripts/pre-commit .git/hooks/
	@chmod +x .git/hooks/pre-commit
	@echo "✅ Hooks Git installés"

# Gestion des modèles Ollama
ollama-pull:
	@echo "⬇️  Téléchargement des modèles Ollama..."
	@docker-compose exec ollama ollama pull llama3.2:8b
	@docker-compose exec ollama ollama pull mistral:7b
	@docker-compose exec ollama ollama pull qwen2:7b

ollama-list:
	@echo "📋 Modèles Ollama disponibles..."
	@docker-compose exec ollama ollama list

# Migration et maintenance DB
db-init:
	@echo "💾 Initialisation base de données..."
	@docker-compose exec backend python -m scripts.init_db

db-migrate:
	@echo "🔄 Migration base de données..."
	@docker-compose exec backend python -m scripts.migrate_db

# Monitoring avancé
monitor:
	@echo "📊 Monitoring en temps réel..."
	@docker stats $(shell docker-compose ps -q)

top:
	@echo "📈 Processus par service..."
	@docker-compose top

# Sécurité
security-scan:
	@echo "🔒 Scan de sécurité..."
	@docker-compose exec backend safety check
	@docker-compose exec frontend npm audit

# Export/Import de configuration
export-config:
	@echo "📤 Export de la configuration..."
	@docker-compose config > pharma_multiagent_config.yml

# Déploiement
deploy-staging:
	@echo "🚀 Déploiement staging..."
	@ENVIRONMENT=staging docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

deploy-prod:
	@echo "🚀 Déploiement production..."
	@ENVIRONMENT=production docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Commandes par défaut
.DEFAULT_GOAL := help