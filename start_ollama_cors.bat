@echo off
title Ollama Server avec CORS - Port 11434
echo ╔═══════════════════════════════════════╗
echo ║        OLLAMA SERVER + CORS           ║
echo ║          Port: 11434                  ║
echo ║          CORS: Activé                 ║
echo ║          Modèle: qwen3:4b             ║
echo ╚═══════════════════════════════════════╝
echo.

REM Configuration CORS pour l'interface web
set OLLAMA_ORIGINS=*
set OLLAMA_HOST=0.0.0.0:11434

echo Configuration:
echo - OLLAMA_ORIGINS: %OLLAMA_ORIGINS%
echo - OLLAMA_HOST: %OLLAMA_HOST%
echo.

echo Démarrage d'Ollama...
ollama serve