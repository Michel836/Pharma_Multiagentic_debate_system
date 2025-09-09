# 🎭 ARCHITECTURE FINALE : SYSTÈME DE DÉBAT IA VISIBLE AVEC VALIDATION HUMAINE

*Architecture complète intégrant tous les éléments : Débat visible, Vote, Validation humaine, Pipeline 4 étapes*

---

## 🎯 VISION PRODUIT

Un système où **l'utilisateur voit les IAs débattre en temps réel**, peut intervenir aux points critiques, et valide les décisions importantes. Conçu pour éliminer les hallucinations dans un contexte pharmaceutique R&D où **chaque décision compte**.

---

## 🏗️ ARCHITECTURE GLOBALE COMPLÈTE

```
┌─────────────────────────────────────────────────────────────────┐
│                   INTERFACE REACT - DÉBAT VISIBLE               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Chat Debate  │  │ Voting Panel │  │ Human Valid. │         │
│  │   (Live)     │  │  (Scores)    │  │ (Checkpoints)│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────┬───────────────────────────────────────────────┘
                  │ WebSocket
         ┌────────▼────────┐
         │  ORCHESTRATEUR  │ ◄── Gestion débat + rounds
         │   avec JUGE IA  │     Validation humaine
         └────────┬────────┘     Scoring & votes
                  │
    ┌─────────────┴─────────────────────────┐
    │                                       │
┌───▼────┐  ┌────▼────┐  ┌────▼────┐  ┌───▼────┐
│Expert 1│  │Expert 2 │  │Expert 3 │  │  JUGE  │
│ Gemini │  │ Ollama  │  │ Ollama  │  │Arbitre │
│  0.3   │  │ Llama   │  │ Mistral │  │ Final  │
└───┬────┘  └────┬────┘  └────┬────┘  └───┬────┘
    └────────────┴────────────┴────────────┘
                        │
         ┌──────────────▼──────────────┐
         │      TRIPLE RAG SYSTEM      │
         ├──────────────────────────────┤
         │Enterprise│Personal│Contacts │ ◄── Sources
         │  (KB)   │(Context)│(Emails) │     enrichies
         └──────────────┬──────────────┘
                        │
    ┌───────────────────▼───────────────────┐
    │         PIPELINE 4 ÉTAPES             │
    ├────────────────────────────────────────┤
    │ 1.Extract → 2.Validate → 3.Synth → 4.Share │
    └────────────────────────────────────────┘
```

---

## 💬 SYSTÈME DE DÉBAT VISIBLE

### 1. STRUCTURE DU DÉBAT

```python
# debate_manager.py
from typing import Dict, List, Optional
from enum import Enum
import asyncio
import uuid
from datetime import datetime

class DebateRole(Enum):
    EXPERT = "expert"
    JUDGE = "judge"
    HUMAN = "human"

class DebatePhase(Enum):
    INITIALIZATION = "initialization"
    OPENING_STATEMENTS = "opening_statements"
    ARGUMENTATION = "argumentation"
    VOTING = "voting"
    HUMAN_VALIDATION = "human_validation"
    SYNTHESIS = "synthesis"
    FINAL_VALIDATION = "final_validation"

class DebateMessage:
    """Message dans le débat visible"""
    def __init__(self, 
                 agent_id: str,
                 role: DebateRole,
                 content: str,
                 metadata: Dict = None):
        self.id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        self.agent_id = agent_id
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.votes_received = []
        self.confidence_score = 0.0
        
class VisibleDebateManager:
    """Gestionnaire du débat visible entre agents"""
    
    def __init__(self, max_rounds: int = 5):
        self.debate_id = str(uuid.uuid4())
        self.participants = {}
        self.messages = []
        self.current_round = 0
        self.max_rounds = max_rounds
        self.current_phase = DebatePhase.INITIALIZATION
        self.human_validations = []
        self.final_consensus = None
        self.websocket_clients = []
        
    async def initialize_debate(self, 
                               query: str,
                               experts: List[Dict],
                               judge: Dict) -> str:
        """Initialise un nouveau débat"""
        
        # Enregistrer les participants
        for expert in experts:
            self.participants[expert['id']] = {
                'role': DebateRole.EXPERT,
                'provider': expert['provider'],
                'model': expert['model'],
                'temperature': expert.get('temperature', 0.7),
                'score': 0,
                'messages_count': 0
            }
        
        self.participants[judge['id']] = {
            'role': DebateRole.JUDGE,
            'provider': judge['provider'],
            'model': judge['model'],
            'score': 0
        }
        
        # Message d'ouverture
        opening_msg = DebateMessage(
            agent_id="system",
            role=DebateRole.JUDGE,
            content=f"🎭 Début du débat sur : {query}",
            metadata={'query': query, 'phase': 'opening'}
        )
        
        await self.broadcast_message(opening_msg)
        
        self.current_phase = DebatePhase.OPENING_STATEMENTS
        
        return self.debate_id
    
    async def conduct_round(self, topic: str, context: Dict) -> Dict:
        """Conduit un tour de débat"""
        
        self.current_round += 1
        
        # Vérifier limite de tours
        if self.current_round > self.max_rounds:
            return await self.force_conclusion("Max rounds reached")
        
        round_messages = []
        
        # Phase 1: Déclarations d'ouverture
        if self.current_phase == DebatePhase.OPENING_STATEMENTS:
            for participant_id, participant in self.participants.items():
                if participant['role'] == DebateRole.EXPERT:
                    response = await self.get_expert_statement(
                        participant_id, topic, context
                    )
                    round_messages.append(response)
            
            self.current_phase = DebatePhase.ARGUMENTATION
        
        # Phase 2: Argumentation
        elif self.current_phase == DebatePhase.ARGUMENTATION:
            # Les experts répondent aux arguments précédents
            previous_arguments = self.get_previous_arguments()
            
            for participant_id, participant in self.participants.items():
                if participant['role'] == DebateRole.EXPERT:
                    response = await self.get_expert_argument(
                        participant_id, 
                        topic, 
                        previous_arguments,
                        context
                    )
                    round_messages.append(response)
            
            # Vérifier si on passe au vote
            if self.should_proceed_to_voting():
                self.current_phase = DebatePhase.VOTING
        
        # Phase 3: Vote
        elif self.current_phase == DebatePhase.VOTING:
            voting_results = await self.conduct_voting()
            
            # Checkpoint validation humaine
            self.current_phase = DebatePhase.HUMAN_VALIDATION
            return {
                'phase': 'voting_complete',
                'results': voting_results,
                'requires_human_validation': True
            }
        
        return {
            'round': self.current_round,
            'phase': self.current_phase.value,
            'messages': round_messages
        }
    
    async def get_expert_statement(self, 
                                  expert_id: str,
                                  topic: str,
                                  context: Dict) -> DebateMessage:
        """Obtient la déclaration d'un expert"""
        
        expert = self.participants[expert_id]
        
        # Appel au LLM approprié
        prompt = f"""As an expert in pharmaceutical R&D, provide your initial position on:
        {topic}
        
        Context: {context.get('rag_results', 'No additional context')}
        
        Be concise, factual, and highlight key points."""
        
        # Simuler appel LLM (remplacer par vraie implémentation)
        response = await self.call_llm(expert, prompt)
        
        # Créer message de débat
        message = DebateMessage(
            agent_id=expert_id,
            role=DebateRole.EXPERT,
            content=response,
            metadata={
                'round': self.current_round,
                'phase': self.current_phase.value,
                'model': expert['model']
            }
        )
        
        # Broadcaster aux clients
        await self.broadcast_message(message)
        
        self.messages.append(message)
        expert['messages_count'] += 1
        
        return message
    
    async def conduct_voting(self) -> Dict:
        """Système de vote entre agents"""
        
        voting_results = {}
        
        # Chaque expert vote pour les messages des autres
        for voter_id, voter in self.participants.items():
            if voter['role'] == DebateRole.EXPERT:
                votes = await self.get_expert_votes(voter_id)
                voting_results[voter_id] = votes
        
        # Le juge fait une synthèse
        judge_id = self.get_judge_id()
        judge_summary = await self.get_judge_decision(voting_results)
        
        # Calculer les scores
        final_scores = self.calculate_voting_scores(voting_results)
        
        # Message de résultat du vote
        vote_message = DebateMessage(
            agent_id=judge_id,
            role=DebateRole.JUDGE,
            content=f"📊 Résultats du vote : {judge_summary}",
            metadata={
                'voting_results': voting_results,
                'final_scores': final_scores
            }
        )
        
        await self.broadcast_message(vote_message)
        
        return {
            'votes': voting_results,
            'scores': final_scores,
            'judge_summary': judge_summary
        }
    
    async def broadcast_message(self, message: DebateMessage):
        """Envoie le message à tous les clients WebSocket"""
        
        formatted_msg = {
            'id': message.id,
            'timestamp': message.timestamp.isoformat(),
            'agent_id': message.agent_id,
            'role': message.role.value,
            'content': message.content,
            'metadata': message.metadata
        }
        
        # Envoyer à tous les clients connectés
        for client in self.websocket_clients:
            await client.send_json(formatted_msg)
    
    def should_proceed_to_voting(self) -> bool:
        """Détermine si on doit passer au vote"""
        
        # Critères pour passer au vote
        if self.current_round >= 3:
            return True
        
        # Si consensus détecté
        if self.detect_consensus() > 0.8:
            return True
        
        # Si divergence excessive
        if self.detect_divergence() > 0.9:
            return True
        
        return False
    
    def detect_consensus(self) -> float:
        """Détecte le niveau de consensus entre experts"""
        
        if len(self.messages) < 2:
            return 0.0
        
        # Analyse simplifiée des derniers messages
        recent_messages = self.messages[-3:]
        
        # Calcul de similarité (à améliorer avec NLP)
        keywords_sets = []
        for msg in recent_messages:
            if msg.role == DebateRole.EXPERT:
                words = set(msg.content.lower().split())
                keywords = {w for w in words if len(w) > 4}
                keywords_sets.append(keywords)
        
        if not keywords_sets:
            return 0.0
        
        # Intersection des mots-clés
        common = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            common = common.intersection(kw_set)
        
        avg_keywords = sum(len(kw) for kw in keywords_sets) / len(keywords_sets)
        consensus = len(common) / max(avg_keywords, 1)
        
        return min(consensus, 1.0)
```

### 2. VALIDATION HUMAINE OBLIGATOIRE

```python
# human_validation.py
from enum import Enum
from typing import Dict, List, Optional
import asyncio

class ValidationDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CLARIFICATION = "clarification"
    REQUEST_MORE_DEBATE = "more_debate"
    OVERRIDE_WITH_CUSTOM = "override"

class HumanValidationCheckpoint:
    """Point de validation humaine dans le workflow"""
    
    def __init__(self, checkpoint_type: str, mandatory: bool = True):
        self.checkpoint_type = checkpoint_type
        self.mandatory = mandatory
        self.validation_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.validated_at = None
        self.decision = None
        self.validator_notes = ""
        self.validation_score = 0
        
class HumanValidationManager:
    """Gestionnaire des validations humaines obligatoires"""
    
    def __init__(self):
        self.pending_validations = {}
        self.validation_history = []
        self.validation_metrics = {
            'total_validations': 0,
            'approvals': 0,
            'rejections': 0,
            'average_time': 0
        }
        
    async def request_validation(self,
                                debate_state: Dict,
                                checkpoint_type: str,
                                context: Dict) -> ValidationDecision:
        """Demande une validation humaine"""
        
        checkpoint = HumanValidationCheckpoint(
            checkpoint_type=checkpoint_type,
            mandatory=True
        )
        
        # Préparer les données pour l'interface
        validation_request = {
            'id': checkpoint.validation_id,
            'type': checkpoint_type,
            'timestamp': checkpoint.created_at.isoformat(),
            'debate_summary': self.summarize_debate(debate_state),
            'voting_results': debate_state.get('voting_results'),
            'ai_recommendation': self.get_ai_recommendation(debate_state),
            'risk_assessment': self.assess_risks(debate_state, context),
            'requires_immediate_attention': self.is_critical(checkpoint_type)
        }
        
        # Envoyer à l'interface React
        await self.send_to_ui(validation_request)
        
        # Attendre la décision humaine (avec timeout)
        try:
            decision = await asyncio.wait_for(
                self.wait_for_human_decision(checkpoint.validation_id),
                timeout=300  # 5 minutes timeout
            )
        except asyncio.TimeoutError:
            # Timeout - action par défaut sécurisée
            decision = ValidationDecision.REQUEST_MORE_DEBATE
            checkpoint.validator_notes = "Timeout - defaulted to request more debate"
        
        # Enregistrer la validation
        checkpoint.validated_at = datetime.utcnow()
        checkpoint.decision = decision
        self.validation_history.append(checkpoint)
        
        # Métriques
        self.update_metrics(checkpoint)
        
        return decision
    
    def summarize_debate(self, debate_state: Dict) -> Dict:
        """Résume le débat pour la validation humaine"""
        
        return {
            'round': debate_state.get('current_round'),
            'participants': len(debate_state.get('participants', [])),
            'consensus_level': debate_state.get('consensus_score', 0),
            'key_points': self.extract_key_points(debate_state),
            'disagreements': self.extract_disagreements(debate_state),
            'confidence_scores': debate_state.get('confidence_scores', {})
        }
    
    def assess_risks(self, debate_state: Dict, context: Dict) -> Dict:
        """Évalue les risques pour la décision"""
        
        risk_score = 0
        risk_factors = []
        
        # Consensus faible
        if debate_state.get('consensus_score', 0) < 0.5:
            risk_score += 0.3
            risk_factors.append("Low consensus among experts")
        
        # Hallucination détectée
        if debate_state.get('hallucination_detected', False):
            risk_score += 0.5
            risk_factors.append("Potential hallucination detected")
        
        # Contexte critique
        if context.get('compliance_level') == 'GxP':
            risk_score += 0.2
            risk_factors.append("GxP compliance context")
        
        # Données sensibles
        if context.get('contains_pii', False):
            risk_score += 0.2
            risk_factors.append("Contains sensitive data")
        
        return {
            'risk_score': min(risk_score, 1.0),
            'risk_level': self.get_risk_level(risk_score),
            'risk_factors': risk_factors,
            'mitigation_suggestions': self.suggest_mitigations(risk_factors)
        }
    
    def get_risk_level(self, score: float) -> str:
        """Détermine le niveau de risque"""
        if score < 0.3:
            return "LOW"
        elif score < 0.6:
            return "MEDIUM"
        elif score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    async def wait_for_human_decision(self, validation_id: str) -> ValidationDecision:
        """Attend la décision humaine via l'interface"""
        
        # Créer un future pour attendre la décision
        future = asyncio.Future()
        self.pending_validations[validation_id] = future
        
        # Attendre que l'humain prenne une décision
        decision = await future
        
        # Nettoyer
        del self.pending_validations[validation_id]
        
        return decision
    
    async def receive_human_decision(self,
                                    validation_id: str,
                                    decision: str,
                                    notes: str = "",
                                    score: int = 0):
        """Reçoit la décision humaine depuis l'UI"""
        
        if validation_id in self.pending_validations:
            future = self.pending_validations[validation_id]
            
            # Convertir en enum
            decision_enum = ValidationDecision[decision.upper()]
            
            # Résoudre le future
            future.set_result(decision_enum)
            
            # Log la décision
            await self.log_human_decision(validation_id, decision_enum, notes, score)
```

### 3. SYSTÈME DE VOTE ET SCORING

```python
# voting_system.py
from typing import Dict, List, Tuple
import numpy as np

class VotingSystem:
    """Système de vote entre agents avec scoring transparent"""
    
    def __init__(self):
        self.voting_history = []
        self.agent_performance = {}  # Track historique de performance
        
    async def conduct_vote(self, 
                          messages: List[DebateMessage],
                          voters: List[str]) -> Dict:
        """Organise un vote entre agents"""
        
        voting_matrix = {}
        
        for voter_id in voters:
            voter_scores = await self.get_voter_scores(voter_id, messages)
            voting_matrix[voter_id] = voter_scores
        
        # Calculer les scores finaux
        final_scores = self.calculate_weighted_scores(voting_matrix)
        
        # Déterminer le gagnant
        winner = self.determine_winner(final_scores)
        
        # Enregistrer le vote
        vote_record = {
            'timestamp': datetime.utcnow(),
            'voting_matrix': voting_matrix,
            'final_scores': final_scores,
            'winner': winner,
            'consensus_level': self.calculate_consensus(voting_matrix)
        }
        
        self.voting_history.append(vote_record)
        
        return vote_record
    
    async def get_voter_scores(self, 
                              voter_id: str,
                              messages: List[DebateMessage]) -> Dict:
        """Un agent vote sur les messages des autres"""
        
        scores = {}
        
        for message in messages:
            # Ne pas voter pour soi-même
            if message.agent_id == voter_id:
                continue
            
            # Critères de scoring
            score = await self.evaluate_message(message, voter_id)
            scores[message.id] = {
                'message_id': message.id,
                'agent_id': message.agent_id,
                'score': score,
                'criteria': self.get_scoring_criteria(message, score)
            }
        
        return scores
    
    async def evaluate_message(self, 
                              message: DebateMessage,
                              evaluator_id: str) -> float:
        """Évalue un message selon plusieurs critères"""
        
        criteria_scores = {
            'factual_accuracy': await self.check_factual_accuracy(message),
            'relevance': await self.check_relevance(message),
            'consistency': await self.check_consistency(message),
            'completeness': await self.check_completeness(message),
            'clarity': await self.check_clarity(message)
        }
        
        # Pondération des critères
        weights = {
            'factual_accuracy': 0.35,  # Plus important en pharma
            'relevance': 0.20,
            'consistency': 0.20,
            'completeness': 0.15,
            'clarity': 0.10
        }
        
        # Score pondéré
        final_score = sum(
            criteria_scores[criterion] * weights[criterion]
            for criterion in criteria_scores
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def calculate_weighted_scores(self, voting_matrix: Dict) -> Dict:
        """Calcule les scores finaux pondérés"""
        
        message_scores = {}
        
        # Agrégation des votes
        for voter_id, votes in voting_matrix.items():
            voter_weight = self.get_voter_weight(voter_id)
            
            for message_id, vote_data in votes.items():
                if message_id not in message_scores:
                    message_scores[message_id] = {
                        'total_score': 0,
                        'vote_count': 0,
                        'voters': []
                    }
                
                message_scores[message_id]['total_score'] += vote_data['score'] * voter_weight
                message_scores[message_id]['vote_count'] += 1
                message_scores[message_id]['voters'].append(voter_id)
        
        # Normalisation
        for message_id in message_scores:
            if message_scores[message_id]['vote_count'] > 0:
                message_scores[message_id]['average_score'] = (
                    message_scores[message_id]['total_score'] / 
                    message_scores[message_id]['vote_count']
                )
            else:
                message_scores[message_id]['average_score'] = 0
        
        return message_scores
    
    def get_voter_weight(self, voter_id: str) -> float:
        """Détermine le poids du vote d'un agent selon ses performances"""
        
        if voter_id not in self.agent_performance:
            return 1.0  # Poids par défaut
        
        perf = self.agent_performance[voter_id]
        
        # Facteurs de pondération
        accuracy_weight = perf.get('historical_accuracy', 0.5)
        consistency_weight = perf.get('consistency_score', 0.5)
        
        # Poids final entre 0.5 et 1.5
        weight = 0.5 + (accuracy_weight + consistency_weight) / 2
        
        return weight
    
    def calculate_consensus(self, voting_matrix: Dict) -> float:
        """Calcule le niveau de consensus entre votants"""
        
        if not voting_matrix or len(voting_matrix) < 2:
            return 0.0
        
        # Extraire tous les scores par message
        message_votes = {}
        
        for voter_id, votes in voting_matrix.items():
            for message_id, vote_data in votes.items():
                if message_id not in message_votes:
                    message_votes[message_id] = []
                message_votes[message_id].append(vote_data['score'])
        
        # Calculer la variance pour chaque message
        variances = []
        for message_id, scores in message_votes.items():
            if len(scores) > 1:
                variance = np.var(scores)
                variances.append(variance)
        
        if not variances:
            return 0.0
        
        # Consensus inversement proportionnel à la variance moyenne
        avg_variance = np.mean(variances)
        consensus = 1.0 - min(avg_variance * 2, 1.0)  # Normaliser
        
        return consensus
```

### 4. COMPTEUR DE TOURS AVEC INTERRUPTION

```python
# round_counter.py
from typing import Optional, Callable

class RoundCounter:
    """Compteur de tours avec interruption automatique"""
    
    def __init__(self, 
                 max_rounds: int = 5,
                 user_threshold: Optional[int] = None):
        self.current_round = 0
        self.max_rounds = max_rounds
        self.user_threshold = user_threshold or max_rounds
        self.round_history = []
        self.interruption_triggered = False
        self.interruption_reason = None
        
    def increment(self) -> Tuple[int, bool]:
        """Incrémente le compteur et vérifie les conditions d'arrêt"""
        
        self.current_round += 1
        
        # Enregistrer dans l'historique
        self.round_history.append({
            'round': self.current_round,
            'timestamp': datetime.utcnow(),
            'messages_count': 0,
            'consensus_level': 0
        })
        
        # Vérifier les conditions d'interruption
        should_interrupt = self.check_interruption_conditions()
        
        return self.current_round, should_interrupt
    
    def check_interruption_conditions(self) -> bool:
        """Vérifie si on doit interrompre le débat"""
        
        # Seuil utilisateur atteint
        if self.current_round >= self.user_threshold:
            self.interruption_triggered = True
            self.interruption_reason = f"User threshold reached ({self.user_threshold} rounds)"
            return True
        
        # Maximum absolu atteint
        if self.current_round >= self.max_rounds:
            self.interruption_triggered = True
            self.interruption_reason = f"Maximum rounds reached ({self.max_rounds})"
            return True
        
        # Détection de pattern de répétition
        if self.detect_repetition_pattern():
            self.interruption_triggered = True
            self.interruption_reason = "Repetition pattern detected"
            return True
        
        # Consensus parfait atteint
        if self.check_perfect_consensus():
            self.interruption_triggered = True
            self.interruption_reason = "Perfect consensus achieved"
            return True
        
        return False
    
    def detect_repetition_pattern(self) -> bool:
        """Détecte si les agents tournent en rond"""
        
        if len(self.round_history) < 3:
            return False
        
        # Comparer les 3 derniers rounds
        recent_rounds = self.round_history[-3:]
        
        # Si le consensus n'évolue pas
        consensus_values = [r.get('consensus_level', 0) for r in recent_rounds]
        if len(set(consensus_values)) == 1:  # Toutes valeurs identiques
            return True
        
        return False
    
    def check_perfect_consensus(self) -> bool:
        """Vérifie si un consensus parfait est atteint"""
        
        if not self.round_history:
            return False
        
        last_round = self.round_history[-1]
        return last_round.get('consensus_level', 0) > 0.95
    
    def get_status(self) -> Dict:
        """Retourne le statut actuel du compteur"""
        
        return {
            'current_round': self.current_round,
            'max_rounds': self.max_rounds,
            'user_threshold': self.user_threshold,
            'rounds_remaining': self.user_threshold - self.current_round,
            'interruption_triggered': self.interruption_triggered,
            'interruption_reason': self.interruption_reason,
            'efficiency_score': self.calculate_efficiency()
        }
    
    def calculate_efficiency(self) -> float:
        """Calcule l'efficacité du débat"""
        
        if not self.round_history:
            return 0.0
        
        # Facteurs d'efficacité
        rounds_used = self.current_round
        max_expected = self.user_threshold
        
        # Plus c'est rapide, plus c'est efficace
        efficiency = 1.0 - (rounds_used / max_expected)
        
        # Bonus si consensus atteint rapidement
        if self.interruption_reason == "Perfect consensus achieved":
            efficiency += 0.2
        
        return min(max(efficiency, 0.0), 1.0)
```

### 5. PIPELINE 4 ÉTAPES VISIBLE

```python
# pipeline_processor.py
from enum import Enum

class PipelineStage(Enum):
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    SYNTHESIS = "synthesis"
    SHARING = "sharing"

class VisiblePipeline:
    """Pipeline de traitement visible en 4 étapes"""
    
    def __init__(self):
        self.current_stage = None
        self.stage_results = {}
        self.pipeline_metadata = {}
        self.observers = []  # WebSocket clients
        
    async def process(self, 
                     input_data: Dict,
                     context: Dict) -> Dict:
        """Exécute le pipeline complet avec visibilité"""
        
        pipeline_id = str(uuid.uuid4())
        
        # Étape 1: Extraction
        await self.notify_stage_start(PipelineStage.EXTRACTION)
        extraction_results = await self.extract_stage(input_data, context)
        self.stage_results['extraction'] = extraction_results
        await self.notify_stage_complete(PipelineStage.EXTRACTION, extraction_results)
        
        # Étape 2: Validation
        await self.notify_stage_start(PipelineStage.VALIDATION)
        validation_results = await self.validate_stage(extraction_results)
        self.stage_results['validation'] = validation_results
        await self.notify_stage_complete(PipelineStage.VALIDATION, validation_results)
        
        # Checkpoint humain obligatoire ici
        human_decision = await self.request_human_validation(validation_results)
        if human_decision != ValidationDecision.APPROVE:
            return await self.handle_rejection(human_decision)
        
        # Étape 3: Synthèse
        await self.notify_stage_start(PipelineStage.SYNTHESIS)
        synthesis_results = await self.synthesis_stage(
            extraction_results,
            validation_results
        )
        self.stage_results['synthesis'] = synthesis_results
        await self.notify_stage_complete(PipelineStage.SYNTHESIS, synthesis_results)
        
        # Étape 4: Partage
        await self.notify_stage_start(PipelineStage.SHARING)
        sharing_results = await self.sharing_stage(synthesis_results)
        self.stage_results['sharing'] = sharing_results
        await self.notify_stage_complete(PipelineStage.SHARING, sharing_results)
        
        return {
            'pipeline_id': pipeline_id,
            'stages': self.stage_results,
            'final_output': sharing_results['formatted_output'],
            'metadata': self.pipeline_metadata
        }
    
    async def extract_stage(self, input_data: Dict, context: Dict) -> Dict:
        """Étape 1: Extraction des informations depuis les RAGs"""
        
        extraction = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': [],
            'key_information': [],
            'confidence_scores': {}
        }
        
        # Extraction depuis Enterprise RAG
        enterprise_data = await self.extract_from_enterprise_rag(
            input_data['query']
        )
        extraction['sources'].append({
            'type': 'enterprise',
            'count': len(enterprise_data),
            'relevance': self.calculate_relevance(enterprise_data)
        })
        
        # Extraction depuis Personal RAG
        personal_data = await self.extract_from_personal_rag(
            input_data['query'],
            context.get('user_id')
        )
        extraction['sources'].append({
            'type': 'personal',
            'count': len(personal_data),
            'relevance': self.calculate_relevance(personal_data)
        })
        
        # Extraction depuis Contacts/Emails
        contacts_data = await self.extract_from_contacts(
            input_data['query'],
            context.get('user_id')
        )
        extraction['sources'].append({
            'type': 'contacts',
            'count': len(contacts_data),
            'relevance': self.calculate_relevance(contacts_data)
        })
        
        # Consolidation
        extraction['key_information'] = self.consolidate_extractions(
            enterprise_data,
            personal_data,
            contacts_data
        )
        
        return extraction
    
    async def validate_stage(self, extraction_results: Dict) -> Dict:
        """Étape 2: Validation des informations extraites"""
        
        validation = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks_performed': [],
            'issues_found': [],
            'validation_score': 0.0
        }
        
        # Validation factuelle
        fact_check = await self.validate_facts(extraction_results['key_information'])
        validation['checks_performed'].append('fact_checking')
        if fact_check['issues']:
            validation['issues_found'].extend(fact_check['issues'])
        
        # Détection d'hallucinations
        hallucination_check = await self.detect_hallucinations(
            extraction_results['key_information']
        )
        validation['checks_performed'].append('hallucination_detection')
        if hallucination_check['detected']:
            validation['issues_found'].append({
                'type': 'hallucination',
                'severity': 'high',
                'details': hallucination_check['details']
            })
        
        # Validation de cohérence
        consistency_check = await self.validate_consistency(
            extraction_results['key_information']
        )
        validation['checks_performed'].append('consistency_check')
        
        # Score global de validation
        validation['validation_score'] = self.calculate_validation_score(
            fact_check,
            hallucination_check,
            consistency_check
        )
        
        return validation
    
    async def synthesis_stage(self, 
                            extraction_results: Dict,
                            validation_results: Dict) -> Dict:
        """Étape 3: Synthèse des informations validées"""
        
        synthesis = {
            'timestamp': datetime.utcnow().isoformat(),
            'consolidated_information': {},
            'confidence_level': 0.0,
            'synthesis_method': 'consensus_based'
        }
        
        # Filtrer les informations validées
        validated_info = self.filter_validated_information(
            extraction_results['key_information'],
            validation_results
        )
        
        # Construire la synthèse
        synthesis['consolidated_information'] = {
            'main_findings': self.extract_main_findings(validated_info),
            'supporting_evidence': self.gather_evidence(validated_info),
            'recommendations': self.generate_recommendations(validated_info),
            'caveats': self.identify_caveats(validation_results)
        }
        
        # Calculer le niveau de confiance
        synthesis['confidence_level'] = self.calculate_synthesis_confidence(
            validation_results['validation_score'],
            len(validated_info)
        )
        
        return synthesis
    
    async def sharing_stage(self, synthesis_results: Dict) -> Dict:
        """Étape 4: Formatage pour partage"""
        
        sharing = {
            'timestamp': datetime.utcnow().isoformat(),
            'formatted_output': {},
            'export_ready': False
        }
        
        # Formatter selon le template pharmaceutique
        sharing['formatted_output'] = {
            'thematique': self.extract_theme(synthesis_results),
            'sujet': self.extract_subject(synthesis_results),
            'points_clefs': self.extract_key_points(synthesis_results),
            'points_attention': self.extract_attention_points(synthesis_results),
            'tableau_prochaines_etapes': self.generate_next_steps_table(synthesis_results)
        }
        
        # Préparer les exports
        sharing['export_formats'] = {
            'json': json.dumps(sharing['formatted_output'], indent=2),
            'markdown': self.format_as_markdown(sharing['formatted_output']),
            'pdf_ready': self.prepare_pdf_export(sharing['formatted_output'])
        }
        
        sharing['export_ready'] = True
        
        return sharing
    
    async def notify_stage_start(self, stage: PipelineStage):
        """Notifie les observateurs du début d'une étape"""
        
        notification = {
            'event': 'stage_start',
            'stage': stage.value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for observer in self.observers:
            await observer.send_json(notification)
    
    async def notify_stage_complete(self, stage: PipelineStage, results: Dict):
        """Notifie les observateurs de la fin d'une étape"""
        
        notification = {
            'event': 'stage_complete',
            'stage': stage.value,
            'timestamp': datetime.utcnow().isoformat(),
            'summary': self.summarize_stage_results(results)
        }
        
        for observer in self.observers:
            await observer.send_json(notification)
```

---

## 🎨 INTERFACE REACT - DÉBAT VISIBLE

### Component Principal - DebateChat

```jsx
// src/components/DebateChat.jsx
import React, { useState, useEffect, useRef } from 'react';
import { WebSocketService } from '../services/websocket';
import VotingPanel from './VotingPanel';
import HumanValidation from './HumanValidation';
import PipelineViewer from './PipelineViewer';
import './DebateChat.css';

const DebateChat = () => {
  const [messages, setMessages] = useState([]);
  const [debatePhase, setDebatePhase] = useState('initialization');
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(5);
  const [participants, setParticipants] = useState({});
  const [isVoting, setIsVoting] = useState(false);
  const [validationRequired, setValidationRequired] = useState(false);
  const [consensusLevel, setConsensusLevel] = useState(0);
  
  const messagesEndRef = useRef(null);
  const ws = useRef(null);
  
  useEffect(() => {
    // Connexion WebSocket
    ws.current = new WebSocketService('ws://localhost:8000/ws');
    
    ws.current.on('message', (msg) => {
      handleIncomingMessage(msg);
    });
    
    ws.current.on('debate_update', (update) => {
      handleDebateUpdate(update);
    });
    
    return () => ws.current.close();
  }, []);
  
  useEffect(() => {
    // Auto-scroll vers le bas
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleIncomingMessage = (msg) => {
    setMessages(prev => [...prev, {
      id: msg.id,
      timestamp: msg.timestamp,
      agent: msg.agent_id,
      role: msg.role,
      content: msg.content,
      metadata: msg.metadata
    }]);
    
    // Mise à jour du compteur de tours
    if (msg.metadata?.round) {
      setCurrentRound(msg.metadata.round);
    }
  };
  
  const handleDebateUpdate = (update) => {
    if (update.phase) setDebatePhase(update.phase);
    if (update.consensus_level) setConsensusLevel(update.consensus_level);
    if (update.voting_required) setIsVoting(true);
    if (update.validation_required) setValidationRequired(true);
  };
  
  const renderMessage = (msg) => {
    const agentColors = {
      'expert_1': '#4285f4',  // Bleu Gemini
      'expert_2': '#00a67e',  // Vert Ollama
      'expert_3': '#ff6b6b',  // Rouge Mistral
      'judge': '#9b59b6',     // Violet Juge
      'system': '#95a5a6'     // Gris Système
    };
    
    const color = agentColors[msg.agent] || '#333';
    
    return (
      <div key={msg.id} className={`debate-message ${msg.role}`}>
        <div className="message-header">
          <span className="agent-name" style={{ color }}>
            {getAgentDisplayName(msg.agent)}
          </span>
          <span className="timestamp">
            {new Date(msg.timestamp).toLocaleTimeString()}
          </span>
          {msg.metadata?.confidence_score && (
            <span className="confidence">
              Confiance: {(msg.metadata.confidence_score * 100).toFixed(0)}%
            </span>
          )}
        </div>
        <div className="message-content">
          {msg.content}
        </div>
        {msg.metadata?.votes_received && msg.metadata.votes_received.length > 0 && (
          <div className="votes-received">
            Votes reçus: {msg.metadata.votes_received.map(v => `${v.voter}: ${v.score}`).join(', ')}
          </div>
        )}
      </div>
    );
  };
  
  const getAgentDisplayName = (agentId) => {
    const names = {
      'expert_1': '🤖 Expert Gemini',
      'expert_2': '🦙 Expert Llama',
      'expert_3': '🌊 Expert Mistral',
      'judge': '⚖️ Juge IA',
      'system': '📋 Système'
    };
    return names[agentId] || agentId;
  };
  
  const handleValidationDecision = (decision) => {
    ws.current.send({
      type: 'human_validation',
      decision: decision,
      timestamp: new Date().toISOString()
    });
    setValidationRequired(false);
  };
  
  return (
    <div className="debate-container">
      {/* Header avec infos débat */}
      <div className="debate-header">
        <div className="debate-info">
          <span className="phase-badge">{debatePhase}</span>
          <span className="round-counter">
            Tour {currentRound}/{maxRounds}
          </span>
          <div className="consensus-bar">
            <div 
              className="consensus-fill" 
              style={{ width: `${consensusLevel * 100}%` }}
            />
            <span className="consensus-label">
              Consensus: {(consensusLevel * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        
        {/* Kill Switch */}
        <button 
          className="kill-switch"
          onClick={() => ws.current.send({ type: 'kill_switch' })}
        >
          🛑 ARRÊT D'URGENCE
        </button>
      </div>
      
      {/* Zone de chat principal */}
      <div className="debate-messages">
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
      </div>
      
      {/* Panel de vote */}
      {isVoting && (
        <VotingPanel 
          messages={messages.filter(m => m.role === 'expert')}
          onVoteComplete={() => setIsVoting(false)}
        />
      )}
      
      {/* Validation humaine */}
      {validationRequired && (
        <HumanValidation
          debateState={{
            messages,
            currentRound,
            consensusLevel,
            phase: debatePhase
          }}
          onValidate={handleValidationDecision}
        />
      )}
      
      {/* Visualisation du pipeline */}
      <PipelineViewer />
    </div>
  );
};

export default DebateChat;
```

### Styles CSS pour le débat

```css
/* src/components/DebateChat.css */
.debate-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f7f8fa;
  font-family: 'Inter', sans-serif;
}

.debate-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 2px solid #e1e4e8;
}

.debate-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.phase-badge {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.round-counter {
  font-size: 16px;
  font-weight: 500;
  color: #666;
}

.consensus-bar {
  position: relative;
  width: 200px;
  height: 24px;
  background: #e9ecef;
  border-radius: 12px;
  overflow: hidden;
}

.consensus-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b, #ffd93d, #6bcf7f);
  transition: width 0.3s ease;
}

.consensus-label {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

.kill-switch {
  padding: 10px 20px;
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.kill-switch:hover {
  background: #c82333;
}

.debate-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f7f8fa;
}

.debate-message {
  margin-bottom: 20px;
  padding: 15px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.debate-message.expert {
  border-left: 4px solid #4285f4;
}

.debate-message.judge {
  border-left: 4px solid #9b59b6;
  background: #f8f4ff;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.agent-name {
  font-weight: 600;
  font-size: 14px;
}

.timestamp {
  font-size: 12px;
  color: #999;
}

.confidence {
  padding: 2px 8px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 12px;
  font-size: 12px;
}

.message-content {
  font-size: 15px;
  line-height: 1.6;
  color: #333;
}

.votes-received {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
  font-size: 13px;
  color: #666;
}

/* Responsive */
@media (max-width: 768px) {
  .debate-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .consensus-bar {
    width: 100%;
  }
}
```

---

## 🚀 DÉMARRAGE RAPIDE

### Installation Backend

```bash
# Backend Python
cd backend
pip install -r requirements.txt

# Requirements
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
google-generativeai==0.3.0
ollama==0.1.7
pydantic==2.5.0
asyncio==3.4.3
```

### Installation Frontend

```bash
# Frontend React
cd frontend
npm install

# Package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.5.0",
    "@mui/material": "^5.14.0"
  }
}
```

### Lancement

```bash
# Terminal 1 - Backend
python main.py

# Terminal 2 - Frontend
npm start

# Accès : http://localhost:3000
```

---

## 📊 MÉTRIQUES CLÉS

```yaml
debate_metrics:
  engagement:
    - messages_per_round
    - consensus_evolution
    - voting_participation
    
  quality:
    - hallucination_detection_rate
    - factual_accuracy_score
    - validation_success_rate
    
  efficiency:
    - rounds_to_consensus
    - human_intervention_count
    - decision_time
    
  compliance:
    - validation_checkpoints_passed
    - audit_trail_completeness
    - risk_mitigation_success
```

---

*Architecture finale avec débat visible, validation humaine et pipeline complet - Septembre 2025*