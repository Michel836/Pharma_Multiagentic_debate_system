# voting_system.py - Système de vote entre agents avec scoring transparent
import asyncio
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VotingSystem:
    """Système de vote entre agents avec scoring transparent"""
    
    def __init__(self):
        self.voting_history = []
        self.agent_performance = {}  # Track historique de performance
        
    async def conduct_vote(self, 
                          messages: List,  # DebateMessage objects
                          voters: List[str]) -> Dict:
        """Organise un vote entre agents"""
        
        logger.info(f"🗳️ Début du vote - {len(voters)} votants, {len(messages)} messages")
        
        voting_matrix = {}
        
        # Chaque agent vote pour les messages des autres
        for voter_id in voters:
            try:
                voter_scores = await self.get_voter_scores(voter_id, messages)
                voting_matrix[voter_id] = voter_scores
                logger.debug(f"Vote de {voter_id}: {len(voter_scores)} évaluations")
            except Exception as e:
                logger.error(f"Erreur vote {voter_id}: {str(e)}")
                voting_matrix[voter_id] = {}
        
        # Calculer les scores finaux
        final_scores = self.calculate_weighted_scores(voting_matrix)
        
        # Déterminer le gagnant
        winner = self.determine_winner(final_scores)
        
        # Calculer le niveau de consensus
        consensus_level = self.calculate_consensus(voting_matrix)
        
        # Enregistrer le vote
        vote_record = {
            'timestamp': datetime.utcnow(),
            'voting_matrix': voting_matrix,
            'final_scores': final_scores,
            'winner': winner,
            'consensus_level': consensus_level,
            'voters_count': len(voters),
            'messages_evaluated': len(messages)
        }
        
        self.voting_history.append(vote_record)
        
        # Mettre à jour les performances des agents
        self.update_agent_performance(vote_record, messages)
        
        logger.info(f"✅ Vote terminé - Gagnant: {winner}, Consensus: {consensus_level:.1%}")
        
        return vote_record
    
    async def get_voter_scores(self, 
                              voter_id: str,
                              messages: List) -> Dict:
        """Un agent vote sur les messages des autres"""
        
        scores = {}
        
        for message in messages:
            # Ne pas voter pour soi-même
            if message.agent_id == voter_id:
                continue
            
            try:
                # Critères de scoring
                score = await self.evaluate_message(message, voter_id)
                scores[message.id] = {
                    'message_id': message.id,
                    'agent_id': message.agent_id,
                    'score': score,
                    'criteria': await self.get_detailed_scoring_criteria(message, score),
                    'voter_confidence': self.get_voter_confidence(voter_id)
                }
            except Exception as e:
                logger.error(f"Erreur évaluation message {message.id} par {voter_id}: {str(e)}")
                scores[message.id] = {
                    'message_id': message.id,
                    'agent_id': message.agent_id,
                    'score': 0.0,
                    'error': str(e)
                }
        
        return scores
    
    async def evaluate_message(self, 
                              message,  # DebateMessage
                              evaluator_id: str) -> float:
        """Évalue un message selon plusieurs critères"""
        
        try:
            # Critères d'évaluation avec scores
            criteria_scores = {
                'factual_accuracy': await self.check_factual_accuracy(message),
                'relevance': await self.check_relevance(message),
                'consistency': await self.check_consistency(message),
                'completeness': await self.check_completeness(message),
                'clarity': await self.check_clarity(message)
            }
            
            # Pondération des critères (pharmaceutical context)
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
            
            # Bonus/malus selon le contexte
            final_score = self.apply_context_adjustments(final_score, message, evaluator_id)
            
            return min(max(final_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Erreur évaluation: {str(e)}")
            return 0.5  # Score neutre par défaut
    
    async def check_factual_accuracy(self, message) -> float:
        """Vérifie la précision factuelle (simplifié)"""
        
        content = message.content.lower()
        
        # Indicateurs positifs
        positive_indicators = [
            'étude', 'recherche', 'données', 'résultats', 'publication',
            'essai clinique', 'fda', 'ema', 'protocole', 'molécule'
        ]
        
        # Indicateurs négatifs
        negative_indicators = [
            'je pense', 'peut-être', 'probablement', 'il semblerait',
            'sans doute', 'approximativement'
        ]
        
        positive_count = sum(1 for ind in positive_indicators if ind in content)
        negative_count = sum(1 for ind in negative_indicators if ind in content)
        
        # Score basé sur les indicateurs
        base_score = 0.5
        base_score += (positive_count * 0.1)
        base_score -= (negative_count * 0.15)
        
        # Bonus pour les références spécifiques
        if any(year in content for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            base_score += 0.1
        
        # Bonus pour les termes techniques
        technical_terms = ['pharmacocinétique', 'biodisponibilité', 'métabolisme', 'demi-vie']
        if any(term in content for term in technical_terms):
            base_score += 0.1
        
        return min(max(base_score, 0.0), 1.0)
    
    async def check_relevance(self, message) -> float:
        """Vérifie la pertinence par rapport au contexte pharma"""
        
        content = message.content.lower()
        
        # Termes pharma pertinents
        pharma_terms = [
            'médicament', 'drug', 'molecule', 'princep actif', 'indication',
            'posologie', 'effet secondaire', 'interaction', 'contre-indication',
            'r&d', 'développement', 'recherche', 'clinique', 'préclinique'
        ]
        
        relevance_count = sum(1 for term in pharma_terms if term in content)
        
        # Score basé sur la densité de termes pertinents
        word_count = len(content.split())
        if word_count > 0:
            density = relevance_count / word_count
            return min(density * 10, 1.0)  # Normaliser
        
        return 0.0
    
    async def check_consistency(self, message) -> float:
        """Vérifie la cohérence interne du message"""
        
        content = message.content
        
        # Vérifications de cohérence basiques
        score = 0.8  # Score de base
        
        # Contradiction interne simple
        if 'non' in content and 'oui' in content:
            score -= 0.2
        
        if 'impossible' in content and 'possible' in content:
            score -= 0.1
        
        # Structure logique
        if any(marker in content for marker in ['d\'abord', 'ensuite', 'enfin', 'donc']):
            score += 0.1
        
        # Longueur appropriée (ni trop court ni trop long)
        length = len(content)
        if 50 < length < 500:
            score += 0.1
        elif length < 20 or length > 800:
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)
    
    async def check_completeness(self, message) -> float:
        """Vérifie la complétude de la réponse"""
        
        content = message.content.lower()
        
        # Éléments attendus dans une réponse pharma complète
        completeness_elements = [
            'mécanisme',  # Mécanisme d'action
            'sécurité',   # Aspects sécurité
            'efficacité', # Efficacité
            'dosage' or 'posologie',  # Posologie
            'patient',    # Considérations patient
        ]
        
        present_elements = sum(1 for element in completeness_elements if element in content)
        completeness_score = present_elements / len(completeness_elements)
        
        # Bonus pour les nuances et limitations
        if any(nuance in content for nuance in ['cependant', 'néanmoins', 'limitation', 'attention']):
            completeness_score += 0.2
        
        return min(completeness_score, 1.0)
    
    async def check_clarity(self, message) -> float:
        """Évalue la clarté du message"""
        
        content = message.content
        
        # Métriques de clarté
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Score basé sur la longueur des phrases
        clarity_score = 0.8
        
        if avg_sentence_length > 30:  # Phrases trop longues
            clarity_score -= 0.3
        elif avg_sentence_length < 5:  # Phrases trop courtes
            clarity_score -= 0.2
        
        # Bonus pour structure claire
        if content.count('\\n') > 0:  # Paragraphes
            clarity_score += 0.1
        
        # Malus pour caractères spéciaux excessifs
        special_chars = sum(1 for c in content if not c.isalnum() and c not in ' .,;!?\\n-')
        if special_chars > len(content) * 0.1:
            clarity_score -= 0.2
        
        return min(max(clarity_score, 0.0), 1.0)
    
    async def get_detailed_scoring_criteria(self, message, final_score: float) -> Dict:
        """Retourne les critères détaillés de scoring"""
        
        return {
            'factual_accuracy': await self.check_factual_accuracy(message),
            'relevance': await self.check_relevance(message),
            'consistency': await self.check_consistency(message),
            'completeness': await self.check_completeness(message),
            'clarity': await self.check_clarity(message),
            'final_score': final_score,
            'message_length': len(message.content),
            'confidence_bonus': message.confidence_score * 0.1
        }
    
    def apply_context_adjustments(self, base_score: float, message, evaluator_id: str) -> float:
        """Applique des ajustements contextuels au score"""
        
        adjusted_score = base_score
        
        # Bonus pour réponse rapide (si timestamp disponible)
        if hasattr(message, 'metadata') and 'response_time' in message.metadata:
            response_time = message.metadata['response_time']
            if response_time < 5000:  # Moins de 5 secondes
                adjusted_score += 0.05
        
        # Ajustement selon la performance historique de l'auteur
        if message.agent_id in self.agent_performance:
            historical_accuracy = self.agent_performance[message.agent_id].get('accuracy', 0.5)
            # Légère pondération basée sur l'historique
            adjusted_score = adjusted_score * 0.9 + historical_accuracy * 0.1
        
        # Malus pour erreurs techniques évidentes
        if '❌' in message.content or 'erreur' in message.content.lower():
            adjusted_score *= 0.5
        
        return adjusted_score
    
    def calculate_weighted_scores(self, voting_matrix: Dict) -> Dict:
        """Calcule les scores finaux pondérés"""
        
        message_scores = {}
        
        # Agrégation des votes
        for voter_id, votes in voting_matrix.items():
            voter_weight = self.get_voter_weight(voter_id)
            
            for message_id, vote_data in votes.items():
                if 'error' in vote_data:
                    continue  # Ignorer les votes avec erreur
                    
                if message_id not in message_scores:
                    message_scores[message_id] = {
                        'total_weighted_score': 0,
                        'total_weight': 0,
                        'vote_count': 0,
                        'voters': [],
                        'detailed_votes': []
                    }
                
                score = vote_data['score']
                weighted_score = score * voter_weight
                
                message_scores[message_id]['total_weighted_score'] += weighted_score
                message_scores[message_id]['total_weight'] += voter_weight
                message_scores[message_id]['vote_count'] += 1
                message_scores[message_id]['voters'].append(voter_id)
                message_scores[message_id]['detailed_votes'].append({
                    'voter': voter_id,
                    'score': score,
                    'weight': voter_weight,
                    'weighted_score': weighted_score
                })
        
        # Calcul des moyennes pondérées
        for message_id in message_scores:
            data = message_scores[message_id]
            if data['total_weight'] > 0:
                data['average_score'] = data['total_weighted_score'] / data['total_weight']
            else:
                data['average_score'] = 0
        
        return message_scores
    
    def get_voter_weight(self, voter_id: str) -> float:
        """Détermine le poids du vote d'un agent selon ses performances"""
        
        if voter_id not in self.agent_performance:
            return 1.0  # Poids par défaut pour nouveaux agents
        
        perf = self.agent_performance[voter_id]
        
        # Facteurs de pondération
        accuracy_weight = perf.get('historical_accuracy', 0.5)
        consistency_weight = perf.get('consistency_score', 0.5)
        participation_bonus = min(perf.get('votes_given', 0) / 10, 0.2)  # Bonus participation
        
        # Poids final entre 0.5 et 1.5
        weight = 0.5 + (accuracy_weight + consistency_weight) / 2 + participation_bonus
        
        return min(max(weight, 0.5), 1.5)
    
    def get_voter_confidence(self, voter_id: str) -> float:
        """Retourne la confiance dans les votes d'un agent"""
        
        if voter_id not in self.agent_performance:
            return 0.5
        
        perf = self.agent_performance[voter_id]
        return perf.get('voting_accuracy', 0.5)
    
    def determine_winner(self, final_scores: Dict) -> Optional[str]:
        """Détermine le gagnant du vote"""
        
        if not final_scores:
            return None
        
        # Trouver le message avec le meilleur score moyen
        best_message = max(
            final_scores.items(),
            key=lambda x: x[1].get('average_score', 0)
        )
        
        message_id, score_data = best_message
        
        # Retourner l'agent qui a écrit le message gagnant
        # (Il faudrait une référence au message pour récupérer l'agent_id)
        return {
            'message_id': message_id,
            'score': score_data.get('average_score', 0),
            'vote_count': score_data.get('vote_count', 0)
        }
    
    def calculate_consensus(self, voting_matrix: Dict) -> float:
        """Calcule le niveau de consensus entre votants"""
        
        if not voting_matrix or len(voting_matrix) < 2:
            return 0.0
        
        # Extraire tous les scores par message
        message_votes = {}
        
        for voter_id, votes in voting_matrix.items():
            for message_id, vote_data in votes.items():
                if 'error' in vote_data:
                    continue
                    
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
        consensus = 1.0 - min(avg_variance * 4, 1.0)  # Facteur d'ajustement
        
        return max(consensus, 0.0)
    
    def update_agent_performance(self, vote_record: Dict, messages: List):
        """Met à jour les performances des agents basées sur le vote"""
        
        # Obtenir les scores par agent
        final_scores = vote_record['final_scores']
        
        # Créer un mapping message_id -> agent_id
        message_to_agent = {msg.id: msg.agent_id for msg in messages}
        
        for message_id, score_data in final_scores.items():
            agent_id = message_to_agent.get(message_id)
            if not agent_id:
                continue
            
            if agent_id not in self.agent_performance:
                self.agent_performance[agent_id] = {
                    'historical_accuracy': 0.5,
                    'consistency_score': 0.5,
                    'votes_received': 0,
                    'total_score': 0,
                    'messages_evaluated': 0
                }
            
            perf = self.agent_performance[agent_id]
            
            # Mettre à jour les métriques
            perf['votes_received'] += score_data.get('vote_count', 0)
            perf['total_score'] += score_data.get('average_score', 0)
            perf['messages_evaluated'] += 1
            
            # Recalculer la précision historique
            if perf['messages_evaluated'] > 0:
                perf['historical_accuracy'] = perf['total_score'] / perf['messages_evaluated']
        
        # Mettre à jour les votants
        for voter_id in vote_record['voting_matrix'].keys():
            if voter_id not in self.agent_performance:
                self.agent_performance[voter_id] = {
                    'votes_given': 0,
                    'voting_accuracy': 0.5
                }
            
            self.agent_performance[voter_id]['votes_given'] += 1
    
    def get_voting_statistics(self) -> Dict:
        """Retourne les statistiques du système de vote"""
        
        return {
            'total_votes_conducted': len(self.voting_history),
            'agents_tracked': len(self.agent_performance),
            'average_consensus': np.mean([v['consensus_level'] for v in self.voting_history]) if self.voting_history else 0,
            'agent_performance_summary': {
                agent_id: {
                    'accuracy': perf.get('historical_accuracy', 0),
                    'participation': perf.get('votes_given', 0)
                }
                for agent_id, perf in self.agent_performance.items()
            }
        }