@echo off
echo.
echo ===============================================
echo 🏥 SYSTÈME PHARMA MULTIAGENT COMPLET
echo ===============================================
echo.
echo 🎯 Lancement de l'interface pharmaceutique
echo 🤖 Ollama qwen3:4b + Interface complète
echo 🔐 100%% Local + Confidentialité maximale
echo.

REM Vérifier que les prérequis sont installés
echo 1. Vérification des prérequis...
python --version >nul 2>&1 || (
    echo ❌ Python manquant! Installez Python 3.8+
    pause
    exit /b 1
)
echo ✅ Python détecté

ollama --version >nul 2>&1 || (
    echo ❌ Ollama manquant! Installez Ollama
    pause
    exit /b 1
)
echo ✅ Ollama détecté

echo.
echo 2. Démarrage des services...

REM Démarrer Ollama si pas déjà lancé
echo 🚀 Démarrage d'Ollama...
start "Ollama Server" cmd /k "echo 🤖 OLLAMA SERVER && echo ================ && set OLLAMA_ORIGINS=* && ollama serve"

REM Attendre un peu
timeout /t 3 >nul

REM Vérifier que qwen3:4b est disponible
echo 🔍 Vérification du modèle qwen3:4b...
curl -s http://localhost:11434/api/tags | find "qwen3:4b" >nul
if errorlevel 1 (
    echo ⚠️ Modèle qwen3:4b non trouvé
    echo 📥 Téléchargement automatique...
    ollama pull qwen3:4b
)
echo ✅ Modèle qwen3:4b prêt

REM Démarrer le serveur HTTP
echo 🌐 Démarrage serveur HTTP...
start "HTTP Server" cmd /k "echo 🌐 SERVEUR HTTP && echo =============== && echo Interface: http://localhost:8000/pharma_debate_complete.html && echo. && python -m http.server 8000"

REM Attendre que le serveur démarre
timeout /t 3 >nul

echo.
echo ===============================================
echo ✅ SYSTÈME COMPLETEMENT DÉMARRÉ!
echo ===============================================
echo.
echo 📱 Interface complète: http://localhost:8000/pharma_debate_complete.html
echo 🤖 Ollama API: http://localhost:11434
echo 🌐 Serveur HTTP: http://localhost:8000
echo.
echo 🎯 PROCHAINES ÉTAPES:
echo    1. L'interface va s'ouvrir automatiquement
echo    2. Cliquez sur "Test Connexion"
echo    3. Puis "Démarrer Débat" pour lancer les experts
echo.
echo 📊 FONCTIONNALITÉS:
echo    • 3 Experts pharmaceutiques (Réglementaire, Clinique, Qualité)
echo    • Débats authentiques avec qwen3:4b
echo    • Métriques temps réel et consensus
echo    • 100%% local, 0€, confidentialité maximale
echo.

REM Ouvrir automatiquement l'interface
echo 🚀 Ouverture de l'interface...
timeout /t 2 >nul
start "" "http://localhost:8000/pharma_debate_complete.html"

echo.
echo ===============================================
echo 🎉 PRÊT À UTILISER!
echo ===============================================
echo.
echo ⏹️ Pour arrêter: Fermez les fenêtres cmd ouvertes
echo 📖 Documentation: Voir les fichiers README_*.md
echo 🐛 Support: Vérifiez les logs dans les fenêtres cmd
echo.
pause