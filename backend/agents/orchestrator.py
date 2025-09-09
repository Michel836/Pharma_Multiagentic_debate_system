# orchestrator.py - Orchestrateur principal du système multiagent
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from agents.llm_providers import get_provider, LLMConfig, test_all_providers
from validation.human_validator import HumanValidationManager

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrateur principal pour gérer les providers LLM et coordonner les débats"""
    
    def __init__(self):
        self.providers = {}
        self.provider_configs = []
        self.human_validator = HumanValidationManager()
        self.is_initialized = False
        self.initialization_time = None
        
    async def initialize_providers(self, provider_configs: List[Dict]) -> Dict[str, bool]:
        """Initialise tous les providers LLM configurés"""
        
        logger.info(f"STARTUP: Initialisation de {len(provider_configs)} providers LLM...")
        
        # Convertir les configs en objets LLMConfig
        configs = []
        for config_dict in provider_configs:
            try:
                config = LLMConfig(**config_dict)
                configs.append(config)
                self.provider_configs.append(config)
            except Exception as e:
                logger.error(f"Configuration invalide: {config_dict} - {str(e)}")
        
        # Tester et initialiser tous les providers
        results = await test_all_providers(configs)
        
        # Créer et stocker les providers qui fonctionnent
        for config in configs:
            provider_id = f"{config.provider}_{config.model_name.replace(':', '_').replace('.', '_')}"
            
            if results.get(provider_id, False):
                try:
                    provider = get_provider(
                        config.provider,
                        config.model_name,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        api_key=config.api_key,
                        api_url=config.api_url,
                        timeout=config.timeout
                    )
                    
                    await provider.initialize()
                    self.providers[provider_id] = provider
                    
                    logger.info(f"SUCCESS: Provider {provider_id} prêt")
                    
                except Exception as e:
                    logger.error(f"ERROR: Erreur initialisation {provider_id}: {str(e)}")
                    results[provider_id] = False
        
        self.is_initialized = len(self.providers) > 0
        self.initialization_time = datetime.utcnow()
        
        if self.is_initialized:
            logger.info(f"SUCCESS: Orchestrateur initialisé avec {len(self.providers)} providers")
        else:
            logger.error("ERROR: Aucun provider initialisé avec succès")
        
        return results
    
    async def get_provider(self, provider_id: str):
        """Récupère un provider par son ID"""
        
        if not self.is_initialized:
            raise RuntimeError("Orchestrateur non initialisé")
        
        if provider_id not in self.providers:
            available = list(self.providers.keys())
            raise ValueError(f"Provider {provider_id} non trouvé. Disponibles: {available}")
        
        return self.providers[provider_id]
    
    async def get_providers_status(self) -> Dict:
        """Retourne le statut de tous les providers"""
        
        status = {
            'total_providers': len(self.providers),
            'initialized': self.is_initialized,
            'initialization_time': self.initialization_time.isoformat() if self.initialization_time else None,
            'providers': {}
        }
        
        for provider_id, provider in self.providers.items():
            try:
                health = await provider.health_check()
                status['providers'][provider_id] = {
                    'healthy': health,
                    'model': provider.config.model_name,
                    'provider_type': provider.config.provider,
                    'temperature': provider.config.temperature,
                    'requests_made': provider.request_count,
                    'last_request': provider.last_request_time
                }
            except Exception as e:
                status['providers'][provider_id] = {
                    'healthy': False,
                    'error': str(e)
                }
        
        return status
    
    async def get_providers_health(self) -> Dict:
        """Health check rapide de tous les providers"""
        
        health_results = {}
        
        for provider_id, provider in self.providers.items():
            try:
                health = await asyncio.wait_for(provider.health_check(), timeout=10)
                health_results[provider_id] = health
            except asyncio.TimeoutError:
                health_results[provider_id] = False
                logger.warning(f"Health check timeout pour {provider_id}")
            except Exception as e:
                health_results[provider_id] = False
                logger.error(f"Health check erreur {provider_id}: {str(e)}")
        
        return health_results
    
    async def generate_response(self,
                               provider_id: str,
                               prompt: str,
                               context: Dict = None) -> Dict:
        """Génère une réponse avec un provider spécifique"""
        
        try:
            provider = await self.get_provider(provider_id)
            result = await provider.generate(prompt, context)
            
            # Ajouter des métadonnées d'orchestration
            result['metadata']['orchestrator'] = {
                'provider_id': provider_id,
                'timestamp': datetime.utcnow().isoformat(),
                'context_provided': context is not None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur génération {provider_id}: {str(e)}")
            return {
                'response': f"ERROR: {str(e)}",
                'metadata': {
                    'provider_id': provider_id,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
    
    async def generate_parallel_responses(self,
                                        provider_ids: List[str],
                                        prompt: str,
                                        context: Dict = None) -> Dict[str, Dict]:
        """Génère des réponses en parallèle avec plusieurs providers"""
        
        logger.info(f"PROCESSING: Génération parallèle avec {len(provider_ids)} providers")
        
        # Créer les tâches asynchrones
        tasks = []
        for provider_id in provider_ids:
            task = asyncio.create_task(
                self.generate_response(provider_id, prompt, context)
            )
            tasks.append((provider_id, task))
        
        # Attendre toutes les réponses avec timeout
        results = {}
        for provider_id, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=30)
                results[provider_id] = result
                logger.debug(f"SUCCESS: {provider_id}: réponse reçue")
            except asyncio.TimeoutError:
                logger.warning(f"TIMEOUT: {provider_id}: timeout")
                results[provider_id] = {
                    'response': "TIMEOUT: Request timeout",
                    'metadata': {'error': 'timeout', 'provider_id': provider_id}
                }
            except Exception as e:
                logger.error(f"ERROR: {provider_id}: {str(e)}")
                results[provider_id] = {
                    'response': f"ERROR: {str(e)}",
                    'metadata': {'error': str(e), 'provider_id': provider_id}
                }
        
        return results
    
    def get_recommended_providers(self, 
                                 use_case: str = "debate",
                                 count: int = 3) -> List[str]:
        """Recommande les meilleurs providers selon le cas d'usage"""
        
        if not self.providers:
            return []
        
        # Stratégies de recommandation selon le cas
        if use_case == "debate":
            # Pour débat: mix de providers différents
            recommended = []
            
            # Préférer Gemini pour la précision
            gemini_providers = [p for p in self.providers.keys() if 'gemini' in p]
            if gemini_providers:
                recommended.extend(gemini_providers[:1])
            
            # Ajouter des modèles Ollama pour diversité
            ollama_providers = [p for p in self.providers.keys() if 'ollama' in p]
            if ollama_providers:
                # Privilégier llama et mistral
                for model in ['llama', 'mistral', 'qwen']:
                    matching = [p for p in ollama_providers if model in p.lower()]
                    if matching and len(recommended) < count:
                        recommended.extend(matching[:1])
            
            # Compléter si nécessaire
            all_providers = list(self.providers.keys())
            for provider in all_providers:
                if provider not in recommended and len(recommended) < count:
                    recommended.append(provider)
            
            return recommended[:count]
        
        elif use_case == "fast":
            # Providers les plus rapides (généralement locaux)
            ollama_first = [p for p in self.providers.keys() if 'ollama' in p]
            gemini_last = [p for p in self.providers.keys() if 'gemini' in p]
            return (ollama_first + gemini_last)[:count]
        
        elif use_case == "accurate":
            # Providers les plus précis (généralement cloud)
            gemini_first = [p for p in self.providers.keys() if 'gemini' in p]
            ollama_last = [p for p in self.providers.keys() if 'ollama' in p]
            return (gemini_first + ollama_last)[:count]
        
        else:
            # Par défaut: retourner les premiers disponibles
            return list(self.providers.keys())[:count]
    
    async def create_debate_setup(self, 
                                 participants_count: int = 3,
                                 include_judge: bool = True,
                                 mixed_providers: bool = True) -> Dict:
        """Crée une configuration de débat optimale"""
        
        if not self.is_initialized:
            raise RuntimeError("Orchestrateur non initialisé")
        
        # Déterminer le nombre d'experts
        experts_count = participants_count
        if include_judge:
            experts_count -= 1  # Réserver une place pour le juge
        
        if experts_count < 2:
            raise ValueError("Au moins 2 experts requis pour un débat")
        
        # Sélectionner les providers pour les experts
        if mixed_providers:
            expert_providers = self.get_recommended_providers("debate", experts_count)
        else:
            # Utiliser le même type de provider
            available = list(self.providers.keys())
            expert_providers = available[:experts_count]
        
        if len(expert_providers) < experts_count:
            raise RuntimeError(f"Pas assez de providers disponibles ({len(expert_providers)}/{experts_count})")
        
        # Configuration des experts
        experts = []
        for i, provider_id in enumerate(expert_providers):
            provider = self.providers[provider_id]
            experts.append({
                "id": f"expert_{i+1}",
                "provider": provider.config.provider,
                "model": provider.config.model_name,
                "temperature": provider.config.temperature,
                "provider_id": provider_id,
                "role": "expert"
            })
        
        # Configuration du juge
        judge = None
        if include_judge:
            # Utiliser un provider différent pour le juge si possible
            judge_providers = [p for p in self.providers.keys() if p not in expert_providers]
            if not judge_providers:
                judge_providers = expert_providers[:1]  # Fallback
            
            judge_provider_id = judge_providers[0]
            judge_provider = self.providers[judge_provider_id]
            
            judge = {
                "id": "judge",
                "provider": judge_provider.config.provider,
                "model": judge_provider.config.model_name,
                "temperature": 0.1,  # Plus conservateur pour le juge
                "provider_id": judge_provider_id,
                "role": "judge"
            }
        
        setup = {
            "experts": experts,
            "judge": judge,
            "total_participants": len(experts) + (1 if judge else 0),
            "mixed_providers": mixed_providers,
            "provider_distribution": self._analyze_provider_distribution(experts, judge)
        }
        
        logger.info(f"SETUP: Configuration débat créée: {len(experts)} experts + {'1 juge' if judge else '0 juge'}")
        
        return setup
    
    def _analyze_provider_distribution(self, experts: List[Dict], judge: Optional[Dict]) -> Dict:
        """Analyse la distribution des providers dans le débat"""
        
        distribution = {'gemini': 0, 'ollama': 0, 'other': 0}
        
        all_participants = experts.copy()
        if judge:
            all_participants.append(judge)
        
        for participant in all_participants:
            provider_type = participant['provider'].lower()
            if provider_type in distribution:
                distribution[provider_type] += 1
            else:
                distribution['other'] += 1
        
        return distribution
    
    async def get_system_metrics(self) -> Dict:
        """Retourne les métriques système de l'orchestrateur"""
        
        providers_health = await self.get_providers_health()
        healthy_count = sum(1 for health in providers_health.values() if health)
        
        total_requests = sum(p.request_count for p in self.providers.values())
        
        return {
            'orchestrator': {
                'initialized': self.is_initialized,
                'initialization_time': self.initialization_time.isoformat() if self.initialization_time else None,
                'uptime_seconds': (datetime.utcnow() - self.initialization_time).total_seconds() if self.initialization_time else 0
            },
            'providers': {
                'total': len(self.providers),
                'healthy': healthy_count,
                'unhealthy': len(self.providers) - healthy_count,
                'total_requests': total_requests,
                'distribution': {
                    'gemini': len([p for p in self.providers.keys() if 'gemini' in p]),
                    'ollama': len([p for p in self.providers.keys() if 'ollama' in p]),
                    'other': len([p for p in self.providers.keys() if 'gemini' not in p and 'ollama' not in p])
                }
            },
            'performance': {
                'average_requests_per_provider': total_requests / max(len(self.providers), 1),
                'providers_health': providers_health
            }
        }
    
    async def shutdown(self):
        """Arrêt propre de l'orchestrateur"""
        
        logger.info("STOP: Arrêt de l'orchestrateur...")
        
        # Nettoyer les providers
        for provider_id, provider in self.providers.items():
            try:
                # Si le provider a une méthode cleanup
                if hasattr(provider, 'cleanup'):
                    await provider.cleanup()
                logger.debug(f"Provider {provider_id} nettoyé")
            except Exception as e:
                logger.warning(f"Erreur nettoyage {provider_id}: {str(e)}")
        
        self.providers.clear()
        self.is_initialized = False
        
        logger.info("SUCCESS: Orchestrateur arrêté")

# Fonction utilitaire pour créer l'orchestrateur avec config
async def create_orchestrator(config: Dict) -> MultiAgentOrchestrator:
    """Crée et initialise un orchestrateur avec une configuration"""
    
    orchestrator = MultiAgentOrchestrator()
    
    provider_configs = config.get('llm_providers', [])
    if not provider_configs:
        logger.warning("Aucune configuration de provider trouvée")
        return orchestrator
    
    await orchestrator.initialize_providers(provider_configs)
    
    return orchestrator