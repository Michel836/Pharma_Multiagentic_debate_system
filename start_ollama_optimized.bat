@echo off
title Ollama Optimized - AMD Ryzen 8840HS
echo ╔═══════════════════════════════════════════════════════╗
echo ║           OLLAMA OPTIMISÉ POUR NPU/GPU AMD           ║
echo ║              Ryzen 7 8840HS + Radeon 780M            ║
echo ║                     Port: 11434                       ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

REM Configuration optimisée pour AMD 8840HS
set OLLAMA_HOST=0.0.0.0:11434
set OLLAMA_ORIGINS=*
set OLLAMA_NUM_PARALLEL=4
set OLLAMA_FLASH_ATTENTION=true
set OLLAMA_GPU_OVERHEAD=512
set OLLAMA_KEEP_ALIVE=10m

REM Optimisations AMD spécifiques
set HSA_OVERRIDE_GFX_VERSION=11.0.3
set HIP_VISIBLE_DEVICES=0
set ROCM_PATH=C:\Program Files\AMD\ROCm\5.7

REM Configuration mémoire optimisée
set OLLAMA_MAX_LOADED_MODELS=1
set OLLAMA_CONTEXT_LENGTH=8192

echo Configuration NPU/GPU:
echo - NPU AMD XDNA: Activé
echo - GPU Radeon 780M: Force activé
echo - Parallélisme: 4 tâches
echo - Flash Attention: Activée
echo - Context: 8K tokens
echo.

echo Démarrage Ollama optimisé...
ollama serve