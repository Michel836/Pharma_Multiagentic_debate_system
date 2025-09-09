# debate_manager.py - Gestionnaire principal du débat visible
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class DebateRole(Enum):
    EXPERT = "expert"
    JUDGE = "judge"
    HUMAN = "human"
    SYSTEM = "system"

class DebatePhase(Enum):
    INITIALIZATION = "initialization"
    OPENING_STATEMENTS = "opening_statements"
    ARGUMENTATION = "argumentation"
    VOTING = "voting"
    HUMAN_VALIDATION = "human_validation"
    SYNTHESIS = "synthesis"
    FINAL_VALIDATION = "final_validation"
    COMPLETED = "completed"

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
        
    def to_dict(self) -> Dict:
        """Convertit en dictionnaire pour JSON"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "role": self.role.value,
            "content": self.content,
            "metadata": self.metadata,
            "votes_received": self.votes_received,
            "confidence_score": self.confidence_score
        }

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
        self.voting_results = {}
        self.consensus_scores = []
        self.started_at = datetime.utcnow()
        self.stopped = False
        self.stop_reason = None
        
    async def initialize_debate(self, 
                               query: str,
                               experts: List[Dict],
                               judge: Dict) -> str:
        """Initialise un nouveau débat"""
        
        logger.info(f"STARTUP: Initialisation du débat {self.debate_id[:8]}...")
        
        # Enregistrer les participants
        for expert in experts:
            self.participants[expert['id']] = {
                'role': DebateRole.EXPERT,
                'provider': expert['provider'],
                'model': expert['model'],
                'temperature': expert.get('temperature', 0.7),
                'score': 0,
                'messages_count': 0,
                'votes_given': 0,
                'performance_history': []
            }
        
        self.participants[judge['id']] = {
            'role': DebateRole.JUDGE,
            'provider': judge['provider'],
            'model': judge['model'],
            'score': 0,
            'decisions_made': 0
        }
        
        # Message d'ouverture
        opening_msg = DebateMessage(
            agent_id="system",
            role=DebateRole.SYSTEM,
            content=f"INFO: Débat démarré : {query}\\n\\nINFO: Participants :{self._format_participants()}",
            metadata={
                'query': query, 
                'phase': 'opening',
                'participants_count': len(self.participants)
            }
        )
        
        await self.broadcast_message(opening_msg)
        self.messages.append(opening_msg)
        
        self.current_phase = DebatePhase.OPENING_STATEMENTS
        
        logger.info(f"SUCCESS: Débat initialisé avec {len(experts)} experts + 1 juge")
        
        return self.debate_id
    
    def _format_participants(self) -> str:
        """Formate la liste des participants pour affichage"""
        
        lines = []
        for pid, pdata in self.participants.items():
            if pdata['role'] == DebateRole.EXPERT:
                icon = "[GEMINI]" if "gemini" in pdata['provider'] else "[OLLAMA]"
                lines.append(f"\\n  {icon} {pid} ({pdata['model']})")
            elif pdata['role'] == DebateRole.JUDGE:
                lines.append(f"\\n  [JUDGE] {pid} (Juge)")
        
        return "".join(lines)
    
    async def conduct_round(self, topic: str, context: Dict) -> Dict:
        """Conduit un tour de débat"""
        
        if self.stopped:
            return {"error": "Debate has been stopped", "reason": self.stop_reason}
        
        self.current_round += 1
        
        logger.info(f"PROCESSING: Tour {self.current_round}/{self.max_rounds} - Phase: {self.current_phase.value}")
        
        # Vérifier limite de tours
        if self.current_round > self.max_rounds:
            return await self.force_conclusion("Limite de tours atteinte")
        
        round_messages = []
        
        try:
            # Phase 1: Déclarations d'ouverture
            if self.current_phase == DebatePhase.OPENING_STATEMENTS:
                await self._announce_phase("Déclarations d'ouverture")
                
                for participant_id, participant in self.participants.items():
                    if participant['role'] == DebateRole.EXPERT:
                        response = await self.get_expert_statement(
                            participant_id, topic, context
                        )
                        round_messages.append(response)
                        
                        # Petit délai pour l'effet visuel
                        await asyncio.sleep(1)
                
                self.current_phase = DebatePhase.ARGUMENTATION
            
            # Phase 2: Argumentation
            elif self.current_phase == DebatePhase.ARGUMENTATION:
                await self._announce_phase("Argumentation et débat")
                
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
                        await asyncio.sleep(1)
                
                # Vérifier si on passe au vote
                if self.should_proceed_to_voting():
                    self.current_phase = DebatePhase.VOTING
            
            # Phase 3: Vote
            elif self.current_phase == DebatePhase.VOTING:
                await self._announce_phase("Vote entre agents")
                
                voting_results = await self.conduct_voting()
                self.voting_results = voting_results
                
                # Checkpoint validation humaine
                self.current_phase = DebatePhase.HUMAN_VALIDATION
                return {
                    'phase': 'voting_complete',
                    'round': self.current_round,
                    'voting_results': voting_results,
                    'requires_human_validation': True,
                    'validation_data': self._prepare_validation_data()
                }
        
        except Exception as e:
            logger.error(f"Erreur durant le tour {self.current_round}: {str(e)}")
            await self._announce_error(f"Erreur: {str(e)}")
            return {"error": str(e), "round": self.current_round}
        
        return {
            'round': self.current_round,
            'phase': self.current_phase.value,
            'messages': [msg.to_dict() for msg in round_messages],
            'consensus_score': self.calculate_current_consensus(),
            'should_continue': not self.should_force_stop()
        }
    
    async def _announce_phase(self, phase_name: str):
        """Annonce une nouvelle phase du débat"""
        
        phase_msg = DebateMessage(
            agent_id="system",
            role=DebateRole.SYSTEM,
            content=f"INFO: Phase : {phase_name}",
            metadata={
                'phase_change': True,
                'round': self.current_round,
                'phase': self.current_phase.value
            }
        )
        
        await self.broadcast_message(phase_msg)
        self.messages.append(phase_msg)
    
    async def _announce_error(self, error_msg: str):
        """Annonce une erreur dans le débat"""
        
        error_message = DebateMessage(
            agent_id="system",
            role=DebateRole.SYSTEM,
            content=f"ERROR: {error_msg}",
            metadata={
                'error': True,
                'round': self.current_round,
                'phase': self.current_phase.value
            }
        )
        
        await self.broadcast_message(error_message)
        self.messages.append(error_message)
    
    async def get_expert_statement(self, 
                                  expert_id: str,
                                  topic: str,
                                  context: Dict) -> DebateMessage:
        """Obtient la déclaration d'un expert"""
        
        expert = self.participants[expert_id]
        
        # Import des providers ici pour éviter la dépendance circulaire
        from agents.llm_providers import get_provider
        
        provider = get_provider(expert['provider'], expert['model'])
        
        # Construire le prompt
        prompt = self._build_expert_prompt(expert_id, topic, context, is_opening=True)
        
        try:
            # Appel au LLM
            response_data = await provider.generate(prompt, context)
            response_text = response_data['response']
            
            # Calculer score de confiance
            confidence = response_data['metadata'].get('confidence', 0.5)
            
        except Exception as e:
            logger.error(f"Erreur LLM pour {expert_id}: {str(e)}")
            response_text = f"ERROR: Erreur de connexion au modèle {expert['model']}"
            confidence = 0.0
        
        # Créer message de débat
        message = DebateMessage(
            agent_id=expert_id,
            role=DebateRole.EXPERT,
            content=response_text,
            metadata={
                'round': self.current_round,
                'phase': self.current_phase.value,
                'model': expert['model'],
                'provider': expert['provider'],
                'temperature': expert['temperature'],
                'is_opening_statement': True
            }
        )
        
        message.confidence_score = confidence
        
        # Broadcaster aux clients
        await self.broadcast_message(message)
        
        self.messages.append(message)
        expert['messages_count'] += 1
        
        return message
    
    async def get_expert_argument(self, 
                                 expert_id: str,
                                 topic: str,
                                 previous_arguments: List[str],
                                 context: Dict) -> DebateMessage:
        """Obtient un argument d'expert en réponse aux autres"""
        
        expert = self.participants[expert_id]
        
        from agents.llm_providers import get_provider
        provider = get_provider(expert['provider'], expert['model'])
        
        # Prompt avec arguments précédents
        prompt = self._build_expert_argument_prompt(
            expert_id, topic, previous_arguments, context
        )
        
        try:
            response_data = await provider.generate(prompt, context)
            response_text = response_data['response']
            confidence = response_data['metadata'].get('confidence', 0.5)
            
        except Exception as e:
            logger.error(f"Erreur argument {expert_id}: {str(e)}")
            response_text = f"❌ Impossible de formuler un argument - Erreur modèle"
            confidence = 0.0
        
        message = DebateMessage(
            agent_id=expert_id,
            role=DebateRole.EXPERT,
            content=response_text,
            metadata={
                'round': self.current_round,
                'phase': self.current_phase.value,
                'model': expert['model'],
                'is_argument': True,
                'responds_to': [msg.agent_id for msg in self.messages[-3:] if msg.role == DebateRole.EXPERT]
            }
        )
        
        message.confidence_score = confidence
        
        await self.broadcast_message(message)
        self.messages.append(message)
        expert['messages_count'] += 1
        
        return message
    
    def _build_expert_prompt(self, expert_id: str, topic: str, context: Dict, is_opening: bool = False) -> str:
        """Construit le prompt pour un expert"""
        
        expert = self.participants[expert_id]
        
        if is_opening:
            return f"""You are an expert pharmaceutical researcher participating in a critical R&D debate.
            
TOPIC: {topic}

CONTEXT: {context.get('rag_results', 'No additional context available')}

INSTRUCTIONS:
- Provide your expert analysis and initial position
- Be factual, precise, and evidence-based
- Highlight key scientific points and considerations
- Keep your response focused and under 200 words
- Avoid speculation - stick to known facts
- If uncertain, clearly state limitations

Your expertise perspective as {expert_id}: Focus on {self._get_expert_focus(expert_id)}"""
        
        else:
            previous_messages = "\\n".join([
                f"{msg.agent_id}: {msg.content[:100]}..."
                for msg in self.messages[-3:] 
                if msg.role == DebateRole.EXPERT and msg.agent_id != expert_id
            ])
            
            return f"""Continue the pharmaceutical R&D debate on: {topic}

PREVIOUS ARGUMENTS:
{previous_messages}

INSTRUCTIONS:
- Respond to the arguments above
- Provide counter-arguments or supporting evidence
- Stay factual and evidence-based
- Cite specific considerations when possible
- Keep response under 200 words
- Be respectful but firm in your position

Your perspective: {self._get_expert_focus(expert_id)}"""
    
    def _build_expert_argument_prompt(self, expert_id: str, topic: str, previous_arguments: List[str], context: Dict) -> str:
        """Construit le prompt d'argument pour un expert"""
        
        args_text = "\\n".join([f"- {arg[:100]}..." for arg in previous_arguments[-3:]])
        
        return f"""PHARMACEUTICAL R&D DEBATE CONTINUATION

Topic: {topic}
Your role: {expert_id}

Previous arguments from colleagues:
{args_text}

Instructions:
- Analyze the previous arguments
- Provide your expert perspective
- Support or challenge points with evidence
- Stay within pharmaceutical/scientific domain
- Be concise (under 150 words)
- Maintain professional tone"""
    
    def _get_expert_focus(self, expert_id: str) -> str:
        """Retourne le focus d'expertise de l'agent"""
        
        focuses = {
            "expert_gemini": "drug discovery and molecular mechanisms",
            "expert_llama": "clinical research and regulatory affairs", 
            "expert_mistral": "pharmacokinetics and safety assessment",
            "expert_qwen": "biostatistics and data analysis"
        }
        
        return focuses.get(expert_id, "general pharmaceutical research")
    
    def get_previous_arguments(self) -> List[str]:
        """Récupère les arguments précédents du débat"""
        
        arguments = []
        for msg in self.messages:
            if msg.role == DebateRole.EXPERT and len(msg.content) > 50:
                arguments.append(msg.content)
        
        return arguments[-5:]  # 5 derniers arguments max
    
    def should_proceed_to_voting(self) -> bool:
        """Détermine si on doit passer au vote"""
        
        # Critères pour passer au vote
        if self.current_round >= 3:
            return True
        
        # Si consensus détecté
        if self.calculate_current_consensus() > 0.8:
            return True
        
        # Si divergence excessive
        if self.detect_divergence() > 0.9:
            return True
        
        # Si assez d'échanges
        expert_messages = [m for m in self.messages if m.role == DebateRole.EXPERT]
        if len(expert_messages) >= 6:
            return True
        
        return False
    
    def should_force_stop(self) -> bool:
        """Détermine si le débat doit être arrêté de force"""
        
        # Trop de tours
        if self.current_round >= self.max_rounds:
            return True
        
        # Pas d'activité récente
        if len(self.messages) > 0:
            last_message_time = self.messages[-1].timestamp
            if (datetime.utcnow() - last_message_time).seconds > 300:  # 5 min
                return True
        
        # Erreurs répétées
        recent_errors = [
            m for m in self.messages[-5:] 
            if "❌" in m.content or "erreur" in m.content.lower()
        ]
        if len(recent_errors) >= 3:
            return True
        
        return False
    
    def calculate_current_consensus(self) -> float:
        """Calcule le niveau de consensus actuel"""
        
        expert_messages = [m for m in self.messages if m.role == DebateRole.EXPERT]
        
        if len(expert_messages) < 2:
            return 0.0
        
        # Analyse simplifiée des derniers messages
        recent_messages = expert_messages[-3:]
        
        # Extraction des mots-clés
        keywords_sets = []
        for msg in recent_messages:
            words = set(msg.content.lower().split())
            # Filtrer les mots significatifs
            keywords = {w for w in words if len(w) > 4 and w.isalpha()}
            keywords_sets.append(keywords)
        
        if not keywords_sets:
            return 0.0
        
        # Intersection des mots-clés
        common = keywords_sets[0]
        for kw_set in keywords_sets[1:]:
            common = common.intersection(kw_set)
        
        avg_keywords = sum(len(kw) for kw in keywords_sets) / len(keywords_sets)
        consensus = len(common) / max(avg_keywords, 1)
        
        # Stocker pour historique
        self.consensus_scores.append(consensus)
        
        return min(consensus, 1.0)
    
    def detect_divergence(self) -> float:
        """Détecte le niveau de divergence"""
        
        # Simple: inverse du consensus
        consensus = self.calculate_current_consensus()
        return 1.0 - consensus
    
    async def broadcast_message(self, message: DebateMessage):
        """Envoie le message à tous les clients WebSocket"""
        
        if not self.websocket_clients:
            return
        
        formatted_msg = message.to_dict()
        
        # Envoyer à tous les clients connectés
        disconnected_clients = []
        for client in self.websocket_clients:
            try:
                await client.send_json(formatted_msg)
            except Exception as e:
                logger.warning(f"Client WebSocket déconnecté: {str(e)}")
                disconnected_clients.append(client)
        
        # Nettoyer les clients déconnectés
        for client in disconnected_clients:
            self.websocket_clients.remove(client)
    
    async def conduct_voting(self) -> Dict:
        """Système de vote entre agents"""
        
        from .voting_system import VotingSystem
        
        voting_system = VotingSystem()
        
        # Messages d'experts récents à voter
        votable_messages = [
            msg for msg in self.messages 
            if msg.role == DebateRole.EXPERT and msg.current_round >= self.current_round - 1
        ]
        
        # Liste des votants (tous les experts)
        voters = [
            pid for pid, pdata in self.participants.items() 
            if pdata['role'] == DebateRole.EXPERT
        ]
        
        # Conduire le vote
        vote_results = await voting_system.conduct_vote(votable_messages, voters)
        
        # Annoncer les résultats
        results_msg = DebateMessage(
            agent_id="system",
            role=DebateRole.SYSTEM,
            content=f"📊 **Résultats du vote (Tour {self.current_round})**\\n{self._format_voting_results(vote_results)}",
            metadata={
                'voting_results': vote_results,
                'round': self.current_round,
                'voters_count': len(voters)
            }
        )
        
        await self.broadcast_message(results_msg)
        self.messages.append(results_msg)
        
        return vote_results
    
    def _format_voting_results(self, results: Dict) -> str:
        """Formate les résultats de vote pour affichage"""
        
        lines = []
        final_scores = results.get('final_scores', {})
        
        # Trier par score
        sorted_scores = sorted(
            final_scores.items(), 
            key=lambda x: x[1].get('average_score', 0), 
            reverse=True
        )
        
        for i, (message_id, score_data) in enumerate(sorted_scores[:3], 1):
            # Trouver le message correspondant
            msg = next((m for m in self.messages if m.id == message_id), None)
            if msg:
                score = score_data.get('average_score', 0)
                lines.append(f"{i}. **{msg.agent_id}** - Score: {score:.2f}")
        
        consensus_level = results.get('consensus_level', 0)
        lines.append(f"\\n🤝 Niveau de consensus: {consensus_level:.1%}")
        
        return "\\n".join(lines)
    
    def _prepare_validation_data(self) -> Dict:
        """Prépare les données pour la validation humaine"""
        
        return {
            'debate_id': self.debate_id,
            'current_round': self.current_round,
            'phase': self.current_phase.value,
            'participants_count': len(self.participants),
            'messages_count': len(self.messages),
            'consensus_score': self.calculate_current_consensus(),
            'voting_results': self.voting_results,
            'key_arguments': self._extract_key_arguments(),
            'risk_assessment': self._assess_current_risks()
        }
    
    def _extract_key_arguments(self) -> List[Dict]:
        """Extrait les arguments clés du débat"""
        
        expert_messages = [m for m in self.messages if m.role == DebateRole.EXPERT]
        
        # Prendre les messages les plus récents et les plus longs
        key_messages = sorted(
            expert_messages[-6:], 
            key=lambda x: len(x.content), 
            reverse=True
        )[:3]
        
        return [
            {
                'agent': msg.agent_id,
                'content': msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                'confidence': msg.confidence_score,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in key_messages
        ]
    
    def _assess_current_risks(self) -> Dict:
        """Évalue les risques actuels du débat"""
        
        risk_score = 0
        risk_factors = []
        
        # Consensus faible
        consensus = self.calculate_current_consensus()
        if consensus < 0.5:
            risk_score += 0.3
            risk_factors.append("Consensus faible entre experts")
        
        # Trop de tours
        if self.current_round >= self.max_rounds * 0.8:
            risk_score += 0.2
            risk_factors.append("Approche de la limite de tours")
        
        # Erreurs récentes
        recent_errors = sum(1 for m in self.messages[-5:] if "❌" in m.content)
        if recent_errors > 0:
            risk_score += 0.3 * recent_errors
            risk_factors.append(f"{recent_errors} erreur(s) technique(s)")
        
        # Confiance faible
        recent_confidences = [
            m.confidence_score for m in self.messages[-3:] 
            if m.role == DebateRole.EXPERT and m.confidence_score > 0
        ]
        if recent_confidences and sum(recent_confidences) / len(recent_confidences) < 0.6:
            risk_score += 0.2
            risk_factors.append("Niveau de confiance des agents faible")
        
        return {
            'risk_score': min(risk_score, 1.0),
            'risk_level': 'LOW' if risk_score < 0.3 else 'MEDIUM' if risk_score < 0.6 else 'HIGH',
            'risk_factors': risk_factors
        }
    
    async def force_conclusion(self, reason: str) -> Dict:
        """Force la conclusion du débat"""
        
        logger.warning(f"🛑 Conclusion forcée du débat {self.debate_id[:8]}: {reason}")
        
        self.stopped = True
        self.stop_reason = reason
        self.current_phase = DebatePhase.COMPLETED
        
        # Message de conclusion
        conclusion_msg = DebateMessage(
            agent_id="system",
            role=DebateRole.SYSTEM,
            content=f"🏁 **Débat terminé** - {reason}\\n\\n📊 Statistiques finales:\\n{self._generate_final_stats()}",
            metadata={
                'conclusion': True,
                'reason': reason,
                'forced': True,
                'final_stats': self._generate_final_stats_dict()
            }
        )
        
        await self.broadcast_message(conclusion_msg)
        self.messages.append(conclusion_msg)
        
        return {
            'status': 'concluded',
            'reason': reason,
            'final_phase': self.current_phase.value,
            'total_rounds': self.current_round,
            'total_messages': len(self.messages),
            'final_consensus': self.calculate_current_consensus()
        }
    
    async def force_stop(self, reason: str):
        """Arrête le débat immédiatement (kill switch)"""
        
        await self.force_conclusion(f"Arrêt d'urgence: {reason}")
    
    def _generate_final_stats(self) -> str:
        """Génère les statistiques finales pour affichage"""
        
        expert_msgs = [m for m in self.messages if m.role == DebateRole.EXPERT]
        
        stats = []
        stats.append(f"• Tours complétés: {self.current_round}/{self.max_rounds}")
        stats.append(f"• Messages total: {len(self.messages)}")
        stats.append(f"• Messages d'experts: {len(expert_msgs)}")
        stats.append(f"• Consensus final: {self.calculate_current_consensus():.1%}")
        stats.append(f"• Durée: {self._calculate_duration()}")
        
        return "\\n".join(stats)
    
    def _generate_final_stats_dict(self) -> Dict:
        """Génère les statistiques finales en dictionnaire"""
        
        return {
            'rounds_completed': self.current_round,
            'max_rounds': self.max_rounds,
            'total_messages': len(self.messages),
            'expert_messages': len([m for m in self.messages if m.role == DebateRole.EXPERT]),
            'final_consensus': self.calculate_current_consensus(),
            'duration_minutes': (datetime.utcnow() - self.started_at).seconds / 60,
            'participants': len(self.participants),
            'validation_checkpoints': len(self.human_validations)
        }
    
    def _calculate_duration(self) -> str:
        """Calcule la durée du débat"""
        
        duration = datetime.utcnow() - self.started_at
        minutes = duration.seconds // 60
        seconds = duration.seconds % 60
        
        return f"{minutes}min {seconds}s"