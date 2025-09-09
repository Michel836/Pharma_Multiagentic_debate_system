# logger.py - Configuration du système de logging
import logging
import sys
import json
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Configure le système de logging pour l'application"""
    
    # Créer le répertoire de logs s'il n'existe pas
    log_path = Path('./logs')
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configuration du format
    log_format = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    
    # Nettoyer les handlers existants
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)
    
    # Handler fichier
    try:
        file_handler = logging.FileHandler(
            './logs/pharma_multiagent.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Erreur création handler fichier: {e}", file=sys.stderr)
    
    # Définir le niveau global
    root_logger.setLevel(logging.INFO)
    
    # Configurer les loggers spécifiques
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Logger plus verbeux pour nos modules
    logging.getLogger('agents').setLevel(logging.DEBUG)
    logging.getLogger('debate').setLevel(logging.DEBUG)
    logging.getLogger('orchestrator').setLevel(logging.INFO)
    
    # Log d'initialisation
    logger = logging.getLogger(__name__)
    logger.info("Système de logging initialisé")

def get_logger(name: str) -> logging.Logger:
    """Retourne un logger standard"""
    return logging.getLogger(name)