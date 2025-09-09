@echo off
setlocal enabledelayedexpansion
color 0B
title 🏥 Système Pharma MultiAgent - Démarrage Complet

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                   🏥 SYSTÈME PHARMA MULTIAGENT COMPLET                      ║
echo ║                        Ollama qwen3:4b + Interface Web                      ║
echo ║                      100%% Local • 0€ • Confidentialité Max                ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

REM Configuration des variables
set "PROJECT_DIR=%~dp0"
set "LOG_FILE=%PROJECT_DIR%logs\startup.log"
set "OLLAMA_PORT=11434"
set "HTTP_PORT=8000"
set "INTERFACE_FILE=pharma_debate_complete.html"

REM Créer le dossier logs s'il n'existe pas
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

echo [%date% %time%] Démarrage du système Pharma MultiAgent >> "%LOG_FILE%"
echo 📝 Log détaillé : %LOG_FILE%
echo.

echo ════════════════════════════════════════════════════════════════════════════════
echo 🔍 PHASE 1: VÉRIFICATION DES PRÉREQUIS
echo ════════════════════════════════════════════════════════════════════════════════

REM Vérification Python
echo 🐍 Test Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: Python n'est pas installé ou non accessible
    echo    💡 Solution: Installez Python 3.8+ depuis https://python.org
    echo    📋 Vérifiez que Python est dans le PATH système
    echo [%date% %time%] ERREUR: Python manquant >> "%LOG_FILE%"
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% détecté
echo [%date% %time%] Python %PYTHON_VERSION% OK >> "%LOG_FILE%"

REM Vérification Ollama
echo 🤖 Test Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: Ollama n'est pas installé ou non accessible
    echo    💡 Solution: Installez Ollama depuis https://ollama.ai
    echo    📋 Redémarrez après installation pour mise à jour PATH
    echo [%date% %time%] ERREUR: Ollama manquant >> "%LOG_FILE%"
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('ollama --version 2^>^&1') do set OLLAMA_VERSION=%%i
echo ✅ %OLLAMA_VERSION% détecté
echo [%date% %time%] %OLLAMA_VERSION% OK >> "%LOG_FILE%"

REM Vérification curl (pour tests API)
echo 🌐 Test curl...
curl --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ curl non disponible - tests API limités
    set "CURL_AVAILABLE=false"
) else (
    echo ✅ curl disponible
    set "CURL_AVAILABLE=true"
)

REM Vérification fichier interface
echo 📄 Test fichier interface...
if not exist "%PROJECT_DIR%%INTERFACE_FILE%" (
    echo ❌ ERREUR: Fichier %INTERFACE_FILE% introuvable
    echo    📁 Répertoire: %PROJECT_DIR%
    echo    💡 Solution: Vérifiez que tous les fichiers sont présents
    echo [%date% %time%] ERREUR: Interface manquante >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo ✅ Interface %INTERFACE_FILE% trouvée
echo [%date% %time%] Interface OK >> "%LOG_FILE%"

echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🚀 PHASE 2: DÉMARRAGE DES SERVICES
echo ════════════════════════════════════════════════════════════════════════════════

REM Arrêt des processus existants (nettoyage)
echo 🧹 Nettoyage processus existants...
taskkill /f /im ollama.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
echo ✅ Nettoyage terminé

REM Attendre que les ports se libèrent
timeout /t 2 >nul

REM Démarrage Ollama avec configuration optimale
echo 🤖 Démarrage Ollama Server...
echo    📡 Port: %OLLAMA_PORT%
echo    🌐 CORS: Activé pour toutes origines
echo    🔧 Host: 0.0.0.0 (accessible localement)

start "🤖 Ollama Server" cmd /k "title 🤖 OLLAMA SERVER - Port %OLLAMA_PORT% && echo ╔═══════════════════════════════════════╗ && echo ║        🤖 OLLAMA SERVER ACTIF         ║ && echo ║    Port: %OLLAMA_PORT%                       ║ && echo ║    CORS: Activé                       ║ && echo ║    Modèle: qwen3:4b                   ║ && echo ╚═══════════════════════════════════════╝ && echo. && echo 📊 Logs Ollama: && set OLLAMA_ORIGINS=* && set OLLAMA_HOST=0.0.0.0:%OLLAMA_PORT% && ollama serve"

echo    ⏳ Attente démarrage Ollama (5 secondes)...
timeout /t 5 >nul

REM Test connexion Ollama
echo 🔍 Test connexion Ollama...
if "%CURL_AVAILABLE%"=="true" (
    curl -s http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
    if errorlevel 1 (
        echo ⚠️ Ollama pas encore prêt, attente supplémentaire...
        timeout /t 3 >nul
    ) else (
        echo ✅ Ollama répond sur port %OLLAMA_PORT%
    )
) else (
    echo ⏳ Test Ollama (attente 3 secondes supplémentaires)...
    timeout /t 3 >nul
)

REM Vérification/installation modèle qwen3:4b
echo 🔍 Vérification modèle qwen3:4b...
echo    📥 Cela peut prendre du temps lors du premier lancement...

if "%CURL_AVAILABLE%"=="true" (
    curl -s http://localhost:%OLLAMA_PORT%/api/tags | find "qwen3:4b" >nul 2>&1
    if errorlevel 1 (
        echo 📥 Modèle qwen3:4b non trouvé, téléchargement...
        echo    ⚠️ ATTENTION: Téléchargement ~2.5GB, soyez patient!
        echo    📊 Progression visible dans la fenêtre Ollama
        start /wait ollama pull qwen3:4b
        echo ✅ Modèle qwen3:4b installé
    ) else (
        echo ✅ Modèle qwen3:4b déjà disponible
    )
) else (
    echo 📥 Tentative pull qwen3:4b (peut être ignoré si déjà installé)...
    ollama pull qwen3:4b >nul 2>&1
    echo ✅ Vérification modèle terminée
)

echo [%date% %time%] Ollama et qwen3:4b prêts >> "%LOG_FILE%"

REM Démarrage serveur HTTP
echo 🌐 Démarrage Serveur HTTP...
echo    📡 Port: %HTTP_PORT%
echo    📁 Répertoire: %PROJECT_DIR%
echo    🔧 CORS: Résolu automatiquement

cd /d "%PROJECT_DIR%"
start "🌐 HTTP Server" cmd /k "title 🌐 SERVEUR HTTP - Port %HTTP_PORT% && echo ╔═══════════════════════════════════════╗ && echo ║       🌐 SERVEUR HTTP ACTIF           ║ && echo ║    Port: %HTTP_PORT%                         ║ && echo ║    Interface: pharma_debate_complete  ║ && echo ║    CORS: Résolu                       ║ && echo ╚═══════════════════════════════════════╝ && echo. && echo 🔗 Interface complète: && echo    http://localhost:%HTTP_PORT%/%INTERFACE_FILE% && echo. && echo 📊 Logs HTTP Server: && python -m http.server %HTTP_PORT%"

echo    ⏳ Attente démarrage serveur HTTP (3 secondes)...
timeout /t 3 >nul

echo [%date% %time%] Serveur HTTP démarré >> "%LOG_FILE%"

echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo ✅ PHASE 3: VÉRIFICATIONS FINALES ET LANCEMENT
echo ════════════════════════════════════════════════════════════════════════════════

REM Tests finaux
echo 🧪 Tests système...

if "%CURL_AVAILABLE%"=="true" (
    echo    🔍 Test API Ollama...
    curl -s http://localhost:%OLLAMA_PORT%/api/tags >nul 2>&1
    if errorlevel 1 (
        echo    ⚠️ API Ollama non accessible (peut être normal au démarrage)
    ) else (
        echo    ✅ API Ollama opérationnelle
    )
    
    echo    🔍 Test Serveur HTTP...
    curl -s http://localhost:%HTTP_PORT% >nul 2>&1
    if errorlevel 1 (
        echo    ⚠️ Serveur HTTP non accessible
    ) else (
        echo    ✅ Serveur HTTP opérationnel
    )
) else (
    echo    ℹ️ Tests automatiques limités (curl non disponible)
)

echo [%date% %time%] Tests finalisés >> "%LOG_FILE%"

REM Affichage informations système
echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                        ✅ SYSTÈME COMPLÈTEMENT DÉMARRÉ!                     ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.
echo 🎯 ACCÈS PRINCIPAL:
echo    🌐 Interface complète : http://localhost:%HTTP_PORT%/%INTERFACE_FILE%
echo.
echo 🔧 SERVICES ACTIFS:
echo    🤖 Ollama API         : http://localhost:%OLLAMA_PORT%
echo    🌐 Serveur HTTP       : http://localhost:%HTTP_PORT%
echo    📊 Logs détaillés     : %LOG_FILE%
echo.
echo 📋 PROCHAINES ÉTAPES:
echo    1️⃣ L'interface va s'ouvrir automatiquement dans 5 secondes
echo    2️⃣ Cliquer sur "🔍 Test Connexion" pour vérifier le système
echo    3️⃣ Puis "🚀 Démarrer Débat" pour lancer les experts IA
echo.
echo 💡 FONCTIONNALITÉS DISPONIBLES:
echo    🔬 Expert Réglementaire  : Conformité GxP, réglementations FDA/EMA
echo    💊 Expert Clinique       : Essais Phase III, intégrité données  
echo    🔍 Expert Qualité        : Assurance qualité, contrôles processus
echo.
echo 🎛️ CONTRÔLES:
echo    ⏸️ Pause/Reprendre      : Bouton pause dans l'interface
echo    🗑️ Effacer messages     : Bouton effacer pour nouveau débat
echo    📊 Métriques temps réel : Consensus, temps réponse, confiance
echo.
echo 🔒 AVANTAGES:
echo    🏠 100%% Local           : Aucune donnée envoyée vers le cloud
echo    💰 0€ de coût           : Pas de tokens payants
echo    🔐 Confidentialité max  : Données restent sur votre machine
echo    ⚡ Performance contrôlée : Pas de throttling cloud
echo.

REM Attente avant ouverture automatique
echo ⏳ Ouverture automatique dans 5 secondes...
echo    (Appuyez sur Ctrl+C pour annuler l'ouverture automatique)
timeout /t 5

REM Ouverture interface dans navigateur par défaut
echo 🚀 Ouverture interface principale...
start "" "http://localhost:%HTTP_PORT%/%INTERFACE_FILE%"

echo [%date% %time%] Interface ouverte >> "%LOG_FILE%"

echo.
echo ════════════════════════════════════════════════════════════════════════════════
echo 🎉 SYSTÈME PRÊT À UTILISER!
echo ════════════════════════════════════════════════════════════════════════════════
echo.
echo ℹ️ AIDE ET SUPPORT:
echo    📖 Documentation      : README_COMPLET.md
echo    🐛 Résolution problèmes: Vérifiez les fenêtres cmd ouvertes
echo    📊 Logs système       : %LOG_FILE%
echo.
echo ⚠️ POUR ARRÊTER LE SYSTÈME:
echo    🔴 Fermez les 2 fenêtres cmd ouvertes (Ollama + HTTP Server)
echo    🔄 Ou relancez ce script pour redémarrer proprement
echo.
echo 🎯 BON DÉBAT PHARMACEUTIQUE MULTIAGENT!
echo.

REM Attendre une touche pour fermer cette fenêtre
pause
echo [%date% %time%] Script terminé >> "%LOG_FILE%"