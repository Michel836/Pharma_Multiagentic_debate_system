# llm_providers.py - Providers LLM avec support Gemini et Ollama
import asyncio
import aiohttp
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Pour Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Pour Ollama
try:
    import ollama
except ImportError:
    ollama = None

logger = logging.getLogger(__name__)

@dataclass
class LLMConfig:
    """Configuration unifiée pour tout LLM"""
    provider: str  # 'gemini', 'ollama'
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2048
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    timeout: int = 30

class BaseLLMProvider(ABC):
    """Interface abstraite pour tous les providers LLM"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.is_initialized = False
        self.last_request_time = 0
        self.request_count = 0
        
    @abstractmethod
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse à partir du prompt"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie que le modèle est disponible"""
        pass
    
    async def initialize(self) -> bool:
        """Initialise le provider"""
        try:
            success = await self.health_check()
            self.is_initialized = success
            if success:
                logger.info(f"SUCCESS: Provider {self.config.provider}:{self.config.model_name} initialisé")
            else:
                logger.error(f"ERROR: Échec initialisation {self.config.provider}:{self.config.model_name}")
            return success
        except Exception as e:
            logger.error(f"ERROR: Erreur initialisation {self.config.provider}: {str(e)}")
            return False
    
    def _rate_limit(self, min_interval: float = 1.0):
        """Applique un rate limiting simple"""
        current_time = time.time()
        if current_time - self.last_request_time < min_interval:
            sleep_time = min_interval - (current_time - self.last_request_time)
            time.sleep(sleep_time)
        self.last_request_time = time.time()
        self.request_count += 1

class GeminiProvider(BaseLLMProvider):
    """Provider pour Gemini API"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.model = None
        
        if not genai:
            raise ImportError("google-generativeai non installé. Installer avec: pip install google-generativeai")
        
        if not config.api_key:
            raise ValueError("Clé API Gemini requise")
    
    async def initialize(self) -> bool:
        """Initialise le client Gemini"""
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Configuration du modèle
            generation_config = {
                'temperature': self.config.temperature,
                'max_output_tokens': self.config.max_tokens,
                'top_p': 0.9,
                'top_k': 40
            }
            
            # Paramètres de sécurité pour contexte pharma
            safety_settings = {
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE', 
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
            }
            
            self.model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            return await super().initialize()
            
        except Exception as e:
            logger.error(f"Erreur initialisation Gemini: {str(e)}")
            return False
    
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse via Gemini"""
        
        if not self.is_initialized:
            raise RuntimeError(f"Provider {self.config.provider} non initialisé")
        
        start_time = time.time()
        
        try:
            # Rate limiting
            self._rate_limit(1.0)  # 1 requête par seconde max
            
            # Préparer le prompt avec contexte
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Génération asynchrone
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(full_prompt)
            )
            
            # Extraction du texte
            generated_text = response.text if response.text else "ERROR: Réponse vide de Gemini"
            
            # Métriques
            duration_ms = (time.time() - start_time) * 1000
            
            # Calcul approximatif des tokens
            input_tokens = len(full_prompt.split())
            output_tokens = len(generated_text.split())
            total_tokens = input_tokens + output_tokens
            
            # Analyse de la qualité de réponse
            confidence = self._calculate_confidence(response, generated_text)
            
            result = {
                'response': generated_text,
                'metadata': {
                    'provider': 'gemini',
                    'model': self.config.model_name,
                    'duration_ms': duration_ms,
                    'tokens_used': total_tokens,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'confidence': confidence,
                    'finish_reason': self._get_finish_reason(response),
                    'safety_ratings': self._extract_safety_ratings(response)
                }
            }
            
            logger.debug(f"Gemini response: {duration_ms:.0f}ms, {total_tokens} tokens, confidence: {confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur génération Gemini: {str(e)}")
            return {
                'response': f"ERROR: Erreur Gemini: {str(e)}",
                'metadata': {
                    'provider': 'gemini',
                    'model': self.config.model_name,
                    'error': str(e),
                    'duration_ms': (time.time() - start_time) * 1000,
                    'confidence': 0.0
                }
            }
    
    async def health_check(self) -> bool:
        """Vérifie que Gemini API est accessible"""
        
        try:
            if not self.model:
                return False
                
            # Test simple
            test_response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(
                    "Hello",
                    generation_config={'max_output_tokens': 10}
                )
            )
            
            return bool(test_response.text)
            
        except Exception as e:
            logger.error(f"Health check Gemini échoué: {str(e)}")
            return False
    
    def _prepare_prompt(self, prompt: str, context: Dict = None) -> str:
        """Prépare le prompt avec contexte éventuel"""
        
        if not context:
            return prompt
        
        # Ajout du contexte RAG si disponible
        if 'rag_results' in context:
            rag_content = "\\n".join([
                f"- {result.get('content', '')[:150]}..."
                for result in context['rag_results'][:3]
            ])
            
            return f"""Contexte de la base de connaissances :
{rag_content}

Question/Demande : {prompt}

Veuillez répondre en vous basant sur le contexte fourni, en restant précis et factuel."""
        
        return prompt
    
    def _calculate_confidence(self, response, generated_text: str) -> float:
        """Calcule un score de confiance basé sur les métriques Gemini"""
        
        confidence = 0.5  # Base
        
        try:
            # Vérifier les safety ratings
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Si pas de blocage de sécurité
                if hasattr(candidate, 'finish_reason'):
                    if str(candidate.finish_reason) == 'FinishReason.STOP':
                        confidence += 0.3
                
                # Analyser les safety ratings
                if hasattr(candidate, 'safety_ratings'):
                    blocked_ratings = [
                        r for r in candidate.safety_ratings
                        if str(r.probability) in ['HIGH', 'MEDIUM']
                    ]
                    if len(blocked_ratings) == 0:
                        confidence += 0.2
            
            # Longueur de réponse appropriée
            if 50 < len(generated_text) < 1000:
                confidence += 0.1
            
            # Pas d'erreurs évidentes
            if "ERROR:" not in generated_text and "erreur" not in generated_text.lower():
                confidence += 0.1
                
        except Exception:
            pass  # Garder confiance de base
        
        return min(confidence, 1.0)
    
    def _get_finish_reason(self, response) -> str:
        """Extrait la raison de fin de génération"""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                return str(response.candidates[0].finish_reason)
        except:
            pass
        return "UNKNOWN"
    
    def _extract_safety_ratings(self, response) -> List[Dict]:
        """Extrait les ratings de sécurité"""
        try:
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    return [
                        {
                            'category': str(rating.category),
                            'probability': str(rating.probability)
                        }
                        for rating in candidate.safety_ratings
                    ]
        except:
            pass
        return []

class OllamaProvider(BaseLLMProvider):
    """Provider pour modèles Ollama locaux"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = None
        
        if not ollama:
            raise ImportError("ollama non installé. Installer avec: pip install ollama")
        
        self.api_url = config.api_url or 'http://localhost:11434'
    
    async def initialize(self) -> bool:
        """Initialise le client Ollama"""
        try:
            self.client = ollama.AsyncClient(host=self.api_url)
            return await super().initialize()
        except Exception as e:
            logger.error(f"Erreur initialisation Ollama: {str(e)}")
            return False
    
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse via Ollama"""
        
        if not self.is_initialized:
            raise RuntimeError(f"Provider {self.config.provider} non initialisé")
        
        start_time = time.time()
        
        try:
            # Préparer le prompt avec contexte
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Configuration du modèle
            options = {
                'temperature': self.config.temperature,
                'num_predict': self.config.max_tokens,
                'top_p': 0.9,
                'repeat_penalty': 1.1,
                'stop': ['Human:', 'User:']  # Stop tokens
            }
            
            # Appel Ollama
            response = await self.client.chat(
                model=self.config.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': self._get_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': full_prompt
                    }
                ],
                options=options
            )
            
            # Extraction de la réponse
            generated_text = response['message']['content']
            
            # Métriques
            duration_ms = (time.time() - start_time) * 1000
            
            # Calcul des tokens (approximatif)
            input_tokens = response.get('prompt_eval_count', len(full_prompt.split()))
            output_tokens = response.get('eval_count', len(generated_text.split()))
            total_tokens = input_tokens + output_tokens
            
            # Métriques de performance Ollama
            load_duration = response.get('load_duration', 0) / 1e6  # Convert to ms
            eval_duration = response.get('eval_duration', 0) / 1e6
            
            # Score de confiance
            confidence = self._calculate_confidence(response, generated_text, duration_ms)
            
            result = {
                'response': generated_text,
                'metadata': {
                    'provider': 'ollama',
                    'model': self.config.model_name,
                    'duration_ms': duration_ms,
                    'tokens_used': total_tokens,
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens,
                    'confidence': confidence,
                    'load_duration_ms': load_duration,
                    'eval_duration_ms': eval_duration,
                    'tokens_per_second': output_tokens / max(eval_duration / 1000, 0.001) if eval_duration > 0 else 0
                }
            }
            
            logger.debug(f"Ollama response: {duration_ms:.0f}ms, {total_tokens} tokens, {confidence:.2f} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur génération Ollama: {str(e)}")
            return {
                'response': f"ERROR: Erreur Ollama ({self.config.model_name}): {str(e)}",
                'metadata': {
                    'provider': 'ollama',
                    'model': self.config.model_name,
                    'error': str(e),
                    'duration_ms': (time.time() - start_time) * 1000,
                    'confidence': 0.0
                }
            }
    
    async def health_check(self) -> bool:
        """Vérifie que Ollama est accessible et le modèle est chargé"""
        
        try:
            if not self.client:
                return False
            
            # Liste les modèles disponibles
            models = await self.client.list()
            
            # Vérifie que notre modèle est disponible
            model_names = [m['name'] for m in models['models']]
            
            if self.config.model_name not in model_names:
                logger.warning(f"Modèle {self.config.model_name} non trouvé, tentative de pull...")
                
                # Tente de télécharger le modèle
                try:
                    await asyncio.wait_for(
                        self.client.pull(self.config.model_name),
                        timeout=300  # 5 minutes timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Timeout lors du téléchargement de {self.config.model_name}")
                    return False
            
            # Test rapide
            test_response = await self.client.generate(
                model=self.config.model_name,
                prompt="Hello",
                options={'num_predict': 5}
            )
            
            return bool(test_response.get('response'))
            
        except Exception as e:
            logger.error(f"Health check Ollama échoué: {str(e)}")
            return False
    
    def _get_system_prompt(self) -> str:
        """Retourne le prompt système pour les modèles Ollama"""
        return """You are a pharmaceutical research expert participating in a scientific debate. 
        
Rules:
- Be precise and factual
- Cite scientific evidence when possible  
- Avoid speculation
- Keep responses concise and focused
- Use professional pharmaceutical terminology
- If uncertain, clearly state limitations"""
    
    def _prepare_prompt(self, prompt: str, context: Dict = None) -> str:
        """Prépare le prompt avec contexte RAG si disponible"""
        
        if not context or 'rag_results' not in context:
            return prompt
        
        # Injection du contexte RAG
        context_text = "\\n".join([
            f"- {result.get('content', '')[:200]}..."
            for result in context['rag_results'][:3]
        ])
        
        return f"""Knowledge Base Context:
{context_text}

User Question: {prompt}

Please provide a comprehensive answer based on the context provided and your pharmaceutical expertise."""
    
    def _calculate_confidence(self, response: Dict, generated_text: str, duration_ms: float) -> float:
        """Calcule un score de confiance basé sur les métriques Ollama"""
        
        confidence = 0.5  # Base
        
        # Vitesse de génération (modèles locaux plus rapides = plus sûrs)
        eval_duration = response.get('eval_duration', 0)
        if eval_duration > 0:
            tokens_per_second = response.get('eval_count', 0) / (eval_duration / 1e9)
            if tokens_per_second > 20:
                confidence += 0.2
            elif tokens_per_second > 10:
                confidence += 0.1
        
        # Longueur de réponse appropriée
        if 30 < len(generated_text) < 800:
            confidence += 0.2
        
        # Pas d'erreurs système évidentes
        if "ERROR:" not in generated_text:
            confidence += 0.1
        
        # Durée raisonnable (pas de timeout)
        if duration_ms < 30000:  # Moins de 30 secondes
            confidence += 0.1
        
        # Bonus si réponse structurée
        if any(marker in generated_text for marker in ['-', '1.', '2.', '•']):
            confidence += 0.1
        
        return min(confidence, 1.0)

# Factory function pour créer les providers
def get_provider(provider_type: str, model_name: str, **kwargs) -> BaseLLMProvider:
    """Factory pour créer un provider LLM"""
    
    config = LLMConfig(
        provider=provider_type,
        model_name=model_name,
        **kwargs
    )
    
    if provider_type.lower() == 'gemini':
        return GeminiProvider(config)
    elif provider_type.lower() == 'ollama':
        return OllamaProvider(config)
    else:
        raise ValueError(f"Provider non supporté: {provider_type}")

# Configuration des modèles disponibles
AVAILABLE_MODELS = {
    'gemini': [
        'gemini-pro',
        'gemini-pro-vision',
        'gemini-1.5-pro',
        'gemini-1.5-flash'
    ],
    'ollama': [
        'llama3.2',
        'llama3.1',
        'mistral:7b',
        'qwen2.5:7b',
        'phi3:medium',
        'codellama:7b',
        'neural-chat:7b'
    ]
}

def list_available_models() -> Dict[str, List[str]]:
    """Liste les modèles disponibles par provider"""
    return AVAILABLE_MODELS.copy()

async def test_all_providers(config_list: List[LLMConfig]) -> Dict[str, bool]:
    """Teste tous les providers configurés"""
    
    results = {}
    
    for config in config_list:
        provider_id = f"{config.provider}_{config.model_name}"
        
        try:
            provider = get_provider(config.provider, config.model_name, **config.__dict__)
            success = await provider.initialize()
            results[provider_id] = success
            
            if success:
                logger.info(f"SUCCESS: {provider_id} : OK")
            else:
                logger.error(f"ERROR: {provider_id} : ÉCHEC")
                
        except Exception as e:
            logger.error(f"ERROR: {provider_id} : ERREUR - {str(e)}")
            results[provider_id] = False
    
    return results