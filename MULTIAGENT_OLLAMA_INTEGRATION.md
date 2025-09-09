# 🔄 INTÉGRATION OLLAMA - SYSTÈME MULTIAGENT HYBRIDE

*Extension du système pour support multi-LLM avec modèles locaux*

---

## 🎯 OBJECTIF

Permettre le **challenge entre Gemini (cloud) et modèles Ollama (local)** pour une validation croisée encore plus robuste et des tests comparatifs.

---

## 🏗️ ARCHITECTURE HYBRIDE ÉTENDUE

```
┌─────────────────────────────────────────────────────────────────┐
│                     UTILISATEUR R&D PHARMA                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │
         ┌────────▼────────┐
         │  LLM ROUTER     │ ◄── Sélection intelligente
         │  & ORCHESTRATOR │     Cloud vs Local
         └────────┬────────┘
                  │
    ┌─────────────┴───────────────────────────┐
    │                                         │
┌───▼─────────┐                    ┌─────────▼────────┐
│ CLOUD AGENTS│                    │  LOCAL AGENTS    │
├─────────────┤                    ├──────────────────┤
│ Gemini Pro  │                    │ Llama 3.2       │
│ Gemini Ultra│                    │ Mistral 7B      │
│ Claude API  │                    │ Qwen 2.5        │
└─────────────┘                    │ Phi-3           │
                                   └──────────────────┘
                  │
         ┌────────▼────────┐
         │ CROSS-VALIDATION│ ◄── Challenge Cloud vs Local
         │    ENGINE       │     + Consensus building
         └─────────────────┘
```

---

## 💻 IMPLÉMENTATION COUCHE D'ABSTRACTION LLM

### 1. INTERFACE LLM UNIVERSELLE

```python
# llm_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio
import aiohttp
import json

@dataclass
class LLMConfig:
    """Configuration unifiée pour tout LLM"""
    provider: str  # 'gemini', 'ollama', 'openai', etc.
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
        self.logger = PharmaMultiAgentLogger(f"{config.provider}_{config.model_name}")
        
    @abstractmethod
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse à partir du prompt"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Vérifie que le modèle est disponible"""
        pass
    
    async def log_interaction(self, prompt: str, response: str, metadata: Dict):
        """Log unifié pour tous les providers"""
        await self.logger.log_agent_interaction(
            trace_id=metadata.get('trace_id'),
            input_text=prompt,
            output_text=response,
            metadata={
                'provider': self.config.provider,
                'model': self.config.model_name,
                'temperature': self.config.temperature,
                **metadata
            }
        )
```

### 2. PROVIDER OLLAMA

```python
# ollama_provider.py
import ollama
from typing import Dict, Any
import time

class OllamaProvider(BaseLLMProvider):
    """Provider pour modèles Ollama locaux"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = ollama.AsyncClient(
            host=config.api_url or 'http://localhost:11434'
        )
        
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse via Ollama"""
        
        start_time = time.time()
        
        try:
            # Préparer le prompt avec contexte
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Appel Ollama
            response = await self.client.chat(
                model=self.config.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a pharmaceutical R&D expert assistant. Be precise and avoid hallucinations.'
                    },
                    {
                        'role': 'user',
                        'content': full_prompt
                    }
                ],
                options={
                    'temperature': self.config.temperature,
                    'num_predict': self.config.max_tokens,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1
                }
            )
            
            # Extraction de la réponse
            generated_text = response['message']['content']
            
            # Métriques
            duration_ms = (time.time() - start_time) * 1000
            tokens_used = response.get('eval_count', 0) + response.get('prompt_eval_count', 0)
            
            # Log de l'interaction
            await self.log_interaction(
                prompt=prompt,
                response=generated_text,
                metadata={
                    'duration_ms': duration_ms,
                    'tokens_used': tokens_used,
                    'model_load_duration': response.get('load_duration', 0) / 1e6,  # Convert to ms
                    'eval_duration': response.get('eval_duration', 0) / 1e6
                }
            )
            
            return {
                'response': generated_text,
                'metadata': {
                    'provider': 'ollama',
                    'model': self.config.model_name,
                    'duration_ms': duration_ms,
                    'tokens_used': tokens_used,
                    'confidence': self._calculate_confidence(response)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Ollama generation error: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Vérifie que Ollama est accessible et le modèle est chargé"""
        
        try:
            # Liste les modèles disponibles
            models = await self.client.list()
            
            # Vérifie que notre modèle est disponible
            model_names = [m['name'] for m in models['models']]
            
            if self.config.model_name not in model_names:
                # Tente de pull le modèle
                self.logger.info(f"Pulling model {self.config.model_name}...")
                await self.client.pull(self.config.model_name)
            
            # Test rapide
            test_response = await self.client.generate(
                model=self.config.model_name,
                prompt="Hello",
                options={'num_predict': 1}
            )
            
            return bool(test_response)
            
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    def _calculate_confidence(self, response: Dict) -> float:
        """Calcule un score de confiance basé sur les métriques Ollama"""
        
        # Facteurs de confiance
        eval_duration = response.get('eval_duration', 0)
        tokens_per_second = response.get('eval_count', 0) / max(eval_duration / 1e9, 1)
        
        # Score basé sur la vitesse de génération (plus c'est rapide, plus le modèle est "sûr")
        if tokens_per_second > 50:
            confidence = 0.9
        elif tokens_per_second > 20:
            confidence = 0.7
        else:
            confidence = 0.5
            
        return confidence
    
    def _prepare_prompt(self, prompt: str, context: Dict = None) -> str:
        """Prépare le prompt avec contexte RAG si disponible"""
        
        if not context or 'rag_results' not in context:
            return prompt
        
        # Injection du contexte RAG
        context_text = "\n".join([
            f"- {result['content'][:200]}..." 
            for result in context['rag_results'][:3]
        ])
        
        return f"""Context from knowledge base:
{context_text}

User question: {prompt}

Please provide a comprehensive answer based on the context provided."""
```

### 3. PROVIDER GEMINI ADAPTÉ

```python
# gemini_provider.py
import google.generativeai as genai
from typing import Dict, Any
import time

class GeminiProvider(BaseLLMProvider):
    """Provider pour Gemini API"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(
            model_name=config.model_name,
            generation_config={
                'temperature': config.temperature,
                'max_output_tokens': config.max_tokens,
                'top_p': 0.9
            },
            safety_settings={
                'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE'
            }
        )
        
    async def generate(self, prompt: str, context: Dict = None) -> Dict:
        """Génère une réponse via Gemini"""
        
        start_time = time.time()
        
        try:
            # Préparer le prompt
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Génération
            response = await self.model.generate_content_async(full_prompt)
            
            # Extraction
            generated_text = response.text
            
            # Métriques
            duration_ms = (time.time() - start_time) * 1000
            
            # Calcul des tokens (approximatif pour Gemini)
            tokens_used = len(full_prompt.split()) + len(generated_text.split())
            
            # Log
            await self.log_interaction(
                prompt=prompt,
                response=generated_text,
                metadata={
                    'duration_ms': duration_ms,
                    'tokens_used': tokens_used,
                    'finish_reason': response.candidates[0].finish_reason.name,
                    'safety_ratings': [
                        {'category': r.category.name, 'probability': r.probability.name}
                        for r in response.candidates[0].safety_ratings
                    ]
                }
            )
            
            return {
                'response': generated_text,
                'metadata': {
                    'provider': 'gemini',
                    'model': self.config.model_name,
                    'duration_ms': duration_ms,
                    'tokens_used': tokens_used,
                    'confidence': self._calculate_confidence(response)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Gemini generation error: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Vérifie que Gemini API est accessible"""
        
        try:
            # Test simple
            response = await self.model.generate_content_async(
                "Say 'OK'",
                generation_config={'max_output_tokens': 10}
            )
            return bool(response.text)
        except:
            return False
    
    def _calculate_confidence(self, response) -> float:
        """Score de confiance basé sur les safety ratings"""
        
        safety_ratings = response.candidates[0].safety_ratings
        
        # Si des contenus sont bloqués, confiance réduite
        blocked_count = sum(1 for r in safety_ratings if r.probability.name == 'HIGH')
        
        if blocked_count == 0:
            return 0.9
        elif blocked_count == 1:
            return 0.7
        else:
            return 0.5
```

### 4. ORCHESTRATEUR MULTI-PROVIDER

```python
# multi_provider_orchestrator.py
from typing import Dict, List, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class MultiProviderOrchestrator:
    """Orchestrateur pour gérer multiple LLM providers"""
    
    def __init__(self):
        self.providers = {}
        self.logger = PharmaMultiAgentLogger("multi_provider_orchestrator")
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    async def initialize_providers(self, configs: List[LLMConfig]):
        """Initialise tous les providers configurés"""
        
        for config in configs:
            provider_id = f"{config.provider}_{config.model_name}"
            
            if config.provider == 'ollama':
                provider = OllamaProvider(config)
            elif config.provider == 'gemini':
                provider = GeminiProvider(config)
            else:
                self.logger.warning(f"Unknown provider: {config.provider}")
                continue
            
            # Health check
            if await provider.health_check():
                self.providers[provider_id] = provider
                self.logger.info(f"Provider {provider_id} initialized successfully")
            else:
                self.logger.error(f"Provider {provider_id} health check failed")
    
    async def challenge_providers(self, 
                                 prompt: str,
                                 provider_ids: List[str] = None,
                                 context: Dict = None) -> Dict:
        """Lance un challenge entre plusieurs providers"""
        
        if provider_ids is None:
            provider_ids = list(self.providers.keys())
        
        # Lancer toutes les générations en parallèle
        tasks = []
        for provider_id in provider_ids:
            if provider_id in self.providers:
                provider = self.providers[provider_id]
                task = asyncio.create_task(
                    self._generate_with_timeout(provider, prompt, context)
                )
                tasks.append((provider_id, task))
        
        # Attendre toutes les réponses
        responses = {}
        for provider_id, task in tasks:
            try:
                result = await task
                responses[provider_id] = result
            except Exception as e:
                self.logger.error(f"Provider {provider_id} failed: {str(e)}")
                responses[provider_id] = {
                    'response': None,
                    'error': str(e),
                    'metadata': {'provider': provider_id.split('_')[0]}
                }
        
        # Analyse comparative
        analysis = await self._analyze_responses(responses, prompt)
        
        return {
            'prompt': prompt,
            'responses': responses,
            'analysis': analysis,
            'consensus': self._build_consensus(responses, analysis)
        }
    
    async def _generate_with_timeout(self, 
                                    provider: BaseLLMProvider,
                                    prompt: str,
                                    context: Dict,
                                    timeout: int = 30) -> Dict:
        """Génère avec timeout pour éviter les blocages"""
        
        try:
            return await asyncio.wait_for(
                provider.generate(prompt, context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise Exception(f"Provider timeout after {timeout}s")
    
    async def _analyze_responses(self, responses: Dict, prompt: str) -> Dict:
        """Analyse comparative des réponses"""
        
        analysis = {
            'total_providers': len(responses),
            'successful_responses': sum(1 for r in responses.values() if r.get('response')),
            'average_duration': None,
            'consensus_score': 0,
            'divergence_points': [],
            'provider_rankings': []
        }
        
        # Calcul durée moyenne
        durations = [
            r['metadata']['duration_ms'] 
            for r in responses.values() 
            if r.get('metadata', {}).get('duration_ms')
        ]
        if durations:
            analysis['average_duration'] = sum(durations) / len(durations)
        
        # Analyse de consensus (simplifiée)
        valid_responses = [
            r['response'] 
            for r in responses.values() 
            if r.get('response')
        ]
        
        if len(valid_responses) >= 2:
            # Calcul de similarité basique
            analysis['consensus_score'] = self._calculate_consensus(valid_responses)
        
        # Ranking des providers
        for provider_id, response in responses.items():
            if response.get('response'):
                score = self._score_response(response, analysis['consensus_score'])
                analysis['provider_rankings'].append({
                    'provider': provider_id,
                    'score': score,
                    'duration_ms': response['metadata'].get('duration_ms', 0),
                    'confidence': response['metadata'].get('confidence', 0)
                })
        
        # Tri par score
        analysis['provider_rankings'].sort(key=lambda x: x['score'], reverse=True)
        
        return analysis
    
    def _calculate_consensus(self, responses: List[str]) -> float:
        """Calcule le niveau de consensus entre réponses"""
        
        # Implémentation simplifiée - à améliorer avec NLP
        # Compare la longueur et les mots clés communs
        
        if not responses:
            return 0.0
        
        # Extraction des mots clés
        keywords_sets = []
        for response in responses:
            words = set(response.lower().split())
            # Filtrer les mots communs
            keywords = {w for w in words if len(w) > 4}
            keywords_sets.append(keywords)
        
        # Calcul intersection
        if len(keywords_sets) == 1:
            return 1.0
        
        common_keywords = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            common_keywords = common_keywords.intersection(kw_set)
        
        # Score basé sur le ratio de mots communs
        avg_keywords = sum(len(kw) for kw in keywords_sets) / len(keywords_sets)
        consensus = len(common_keywords) / max(avg_keywords, 1)
        
        return min(consensus, 1.0)
    
    def _build_consensus(self, responses: Dict, analysis: Dict) -> str:
        """Construit une réponse consensus à partir de toutes les réponses"""
        
        valid_responses = [
            r['response'] 
            for r in responses.values() 
            if r.get('response')
        ]
        
        if not valid_responses:
            return "No valid responses received from any provider."
        
        if len(valid_responses) == 1:
            return valid_responses[0]
        
        # Stratégie simple : prendre la meilleure réponse selon le ranking
        if analysis['provider_rankings']:
            best_provider = analysis['provider_rankings'][0]['provider']
            return responses[best_provider]['response']
        
        # Fallback : première réponse valide
        return valid_responses[0]
    
    def _score_response(self, response: Dict, consensus_score: float) -> float:
        """Score une réponse individuelle"""
        
        score = 0.0
        
        # Facteurs de scoring
        if response.get('response'):
            score += 0.3  # Réponse valide
            
            # Longueur de réponse (ni trop court ni trop long)
            length = len(response['response'])
            if 100 < length < 2000:
                score += 0.2
            
            # Confiance du modèle
            confidence = response['metadata'].get('confidence', 0)
            score += confidence * 0.2
            
            # Vitesse de réponse
            duration = response['metadata'].get('duration_ms', 10000)
            if duration < 1000:
                score += 0.2
            elif duration < 5000:
                score += 0.1
            
            # Bonus consensus
            score += consensus_score * 0.1
        
        return min(score, 1.0)
```

### 5. CONFIGURATION HYBRIDE

```yaml
# config/llm_providers.yaml
providers:
  # Gemini Cloud
  - provider: gemini
    model_name: gemini-pro
    temperature: 0.3
    max_tokens: 2048
    api_key: ${GEMINI_API_KEY}
    enabled: true
    
  - provider: gemini
    model_name: gemini-pro
    temperature: 0.7
    max_tokens: 2048
    api_key: ${GEMINI_API_KEY}
    enabled: true

  # Ollama Local
  - provider: ollama
    model_name: llama3.2:latest
    temperature: 0.3
    max_tokens: 2048
    api_url: http://localhost:11434
    enabled: true
    
  - provider: ollama
    model_name: mistral:7b
    temperature: 0.5
    max_tokens: 2048
    api_url: http://localhost:11434
    enabled: true
    
  - provider: ollama
    model_name: qwen2.5:7b
    temperature: 0.4
    max_tokens: 2048
    api_url: http://localhost:11434
    enabled: true
    
  - provider: ollama
    model_name: phi3:medium
    temperature: 0.6
    max_tokens: 2048
    api_url: http://localhost:11434
    enabled: false  # Désactivé par défaut

# Stratégies de challenge
challenge_strategies:
  
  # Challenge Gemini vs Gemini (original)
  gemini_only:
    providers:
      - gemini_gemini-pro_0.3
      - gemini_gemini-pro_0.7
    description: "Challenge entre instances Gemini"
    
  # Challenge Ollama local uniquement
  local_only:
    providers:
      - ollama_llama3.2:latest
      - ollama_mistral:7b
      - ollama_qwen2.5:7b
    description: "Challenge entre modèles locaux"
    
  # Challenge Hybride Cloud vs Local
  hybrid_challenge:
    providers:
      - gemini_gemini-pro_0.3
      - ollama_llama3.2:latest
      - ollama_mistral:7b
    description: "Challenge Cloud vs Local"
    
  # Challenge complet
  all_providers:
    providers: all
    description: "Tous les providers activés"

# Configuration des tests comparatifs
testing:
  benchmark_queries:
    - "What is the mechanism of action for aspirin?"
    - "Explain the process of protein synthesis"
    - "What are the safety considerations for handling cytotoxic drugs?"
    
  metrics_to_track:
    - response_time
    - token_usage
    - consensus_score
    - hallucination_rate
    - factual_accuracy
```

### 6. SCRIPT DE TEST COMPARATIF

```python
# test_comparative.py
import asyncio
import json
from datetime import datetime
from typing import List, Dict
import pandas as pd

class ComparativeTestRunner:
    """Runner pour tests comparatifs entre providers"""
    
    def __init__(self):
        self.orchestrator = MultiProviderOrchestrator()
        self.results = []
        
    async def run_comparative_test(self, 
                                  test_queries: List[str],
                                  strategy: str = 'hybrid_challenge') -> Dict:
        """Execute un test comparatif complet"""
        
        print(f"🧪 Starting comparative test with strategy: {strategy}")
        print(f"📝 Testing {len(test_queries)} queries")
        
        # Charger configuration
        config = self._load_config()
        
        # Initialiser providers
        await self.orchestrator.initialize_providers(
            self._get_provider_configs(config, strategy)
        )
        
        # Executer tests
        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}/{len(test_queries)}] Testing: {query[:50]}...")
            
            result = await self.orchestrator.challenge_providers(
                prompt=query,
                context={'test_run': True, 'strategy': strategy}
            )
            
            # Enregistrer résultats
            self.results.append({
                'timestamp': datetime.utcnow().isoformat(),
                'query': query,
                'strategy': strategy,
                'responses': result['responses'],
                'analysis': result['analysis']
            })
            
            # Afficher résumé
            self._print_result_summary(result)
        
        # Générer rapport
        report = self._generate_report()
        
        # Sauvegarder résultats
        self._save_results(report)
        
        return report
    
    def _print_result_summary(self, result: Dict):
        """Affiche un résumé du résultat"""
        
        analysis = result['analysis']
        
        print(f"  ✅ Successful: {analysis['successful_responses']}/{analysis['total_providers']}")
        print(f"  ⏱️ Avg duration: {analysis.get('average_duration', 0):.0f}ms")
        print(f"  🤝 Consensus: {analysis.get('consensus_score', 0):.1%}")
        
        if analysis['provider_rankings']:
            print("  🏆 Rankings:")
            for rank in analysis['provider_rankings'][:3]:
                print(f"     {rank['provider']}: {rank['score']:.2f}")
    
    def _generate_report(self) -> Dict:
        """Génère un rapport comparatif complet"""
        
        report = {
            'summary': {
                'total_tests': len(self.results),
                'timestamp': datetime.utcnow().isoformat(),
                'providers_tested': set()
            },
            'provider_performance': {},
            'consensus_analysis': [],
            'recommendations': []
        }
        
        # Analyse par provider
        provider_stats = {}
        
        for result in self.results:
            for provider_id, response in result['responses'].items():
                if provider_id not in provider_stats:
                    provider_stats[provider_id] = {
                        'success_count': 0,
                        'total_count': 0,
                        'total_duration': 0,
                        'scores': []
                    }
                
                stats = provider_stats[provider_id]
                stats['total_count'] += 1
                
                if response.get('response'):
                    stats['success_count'] += 1
                    stats['total_duration'] += response['metadata'].get('duration_ms', 0)
                
                # Trouver le score dans l'analyse
                for ranking in result['analysis']['provider_rankings']:
                    if ranking['provider'] == provider_id:
                        stats['scores'].append(ranking['score'])
        
        # Calculer moyennes
        for provider_id, stats in provider_stats.items():
            report['provider_performance'][provider_id] = {
                'success_rate': stats['success_count'] / max(stats['total_count'], 1),
                'avg_duration_ms': stats['total_duration'] / max(stats['success_count'], 1),
                'avg_score': sum(stats['scores']) / max(len(stats['scores']), 1) if stats['scores'] else 0,
                'total_tests': stats['total_count']
            }
            report['summary']['providers_tested'].add(provider_id)
        
        # Recommandations
        report['recommendations'] = self._generate_recommendations(report['provider_performance'])
        
        return report
    
    def _generate_recommendations(self, performance: Dict) -> List[str]:
        """Génère des recommandations basées sur les performances"""
        
        recommendations = []
        
        # Trouver le meilleur performer
        best_provider = max(
            performance.items(),
            key=lambda x: x[1]['avg_score']
        )[0] if performance else None
        
        if best_provider:
            recommendations.append(
                f"✅ Best overall performer: {best_provider} "
                f"(score: {performance[best_provider]['avg_score']:.2f})"
            )
        
        # Identifier les providers rapides
        fast_providers = [
            p for p, stats in performance.items()
            if stats['avg_duration_ms'] < 1000
        ]
        if fast_providers:
            recommendations.append(
                f"⚡ Fastest providers: {', '.join(fast_providers)}"
            )
        
        # Identifier les providers fiables
        reliable_providers = [
            p for p, stats in performance.items()
            if stats['success_rate'] > 0.95
        ]
        if reliable_providers:
            recommendations.append(
                f"🛡️ Most reliable: {', '.join(reliable_providers)}"
            )
        
        # Recommandation hybride
        has_cloud = any('gemini' in p for p in performance.keys())
        has_local = any('ollama' in p for p in performance.keys())
        
        if has_cloud and has_local:
            recommendations.append(
                "🔄 Hybrid approach recommended: Use local models for "
                "non-critical queries and cloud for complex analysis"
            )
        
        return recommendations
    
    def _save_results(self, report: Dict):
        """Sauvegarde les résultats du test"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder le rapport JSON
        with open(f'test_results/comparative_test_{timestamp}.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Créer un DataFrame pour analyse
        df_data = []
        for result in self.results:
            for provider_id, response in result['responses'].items():
                df_data.append({
                    'query': result['query'][:50],
                    'provider': provider_id,
                    'success': bool(response.get('response')),
                    'duration_ms': response.get('metadata', {}).get('duration_ms', None),
                    'confidence': response.get('metadata', {}).get('confidence', None),
                    'consensus_score': result['analysis'].get('consensus_score', None)
                })
        
        df = pd.DataFrame(df_data)
        df.to_csv(f'test_results/comparative_test_{timestamp}.csv', index=False)
        
        print(f"\n📊 Results saved to test_results/comparative_test_{timestamp}.*")

# Script principal de test
async def main():
    """Lance un test comparatif complet"""
    
    runner = ComparativeTestRunner()
    
    # Questions de test pharma
    test_queries = [
        "What is the mechanism of action for metformin in type 2 diabetes?",
        "Explain the pharmacokinetics of acetaminophen",
        "What are the main drug-drug interactions with warfarin?",
        "Describe the synthesis pathway for aspirin",
        "What are the FDA requirements for Phase III clinical trials?"
    ]
    
    # Test stratégie hybride
    report = await runner.run_comparative_test(
        test_queries=test_queries,
        strategy='hybrid_challenge'
    )
    
    # Afficher rapport final
    print("\n" + "="*60)
    print("📈 FINAL REPORT")
    print("="*60)
    
    print("\n🏆 Provider Performance:")
    for provider, stats in report['provider_performance'].items():
        print(f"\n  {provider}:")
        print(f"    Success rate: {stats['success_rate']:.1%}")
        print(f"    Avg duration: {stats['avg_duration_ms']:.0f}ms")
        print(f"    Avg score: {stats['avg_score']:.2f}")
    
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🚀 INSTALLATION OLLAMA

### Installation Ollama sur Windows

```bash
# 1. Télécharger Ollama
# https://ollama.ai/download/windows

# 2. Installer les modèles
ollama pull llama3.2
ollama pull mistral:7b
ollama pull qwen2.5:7b
ollama pull phi3:medium

# 3. Vérifier l'installation
ollama list

# 4. Démarrer le serveur (automatique sur Windows)
# Le serveur tourne sur http://localhost:11434
```

### Configuration Python

```bash
# Installer les dépendances
pip install ollama
pip install google-generativeai
pip install pandas
pip install aiohttp
```

---

## 📊 DASHBOARD COMPARATIF

```html
<!-- comparative_dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>LLM Comparative Testing Dashboard</title>
    <style>
        .provider-card {
            display: inline-block;
            width: 200px;
            margin: 10px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
        }
        .provider-gemini { border-color: #4285f4; }
        .provider-ollama { border-color: #00a67e; }
        .metrics { font-size: 12px; margin-top: 10px; }
        .consensus-bar {
            height: 20px;
            background: linear-gradient(to right, red, yellow, green);
            position: relative;
        }
        .consensus-marker {
            position: absolute;
            width: 2px;
            height: 100%;
            background: black;
        }
    </style>
</head>
<body>
    <h1>🔬 Comparative LLM Testing Dashboard</h1>
    
    <div id="providers">
        <!-- Provider cards dynamiques -->
    </div>
    
    <div id="current-test">
        <h2>Current Test</h2>
        <div id="test-query"></div>
        <div id="test-responses"></div>
    </div>
    
    <div id="consensus">
        <h2>Consensus Analysis</h2>
        <div class="consensus-bar">
            <div class="consensus-marker" id="consensus-marker"></div>
        </div>
        <span id="consensus-value">0%</span>
    </div>
    
    <script>
        async function updateDashboard() {
            const response = await fetch('/api/test-status');
            const data = await response.json();
            
            // Update provider cards
            const providersDiv = document.getElementById('providers');
            providersDiv.innerHTML = '';
            
            for (const [provider, stats] of Object.entries(data.providers)) {
                const card = document.createElement('div');
                card.className = `provider-card provider-${provider.split('_')[0]}`;
                card.innerHTML = `
                    <h3>${provider}</h3>
                    <div class="metrics">
                        <div>✅ Success: ${stats.success_rate}%</div>
                        <div>⏱️ Avg: ${stats.avg_duration}ms</div>
                        <div>🎯 Score: ${stats.avg_score}</div>
                    </div>
                `;
                providersDiv.appendChild(card);
            }
            
            // Update consensus
            document.getElementById('consensus-value').innerText = 
                `${(data.consensus_score * 100).toFixed(1)}%`;
            document.getElementById('consensus-marker').style.left = 
                `${data.consensus_score * 100}%`;
        }
        
        // Update every 2 seconds
        setInterval(updateDashboard, 2000);
        updateDashboard();
    </script>
</body>
</html>
```

---

## 🎯 AVANTAGES DU SYSTÈME HYBRIDE

### 1. **Flexibilité Maximale**
- ✅ Choix entre cloud (Gemini) et local (Ollama)
- ✅ Possibilité de mixer les providers
- ✅ Tests comparatifs objectifs

### 2. **Confidentialité Adaptable**
- ✅ Données sensibles → Ollama local uniquement
- ✅ Requêtes générales → Gemini pour performance
- ✅ Validation croisée cloud/local

### 3. **Résilience**
- ✅ Fallback automatique si un provider échoue
- ✅ Pas de dépendance unique
- ✅ Continuité de service garantie

### 4. **Optimisation Coûts**
- ✅ Ollama gratuit pour usage illimité
- ✅ Gemini seulement quand nécessaire
- ✅ Réduction des coûts API

### 5. **Validation Renforcée**
- ✅ Cross-validation entre architectures différentes
- ✅ Détection d'hallucinations améliorée
- ✅ Consensus plus robuste

---

## 📈 MÉTRIQUES DE COMPARAISON

```yaml
comparison_metrics:
  performance:
    - response_time_ms
    - tokens_per_second
    - memory_usage_mb
    
  quality:
    - factual_accuracy
    - hallucination_rate
    - consistency_score
    
  cost:
    - cost_per_query
    - total_monthly_cost
    
  reliability:
    - uptime_percentage
    - error_rate
    - timeout_rate
```

---

*Extension hybride Gemini/Ollama pour système multiagent - Septembre 2025*