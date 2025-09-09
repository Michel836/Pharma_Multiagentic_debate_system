@echo off
echo 🚀 Démarrage du système Pharma MultiAgent complet
echo ================================================

echo.
echo 1. Vérification des prérequis...
python --version >nul 2>&1 || (
    echo ❌ Python non trouvé! Veuillez installer Python 3.8+
    pause
    exit /b
)

node --version >nul 2>&1 || (
    echo ❌ Node.js non trouvé! Veuillez installer Node.js
    pause
    exit /b
)

echo ✅ Python et Node.js détectés

echo.
echo 2. Démarrage Ollama...
start "Ollama Server" cmd /k "set OLLAMA_ORIGINS=* && set OLLAMA_HOST=0.0.0.0:11434 && ollama serve"
timeout /t 3 >nul

echo.
echo 3. Installation des dépendances Python...
cd backend
pip install -r requirements.txt

echo.
echo 4. Démarrage du backend FastAPI...
start "Backend API" cmd /k "python main.py"
timeout /t 3 >nul

echo.
echo 5. Installation des dépendances React...
cd ..\frontend
if not exist node_modules npm install

echo.
echo 6. Démarrage du frontend React...
start "Frontend React" cmd /k "npm start"

echo.
echo 🎉 Système complet démarré!
echo ================================
echo 📱 Frontend React: http://localhost:3000
echo 🖥️  Backend API: http://localhost:8000
echo 🤖 Ollama API: http://localhost:11434
echo 📊 Interface HTML: test_complete_system.html
echo.
echo Appuyez sur une touche pour ouvrir l'interface...
pause >nul

start "" "http://localhost:3000"
start "" "test_complete_system.html"