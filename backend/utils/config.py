# config.py - Chargement et gestion de la configuration
import os
import yaml
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def load_config(environment: str = None) -> Dict[str, Any]:
    """Charge la configuration depuis les fichiers YAML"""
    
    # Détecter l'environnement
    if environment is None:
        environment = os.getenv('ENVIRONMENT', 'development')
    
    # Chemin des fichiers de configuration
    config_dir = Path(__file__).parent.parent / 'config'
    config_file = config_dir / f'{environment}.yaml'
    
    if not config_file.exists():
        logger.warning(f"Fichier de configuration {config_file} non trouvé, utilisation de la config par défaut")
        return get_default_config()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Substituer les variables d'environnement
        config = _substitute_env_vars(config)
        
        # Valider la configuration
        _validate_config(config)
        
        logger.info(f"Configuration {environment} chargée depuis {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la configuration: {str(e)}")
        logger.warning("Utilisation de la configuration par défaut")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Configuration par défaut de base"""
    
    return {
        'app': {
            'name': 'Pharma MultiAgent System',
            'version': '1.0.0',
            'environment': 'development',
            'debug': True,
            'host': '127.0.0.1',
            'port': 8000
        },
        'llm_providers': [
            {
                'provider': 'gemini',
                'model_name': 'gemini-pro',
                'temperature': 0.5,
                'max_tokens': 1024,
                'api_key': os.getenv('GEMINI_API_KEY'),
                'timeout': 30
            }
        ],
        'debate': {
            'max_rounds': 5,
            'consensus_threshold': 0.7,
            'timeout_per_round': 120,
            'require_human_validation': False,
            'validation_threshold': 0.6
        },
        'logging': {
            'level': 'INFO',
            'format': 'detailed'
        },
        'security': {
            'cors': {
                'enabled': True,
                'allow_origins': ['http://localhost:3000']
            }
        }
    }

def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remplace les références aux variables d'environnement dans la config"""
    
    def _replace_value(value):
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            return os.getenv(env_var, value)
        elif isinstance(value, dict):
            return {k: _replace_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_replace_value(item) for item in value]
        else:
            return value
    
    return _replace_value(config)

def _validate_config(config: Dict[str, Any]) -> None:
    """Valide les paramètres de configuration essentiels"""
    
    # Vérifier les sections obligatoires
    required_sections = ['app', 'llm_providers']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Section de configuration manquante: {section}")
    
    # Valider la configuration des providers LLM
    if 'llm_providers' in config:
        if isinstance(config['llm_providers'], dict):
            # Format YAML avec providers en objets
            providers = []
            for provider_name, provider_config in config['llm_providers'].items():
                if provider_config.get('enabled', False):
                    if provider_name == 'gemini':
                        providers.append({
                            'provider': 'gemini',
                            'model_name': provider_config.get('model', 'gemini-pro'),
                            'temperature': provider_config.get('temperature', 0.5),
                            'max_tokens': provider_config.get('max_tokens', 1024),
                            'api_key': os.getenv('GEMINI_API_KEY'),
                            'timeout': provider_config.get('timeout', 30)
                        })
                    elif provider_name == 'ollama':
                        models = provider_config.get('models', ['llama3.2'])
                        for model in models:
                            providers.append({
                                'provider': 'ollama',
                                'model_name': model,
                                'temperature': 0.5,
                                'max_tokens': 1024,
                                'api_url': provider_config.get('host', 'http://localhost:11434'),
                                'timeout': provider_config.get('timeout', 45)
                            })
            
            config['llm_providers'] = providers
        
        # Vérifier qu'au moins un provider est configuré
        if not config['llm_providers']:
            logger.warning("Aucun provider LLM configuré, ajout de Gemini par défaut")
            config['llm_providers'] = [{
                'provider': 'gemini',
                'model_name': 'gemini-pro',
                'temperature': 0.5,
                'max_tokens': 1024,
                'api_key': os.getenv('GEMINI_API_KEY'),
                'timeout': 30
            }]

def get_env_config() -> str:
    """Retourne l'environnement actuel"""
    return os.getenv('ENVIRONMENT', 'development')

def is_development() -> bool:
    """Vérifie si on est en environnement de développement"""
    return get_env_config() == 'development'

def is_production() -> bool:
    """Vérifie si on est en environnement de production"""
    return get_env_config() == 'production'

def get_database_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait la configuration de base de données"""
    return config.get('database', {})

def get_logging_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait la configuration de logging"""
    return config.get('logging', {'level': 'INFO'})

def get_security_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extrait la configuration de sécurité"""
    return config.get('security', {})