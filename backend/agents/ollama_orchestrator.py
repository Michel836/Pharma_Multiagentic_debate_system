"""
Orchestrateur simplifié pour Ollama uniquement
Mode 100% local sans connexion externe
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import ollama
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class OllamaOnlyOrchestrator:
    """Orchestrateur multiagent utilisant uniquement Ollama en local"""
    
    def __init__(self, config_path: str = "./config/ollama_config.yaml"):
        """Initialise l'orchestrateur avec la configuration Ollama"""
        self.config = self._load_config(config_path)
        self.client = ollama.AsyncClient(host=self.config['ollama']['host'])
        self.agents = {}
        self.debate_history = []
        self.initialized = False
        
    def _load_config(self, config_path: str) -> Dict:
        """Charge la configuration depuis le fichier YAML"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                # Configuration par défaut si le fichier n'existe pas
                return {
                    'ollama': {
                        'host': 'http://localhost:11434',
                        'default_model': 'llama3.2',
                        'agents': {
                            'expert_1': {'model': 'llama3.2', 'temperature': 0.3},
                            'expert_2': {'model': 'llama3.2', 'temperature': 0.5},
                            'expert_3': {'model': 'llama3.2', 'temperature': 0.4},
                            'judge': {'model': 'llama3.2', 'temperature': 0.1}
                        }
                    },
                    'debate': {
                        'max_rounds': 5,
                        'consensus_threshold': 0.7
                    }
                }
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {e}")
            raise
    
    async def initialize(self):
        """Initialise les agents Ollama"""
        try:
            logger.info("🚀 Initialisation de l'orchestrateur Ollama...")
            
            # Vérifier la connexion à Ollama
            await self._check_ollama_connection()
            
            # Initialiser les agents
            for agent_name, agent_config in self.config['ollama']['agents'].items():
                self.agents[agent_name] = {
                    'name': agent_name,
                    'model': agent_config.get('model', self.config['ollama']['default_model']),
                    'temperature': agent_config.get('temperature', 0.7),
                    'role': agent_config.get('role', agent_name),
                    'system_prompt': agent_config.get('system_prompt', f"Tu es {agent_name}")
                }
                logger.info(f"✅ Agent {agent_name} initialisé avec le modèle {self.agents[agent_name]['model']}")
            
            self.initialized = True
            logger.info("✅ Orchestrateur Ollama initialisé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    async def _check_ollama_connection(self):
        """Vérifie la connexion au serveur Ollama"""
        try:
            # Tester la connexion en listant les modèles
            models = await self.client.list()
            available_models = [m['name'] for m in models['models']]
            
            logger.info(f"📋 Modèles Ollama disponibles: {available_models}")
            
            # Vérifier que le modèle par défaut est disponible
            default_model = self.config['ollama']['default_model']
            if not any(default_model in model for model in available_models):
                logger.warning(f"⚠️ Le modèle {default_model} n'est pas installé")
                logger.info(f"💡 Installation du modèle {default_model}...")
                await self.client.pull(default_model)
                logger.info(f"✅ Modèle {default_model} installé")
                
        except Exception as e:
            logger.error(f"❌ Impossible de se connecter à Ollama: {e}")
            logger.error("💡 Assurez-vous qu'Ollama est démarré: 'ollama serve'")
            raise
    
    async def query_agent(self, agent_name: str, prompt: str, context: Dict = None) -> Dict:
        """Interroge un agent spécifique"""
        if not self.initialized:
            await self.initialize()
        
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Agent {agent_name} non trouvé")
        
        try:
            # Construire le prompt complet avec le contexte
            full_prompt = f"{agent['system_prompt']}\n\n"
            
            if context and 'history' in context:
                full_prompt += "Historique du débat:\n"
                for msg in context['history'][-5:]:  # Derniers 5 messages
                    full_prompt += f"- {msg['agent']}: {msg['content'][:200]}...\n"
                full_prompt += "\n"
            
            full_prompt += f"Question: {prompt}\n"
            full_prompt += "Réponds de manière concise et argumentée."
            
            # Appeler Ollama
            response = await self.client.chat(
                model=agent['model'],
                messages=[
                    {'role': 'system', 'content': agent['system_prompt']},
                    {'role': 'user', 'content': full_prompt}
                ],
                options={
                    'temperature': agent['temperature'],
                    'num_predict': 500  # Limiter la longueur des réponses
                }
            )
            
            return {
                'agent': agent_name,
                'role': agent['role'],
                'content': response['message']['content'],
                'model': agent['model'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'interrogation de {agent_name}: {e}")
            return {
                'agent': agent_name,
                'role': agent['role'],
                'content': f"Erreur: {str(e)}",
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    async def conduct_debate_round(self, query: str, round_number: int = 1) -> Dict:
        """Conduit un tour de débat entre tous les agents"""
        logger.info(f"🎯 Tour {round_number}: {query[:100]}...")
        
        round_results = {
            'round': round_number,
            'query': query,
            'responses': [],
            'consensus': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Phase 1: Collecte des opinions des experts
        expert_responses = []
        for agent_name in ['expert_1', 'expert_2', 'expert_3']:
            if agent_name in self.agents:
                response = await self.query_agent(
                    agent_name, 
                    query,
                    {'history': self.debate_history}
                )
                expert_responses.append(response)
                round_results['responses'].append(response)
                
                # Ajouter à l'historique
                self.debate_history.append(response)
                
                # Petit délai pour ne pas surcharger Ollama
                await asyncio.sleep(0.5)
        
        # Phase 2: Synthèse par le juge
        if 'judge' in self.agents:
            judge_prompt = f"""
            Analyse les réponses des experts suivantes sur: {query}
            
            {self._format_expert_responses(expert_responses)}
            
            Fournis:
            1. Une synthèse des points d'accord
            2. Les points de désaccord
            3. Ta recommandation finale
            4. Un score de consensus de 0 à 1
            """
            
            judge_response = await self.query_agent(
                'judge',
                judge_prompt,
                {'history': self.debate_history}
            )
            
            round_results['responses'].append(judge_response)
            round_results['consensus'] = self._calculate_consensus(expert_responses)
            self.debate_history.append(judge_response)
        
        return round_results
    
    def _format_expert_responses(self, responses: List[Dict]) -> str:
        """Formate les réponses des experts pour le juge"""
        formatted = ""
        for resp in responses:
            formatted += f"\n{resp['role']} ({resp['agent']}):\n{resp['content']}\n"
            formatted += "-" * 50
        return formatted
    
    def _calculate_consensus(self, responses: List[Dict]) -> float:
        """Calcule un score de consensus simple basé sur la similarité des réponses"""
        # Implémentation simple: pourcentage de mots communs
        if len(responses) < 2:
            return 1.0
        
        # Extraire les mots clés de chaque réponse
        word_sets = []
        for resp in responses:
            if 'content' in resp and not resp.get('error'):
                words = set(resp['content'].lower().split())
                word_sets.append(words)
        
        if len(word_sets) < 2:
            return 0.5
        
        # Calculer l'intersection
        common_words = word_sets[0]
        for word_set in word_sets[1:]:
            common_words = common_words.intersection(word_set)
        
        # Score basé sur le ratio de mots communs
        total_words = sum(len(ws) for ws in word_sets)
        if total_words == 0:
            return 0.5
        
        consensus_score = len(common_words) * len(word_sets) / total_words
        return min(1.0, consensus_score * 2)  # Normaliser entre 0 et 1
    
    async def run_full_debate(self, query: str, max_rounds: int = None) -> Dict:
        """Exécute un débat complet avec plusieurs tours"""
        if not self.initialized:
            await self.initialize()
        
        max_rounds = max_rounds or self.config['debate']['max_rounds']
        consensus_threshold = self.config['debate']['consensus_threshold']
        
        debate_results = {
            'query': query,
            'rounds': [],
            'final_consensus': 0,
            'conclusion': None,
            'start_time': datetime.now().isoformat()
        }
        
        # Réinitialiser l'historique pour un nouveau débat
        self.debate_history = []
        
        for round_num in range(1, max_rounds + 1):
            # Conduire un tour
            round_result = await self.conduct_debate_round(query, round_num)
            debate_results['rounds'].append(round_result)
            
            # Vérifier le consensus
            if round_result['consensus'] and round_result['consensus'] >= consensus_threshold:
                logger.info(f"✅ Consensus atteint au tour {round_num}: {round_result['consensus']:.2f}")
                debate_results['final_consensus'] = round_result['consensus']
                break
            
            # Préparer la question pour le tour suivant si nécessaire
            if round_num < max_rounds:
                query = f"Compte tenu des discussions précédentes, approfondissons: {query}"
        
        # Conclusion finale
        debate_results['end_time'] = datetime.now().isoformat()
        debate_results['total_rounds'] = len(debate_results['rounds'])
        debate_results['conclusion'] = self._generate_conclusion(debate_results)
        
        return debate_results
    
    def _generate_conclusion(self, debate_results: Dict) -> str:
        """Génère une conclusion du débat"""
        if not debate_results['rounds']:
            return "Aucun débat n'a eu lieu."
        
        last_round = debate_results['rounds'][-1]
        consensus = last_round.get('consensus', 0)
        
        if consensus >= 0.8:
            status = "Fort consensus atteint"
        elif consensus >= 0.6:
            status = "Consensus partiel"
        else:
            status = "Pas de consensus clair"
        
        conclusion = f"""
        Statut: {status} (Score: {consensus:.2f})
        Nombre de tours: {debate_results['total_rounds']}
        
        Synthèse finale:
        """
        
        # Ajouter la dernière réponse du juge s'il existe
        judge_responses = [r for r in last_round['responses'] if r.get('role') == 'Juge arbitre']
        if judge_responses:
            conclusion += judge_responses[-1]['content'][:500]
        
        return conclusion
    
    async def get_status(self) -> Dict:
        """Retourne le statut de l'orchestrateur"""
        status = {
            'initialized': self.initialized,
            'ollama_host': self.config['ollama']['host'],
            'agents_count': len(self.agents),
            'agents': list(self.agents.keys()),
            'default_model': self.config['ollama']['default_model'],
            'debate_history_length': len(self.debate_history)
        }
        
        # Vérifier la connexion Ollama
        try:
            models = await self.client.list()
            status['ollama_connected'] = True
            status['available_models'] = [m['name'] for m in models['models']]
        except:
            status['ollama_connected'] = False
            status['available_models'] = []
        
        return status


# Fonction utilitaire pour tester rapidement
async def test_ollama_orchestrator():
    """Fonction de test rapide"""
    orchestrator = OllamaOnlyOrchestrator()
    await orchestrator.initialize()
    
    # Test simple
    query = "Quelle est la meilleure approche pour valider un nouveau médicament?"
    result = await orchestrator.run_full_debate(query, max_rounds=2)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    # Test direct
    asyncio.run(test_ollama_orchestrator())