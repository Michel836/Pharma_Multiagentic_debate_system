@echo off
echo =================================================
echo    SYSTEME MULTIAGENT 100%% LOCAL AVEC OLLAMA
echo =================================================
echo.

REM Vérifier si Ollama est installé
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Ollama n'est pas installe ou n'est pas dans le PATH
    echo.
    echo Telechargez Ollama depuis: https://ollama.ai
    echo.
    pause
    exit /b 1
)

echo [1/4] Demarrage du serveur Ollama...
start "Ollama Server" cmd /k "ollama serve"
timeout /t 5 /nobreak >nul

echo [2/4] Verification/Installation du modele llama3.2...
ollama list | findstr "llama3.2" >nul 2>nul
if %errorlevel% neq 0 (
    echo Installation du modele llama3.2 (3.2GB)...
    echo Cela peut prendre quelques minutes la premiere fois...
    ollama pull llama3.2
    echo Modele installe avec succes!
) else (
    echo Modele llama3.2 deja installe
)

echo.
echo [3/4] Demarrage du backend Python...
start "Backend MultiAgent" cmd /k "cd backend && python main_ollama.py"
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Demarrage du frontend React...
start "Frontend React" cmd /k "cd frontend && npm start"

echo.
echo =================================================
echo    SYSTEME DEMARRE AVEC SUCCES!
echo =================================================
echo.
echo Services disponibles:
echo - Frontend:     http://localhost:3000
echo - Backend API:  http://localhost:8000
echo - Ollama:       http://localhost:11434
echo.
echo Le navigateur va s'ouvrir automatiquement...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo Appuyez sur une touche pour arreter tous les services...
pause >nul

REM Arrêter tous les services
taskkill /FI "WindowTitle eq Ollama Server*" /T /F >nul 2>nul
taskkill /FI "WindowTitle eq Backend MultiAgent*" /T /F >nul 2>nul
taskkill /FI "WindowTitle eq Frontend React*" /T /F >nul 2>nul

echo.
echo Tous les services ont ete arretes.
pause