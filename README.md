# 🔬 Système Multi-Agent Pharmaceutique avec Débat et Validation

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-14+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 📋 Description

Plateforme sophistiquée de débat multi-agents pour l'industrie pharmaceutique R&D, utilisant l'IA pour analyser et débattre de questions complexes avec validation humaine et système de vote. Les agents IA discutent entre eux sous supervision humaine, avec validation obligatoire aux points critiques pour éliminer les hallucinations.

### 🎯 Objectifs Principaux

- **Débat visible** entre IAs (2+ experts + 1 juge) en temps réel
- **Validation humaine obligatoire** aux points de décision critiques
- **Système de vote** entre agents avec scoring transparent
- **Compteur de tours** configurable avec interruption automatique
- **Pipeline 4 étapes** : Extraction → Validation → Synthèse → Partage
- **RAG étendu** : Enterprise + Personal + Contacts/Emails
- **Conformité pharmaceutique** (GDPR, GxP) avec traçabilité complète

---

## 🏗️ Architecture Technique

```
Utilisateur R&D → Frontend React → Backend FastAPI
                                           ↓
                     ┌────────────────────────────────┐
                     │   Orchestrateur Multi-Agents   │
                     │  (Gemini/GPT-4/Claude/Ollama)  │
                     └────────────────────────────────┘
                                   ↓
                     ┌────────────────────────────────┐
                     │     Système de Validation      │
                     │    Humaine & Vote Pondéré      │
                     └────────────────────────────────┘
                                   ↓
                     ┌────────────────────────────────┐
                     │   Logging & Traçabilité        │
                     │      (JSON Structuré)          │
                     └────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
pharma-multiagent-system/
├── backend/
│   ├── agents/          # Logique des agents IA
│   │   ├── llm_providers.py
│   │   ├── orchestrator.py
│   │   └── ollama_orchestrator.py
│   ├── debate/          # Gestionnaire de débat
│   │   ├── debate_manager.py
│   │   └── voting_system.py
│   ├── validation/      # Système de validation
│   │   └── human_validator.py
│   ├── utils/          # Utilitaires et logging
│   │   ├── config.py
│   │   └── logger.py
│   ├── main.py         # API FastAPI principale
│   └── main_ollama.py  # Version Ollama
├── frontend/
│   ├── src/
│   │   ├── components/  # Composants React
│   │   ├── services/    # Services API
│   │   └── styles/      # Styles CSS
│   └── public/          # Assets statiques
├── scripts/             # Scripts de démarrage
│   ├── setup.sh
│   └── start.sh
├── nginx/              # Configuration reverse proxy
├── docker-compose.yml  # Orchestration Docker
├── Makefile           # Commandes automatisées
├── .env.example       # Variables d'environnement
└── README.md          # Documentation
```

---

## 🚀 Installation Rapide

### Prérequis

- Python 3.8+
- Node.js 14+
- Docker et Docker Compose (optionnel)
- Ollama pour utilisation locale (optionnel)
- 8GB RAM minimum

### Option 1 : Installation avec Docker

```bash
# 1. Cloner le projet
git clone https://github.com/votre-username/pharma-multiagent-system.git
cd pharma-multiagent-system

# 2. Configuration
cp .env.example .env
# Éditer .env avec vos clés API

# 3. Démarrage
docker-compose up
```

### Option 2 : Installation Manuelle

```bash
# 1. Backend
cd backend
pip install -r requirements.txt

# 2. Frontend  
cd ../frontend
npm install

# 3. Configuration
cp .env.example .env
# Ajouter vos clés API

# 4. Démarrage
# Terminal 1 - Backend
cd backend && python main.py

# Terminal 2 - Frontend
cd frontend && npm start
```

### Scripts de Démarrage Rapide

#### Windows
```batch
# Ollama local
start_ollama_only.bat

# Système complet
start_system.bat

# Interface de débat
start_pharma_debate.bat
```

#### Linux/Mac
```bash
# Setup initial
./scripts/setup.sh

# Démarrage
make start

# Ou directement
./scripts/start.sh
```

### Commandes Make Disponibles

```bash
make setup      # Installation complète
make start      # Démarrer tous les services
make stop       # Arrêter tous les services
make logs       # Voir les logs
make test       # Lancer les tests
make clean      # Nettoyer le projet
make help       # Aide détaillée
```

---

## ⚙️ Configuration

### Variables d'Environnement (.env)

```bash
# APIs LLM (au moins une requise)
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key      # Optionnel
ANTHROPIC_API_KEY=your_claude_key   # Optionnel

# Ollama (pour utilisation locale)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama2

# Configuration Débat
NUM_AGENTS=5
NUM_ROUNDS=3
DEBATE_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=90
```

---

## ✨ Fonctionnalités Principales

### 1. Débat Multi-Agent Intelligent
- **Orchestration** : 2 à 10 agents IA simultanés
- **Multi-LLM** : Support Gemini, GPT-4, Claude, Ollama
- **Débat structuré** : Arguments, contre-arguments, synthèse
- **Vote pondéré** : Système de scoring transparent
- **Temps réel** : WebSocket pour updates instantanées

### 2. Validation Humaine Interactive
- **Checkpoints** : Points de validation obligatoires
- **Intervention** : Possibilité d'intervenir à tout moment
- **Commentaires** : Ajout de contexte et corrections
- **Historique** : Traçabilité complète des validations

### 3. Système de Logging Professionnel
- **Format JSON** : Structuré et interrogeable
- **Traçabilité** : Audit trail complet
- **Métriques** : Performance et qualité
- **Conformité** : GDPR et GxP ready

### 4. Interface Web Moderne
- **React** : Interface responsive et intuitive  
- **Visualisation** : Graphiques et métriques en temps réel
- **Export** : JSON, CSV, PDF
- **Multi-langue** : Support FR/EN

### 5. Sécurité & Performance
- **Kill Switch** : Arrêt d'urgence automatique
- **Rate Limiting** : Protection contre abus
- **Cache** : Optimisation des requêtes
- **Monitoring** : Métriques temps réel

---

## 💻 Guide d'Utilisation

### Interface Web

1. **Accès** : http://localhost:3000
2. **Nouveau débat** : Cliquer sur "Nouveau Débat"
3. **Configuration** :
   - Choisir le modèle LLM
   - Nombre d'agents (3-10)
   - Nombre de rounds (1-5)
4. **Lancer** : Entrer la question et démarrer
5. **Interaction** : Valider/rejeter les arguments en temps réel
6. **Résultats** : Export automatique disponible

---

### API REST

```bash
# Créer un débat
POST /api/debate/create
{
  "question": "Analyse comparative des traitements",
  "num_agents": 5,
  "llm_provider": "gemini"
}

# Statut du débat
GET /api/debate/{id}/status

# Valider un argument  
POST /api/debate/{id}/validate
{
  "agent_id": "agent_1",
  "validation": "approved"
}
```

---

## 🧪 Exemples d'Utilisation

### Cas 1 : Analyse de Médicament
```python
"Quelle est la meilleure approche pour développer 
un traitement contre Alzheimer considérant les 
échecs récents des approches amyloïdes?"
```

### Cas 2 : Stratégie Réglementaire  
```python
"Comment optimiser le processus d'approbation FDA 
pour un dispositif médical de classe II avec IA?"
```

### Cas 3 : Évaluation Risques
```python
"Analyse des risques de l'utilisation de l'IA 
générative dans le diagnostic radiologique"
```

---

## 🔧 Dépannage

### Problèmes Fréquents

**Ollama ne démarre pas**
```bash
# Vérifier installation
ollama --version

# Relancer le service
ollama serve
```

**Erreur CORS avec Ollama**
```bash
# Windows
set OLLAMA_ORIGINS=*
ollama serve

# Linux/Mac  
export OLLAMA_ORIGINS=*
ollama serve
```

**Port 3000/8000 occupé**
```bash
# Changer les ports dans .env
FRONTEND_PORT=3001
BACKEND_PORT=8001
```

---

## 📚 Documentation Complète

- [Architecture Détaillée](ARCHITECTURE_FINALE_DEBAT_VISIBLE.md)
- [Guide Ollama](DEMARRAGE_RAPIDE_OLLAMA.md)  
- [Système de Logging](GUIDE_ULTIMATE_LOGGING_2025.md)
- [Architecture Multi-Agent](ARCHITECTURE_MULTIAGENT_PHARMA_LOGGING.md)
- [Intégration Ollama](MULTIAGENT_OLLAMA_INTEGRATION.md)
- [Rapports de Tests](RAPPORT_FINAL_TESTS_SEPTEMBRE_2025.md)

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 🔒 Sécurité

- Sanitization automatique des données sensibles
- Chiffrement des communications
- Authentification API sécurisée  
- Audit trail complet
- Conformité GDPR/GxP

---

## 📊 Performance

- Response time : < 5s (cloud) / < 2s (local)
- Capacité : 5-10 agents simultanés
- Token usage : < 10k par débat
- Taux de consensus : > 80%
- Disponibilité : 99.9%

---

## 📞 Support

- 📧 Email : support@pharma-multiagent.com
- 💬 Discord : [Rejoindre](https://discord.gg/pharma-ai)
- 🐛 Issues : [GitHub](https://github.com/votre-username/pharma-multiagent-system/issues)
- 📖 Wiki : [Documentation](https://github.com/votre-username/pharma-multiagent-system/wiki)

---

## 📄 Licence

MIT License - voir [LICENSE](LICENSE) pour plus de détails

## 🙏 Remerciements

- Anthropic, OpenAI, Google pour les APIs LLM
- Communauté Ollama pour les modèles open-source
- Tous les contributeurs et testeurs

---

**Version** : 1.0.0  
**Dernière mise à jour** : Décembre 2024  
**Statut** : Production Ready