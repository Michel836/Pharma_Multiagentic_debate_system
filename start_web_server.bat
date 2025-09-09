@echo off
title Serveur Web - Port 8000
echo ╔═══════════════════════════════════════╗
echo ║         SERVEUR WEB LOCAL             ║
echo ║            Port: 8000                 ║
echo ╚═══════════════════════════════════════╝
echo.
echo Demarrage du serveur web...
echo.
echo Acces disponible sur:
echo http://localhost:8000/pharma_debate_complete.html
echo.
python -m http.server 8000