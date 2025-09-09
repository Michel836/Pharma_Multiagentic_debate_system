# human_validator.py - Gestionnaire de validation humaine
import asyncio
import uuid
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ValidationDecision(Enum):
    """Types de décision de validation"""
    APPROVE = "approve"
    REJECT = "reject" 
    MODIFY = "modify"
    ESCALATE = "escalate"

class ValidationStatus(Enum):
    """Statuts de validation"""
    PENDING = "pending"
    COMPLETED = "completed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

@dataclass
class ValidationRequest:
    """Requête de validation humaine"""
    validation_id: str
    content: str
    context: Dict[str, Any]
    requester: str
    priority: int = 1
    timeout_seconds: int = 300
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class ValidationResponse:
    """Réponse de validation humaine"""
    validation_id: str
    decision: ValidationDecision
    notes: str = ""
    score: float = 0.0
    validator_id: str = "unknown"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class HumanValidationManager:
    """Gestionnaire pour les validations humaines"""
    
    def __init__(self):
        self.pending_validations: Dict[str, ValidationRequest] = {}
        self.completed_validations: Dict[str, ValidationResponse] = {}
        self.validation_callbacks: Dict[str, Callable] = {}
        self.timeout_tasks: Dict[str, asyncio.Task] = {}
        
        # Statistiques
        self.stats = {
            'total_requests': 0,
            'completed': 0,
            'timeouts': 0,
            'cancelled': 0,
            'average_response_time': 0.0
        }
        
        logger.info("Gestionnaire de validation humaine initialisé")
    
    async def request_validation(self,
                                content: str,
                                context: Dict[str, Any],
                                requester: str,
                                priority: int = 1,
                                timeout_seconds: int = 300) -> str:
        """Demande une validation humaine"""
        
        validation_id = str(uuid.uuid4())
        
        request = ValidationRequest(
            validation_id=validation_id,
            content=content,
            context=context,
            requester=requester,
            priority=priority,
            timeout_seconds=timeout_seconds
        )
        
        self.pending_validations[validation_id] = request
        self.stats['total_requests'] += 1
        
        # Programmer le timeout
        timeout_task = asyncio.create_task(
            self._handle_timeout(validation_id, timeout_seconds)
        )
        self.timeout_tasks[validation_id] = timeout_task
        
        logger.info(f"📋 Validation demandée: {validation_id} par {requester}")
        logger.debug(f"Contenu: {content[:100]}...")
        
        # Notifier les observateurs
        await self._notify_validation_needed(request)
        
        return validation_id
    
    async def receive_human_decision(self,
                                   validation_id: str,
                                   decision: str,
                                   notes: str = "",
                                   score: float = 0.0,
                                   validator_id: str = "human") -> bool:
        """Reçoit une décision de validation humaine"""
        
        if validation_id not in self.pending_validations:
            logger.warning(f"Validation {validation_id} non trouvée ou déjà traitée")
            return False
        
        try:
            decision_enum = ValidationDecision(decision.lower())
        except ValueError:
            logger.error(f"Décision invalide: {decision}")
            return False
        
        # Créer la réponse
        response = ValidationResponse(
            validation_id=validation_id,
            decision=decision_enum,
            notes=notes,
            score=score,
            validator_id=validator_id
        )
        
        # Déplacer de pending vers completed
        request = self.pending_validations.pop(validation_id)
        self.completed_validations[validation_id] = response
        
        # Annuler le timeout
        if validation_id in self.timeout_tasks:
            self.timeout_tasks[validation_id].cancel()
            del self.timeout_tasks[validation_id]
        
        # Mettre à jour les stats
        self.stats['completed'] += 1
        response_time = (response.timestamp - request.created_at).total_seconds()
        self._update_average_response_time(response_time)
        
        logger.info(f"✅ Validation reçue: {validation_id} -> {decision_enum.value} par {validator_id}")
        if notes:
            logger.info(f"Notes: {notes[:100]}...")
        
        # Exécuter le callback si présent
        if validation_id in self.validation_callbacks:
            callback = self.validation_callbacks.pop(validation_id)
            try:
                await callback(response)
            except Exception as e:
                logger.error(f"Erreur callback validation {validation_id}: {str(e)}")
        
        return True
    
    async def wait_for_validation(self,
                                 validation_id: str,
                                 callback: Callable[[ValidationResponse], None] = None) -> Optional[ValidationResponse]:
        """Attend une validation spécifique"""
        
        if validation_id not in self.pending_validations:
            # Vérifier si déjà complétée
            if validation_id in self.completed_validations:
                return self.completed_validations[validation_id]
            return None
        
        # Enregistrer le callback
        if callback:
            self.validation_callbacks[validation_id] = callback
        
        # Attendre la completion ou le timeout
        request = self.pending_validations[validation_id]
        timeout = request.timeout_seconds
        
        start_time = time.time()
        while validation_id in self.pending_validations and (time.time() - start_time) < timeout:
            await asyncio.sleep(1)
        
        # Retourner le résultat si disponible
        return self.completed_validations.get(validation_id)
    
    async def cancel_validation(self, validation_id: str, reason: str = "Cancelled") -> bool:
        """Annule une validation en attente"""
        
        if validation_id not in self.pending_validations:
            return False
        
        # Supprimer la requête
        request = self.pending_validations.pop(validation_id)
        
        # Annuler le timeout
        if validation_id in self.timeout_tasks:
            self.timeout_tasks[validation_id].cancel()
            del self.timeout_tasks[validation_id]
        
        # Supprimer le callback
        if validation_id in self.validation_callbacks:
            del self.validation_callbacks[validation_id]
        
        self.stats['cancelled'] += 1
        
        logger.info(f"🚫 Validation annulée: {validation_id} - {reason}")
        
        return True
    
    async def get_pending_validations(self) -> List[Dict[str, Any]]:
        """Retourne la liste des validations en attente"""
        
        validations = []
        for request in self.pending_validations.values():
            validations.append({
                'validation_id': request.validation_id,
                'content': request.content,
                'context': request.context,
                'requester': request.requester,
                'priority': request.priority,
                'created_at': request.created_at.isoformat(),
                'timeout_seconds': request.timeout_seconds,
                'age_seconds': (datetime.utcnow() - request.created_at).total_seconds()
            })
        
        # Trier par priorité puis par âge
        validations.sort(key=lambda x: (-x['priority'], -x['age_seconds']))
        
        return validations
    
    async def get_validation_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de validation"""
        
        return {
            **self.stats,
            'pending_count': len(self.pending_validations),
            'active_timeouts': len(self.timeout_tasks),
            'oldest_pending': self._get_oldest_pending_age()
        }
    
    async def _handle_timeout(self, validation_id: str, timeout_seconds: int):
        """Gère le timeout d'une validation"""
        
        try:
            await asyncio.sleep(timeout_seconds)
            
            if validation_id in self.pending_validations:
                # Timeout atteint
                request = self.pending_validations.pop(validation_id)
                
                # Créer une réponse de timeout
                response = ValidationResponse(
                    validation_id=validation_id,
                    decision=ValidationDecision.REJECT,
                    notes="Validation timeout - Aucune réponse humaine reçue",
                    score=0.0,
                    validator_id="system"
                )
                
                self.completed_validations[validation_id] = response
                self.stats['timeouts'] += 1
                
                logger.warning(f"⏰ Timeout validation: {validation_id} après {timeout_seconds}s")
                
                # Exécuter le callback si présent
                if validation_id in self.validation_callbacks:
                    callback = self.validation_callbacks.pop(validation_id)
                    try:
                        await callback(response)
                    except Exception as e:
                        logger.error(f"Erreur callback timeout {validation_id}: {str(e)}")
        
        except asyncio.CancelledError:
            # Tâche annulée normalement
            pass
        finally:
            # Nettoyer
            if validation_id in self.timeout_tasks:
                del self.timeout_tasks[validation_id]
    
    async def _notify_validation_needed(self, request: ValidationRequest):
        """Notifie qu'une validation est nécessaire"""
        
        # Ici on pourrait envoyer des notifications via WebSocket, email, etc.
        logger.info(f"🔔 Notification: Validation requise {request.validation_id}")
        
        # Exemple de notification WebSocket (à implémenter)
        # await self._send_websocket_notification({
        #     'type': 'validation_needed',
        #     'validation_id': request.validation_id,
        #     'content': request.content[:200] + '...' if len(request.content) > 200 else request.content,
        #     'priority': request.priority,
        #     'timeout_seconds': request.timeout_seconds
        # })
    
    def _update_average_response_time(self, response_time: float):
        """Met à jour le temps de réponse moyen"""
        
        if self.stats['completed'] <= 1:
            self.stats['average_response_time'] = response_time
        else:
            # Moyenne mobile
            current_avg = self.stats['average_response_time']
            count = self.stats['completed']
            self.stats['average_response_time'] = (current_avg * (count - 1) + response_time) / count
    
    def _get_oldest_pending_age(self) -> Optional[float]:
        """Retourne l'âge de la plus ancienne validation en attente"""
        
        if not self.pending_validations:
            return None
        
        oldest = min(
            self.pending_validations.values(),
            key=lambda r: r.created_at
        )
        
        return (datetime.utcnow() - oldest.created_at).total_seconds()
    
    async def cleanup_old_validations(self, max_age_hours: int = 24):
        """Nettoie les anciennes validations complétées"""
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        old_validations = [
            vid for vid, response in self.completed_validations.items()
            if response.timestamp < cutoff
        ]
        
        for validation_id in old_validations:
            del self.completed_validations[validation_id]
        
        logger.info(f"🧹 Nettoyage: {len(old_validations)} anciennes validations supprimées")
        
        return len(old_validations)

# Singleton global pour l'application
_human_validator_instance = None

def get_human_validator() -> HumanValidationManager:
    """Retourne l'instance singleton du gestionnaire de validation"""
    global _human_validator_instance
    
    if _human_validator_instance is None:
        _human_validator_instance = HumanValidationManager()
    
    return _human_validator_instance