# main.py - Point d'entrée principal du système multiagent
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List, Optional
import json
from datetime import datetime
import logging

from agents.orchestrator import MultiAgentOrchestrator
from debate.debate_manager import VisibleDebateManager
from validation.human_validator import HumanValidationManager
from utils.config import load_config
from utils.logger import setup_logging

# Configuration du logging
setup_logging()
logger = logging.getLogger(__name__)

# Application FastAPI
app = FastAPI(
    title="Pharma MultiAgent Debate System",
    description="Système de débat multiagent avec validation humaine pour R&D pharmaceutique",
    version="1.0.0"
)

# Configuration CORS pour React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaires globaux
orchestrator = MultiAgentOrchestrator()
active_debates: Dict[str, VisibleDebateManager] = {}
human_validator = HumanValidationManager()
connected_clients: List[WebSocket] = []

# Configuration
config = load_config()

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage du système multiagent pharma...")
    
    # Initialiser les providers LLM
    await orchestrator.initialize_providers(config["llm_providers"])
    
    logger.info("✅ Système multiagent initialisé avec succès")

@app.get("/")
async def serve_frontend():
    """Sert l'interface React"""
    return FileResponse("../frontend/build/index.html")

@app.get("/health")
async def health_check():
    """Vérification de l'état du système"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_debates": len(active_debates),
        "connected_clients": len(connected_clients),
        "providers_status": await orchestrator.get_providers_status()
    }

@app.post("/api/start-debate")
async def start_debate(request: Dict):
    """Démarre un nouveau débat"""
    try:
        # Créer un nouveau débat
        debate_manager = VisibleDebateManager(
            max_rounds=request.get("max_rounds", 5)
        )
        
        # Configuration des participants
        experts = request.get("experts", [
            {"id": "expert_gemini", "provider": "gemini", "model": "gemini-pro", "temperature": 0.3},
            {"id": "expert_llama", "provider": "ollama", "model": "llama3.2", "temperature": 0.5},
            {"id": "expert_mistral", "provider": "ollama", "model": "mistral:7b", "temperature": 0.4}
        ])
        
        judge = {"id": "judge", "provider": "gemini", "model": "gemini-pro", "temperature": 0.1}
        
        # Initialiser le débat
        debate_id = await debate_manager.initialize_debate(
            query=request["query"],
            experts=experts,
            judge=judge
        )
        
        # Stocker le débat actif
        active_debates[debate_id] = debate_manager
        
        # Connecter aux WebSockets
        debate_manager.websocket_clients = connected_clients.copy()
        
        logger.info(f"Débat démarré: {debate_id} pour la requête: {request['query'][:50]}...")
        
        return {
            "debate_id": debate_id,
            "status": "started",
            "participants": len(experts) + 1,
            "query": request["query"]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du débat: {str(e)}")
        return {"error": str(e)}, 500

@app.post("/api/debate/{debate_id}/round")
async def conduct_round(debate_id: str, context: Dict):
    """Lance un tour de débat"""
    
    if debate_id not in active_debates:
        return {"error": "Débat non trouvé"}, 404
    
    try:
        debate_manager = active_debates[debate_id]
        
        result = await debate_manager.conduct_round(
            topic=context.get("query", ""),
            context=context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur tour de débat {debate_id}: {str(e)}")
        return {"error": str(e)}, 500

@app.post("/api/human-validation")
async def receive_human_validation(request: Dict):
    """Reçoit une validation humaine"""
    
    try:
        validation_id = request["validation_id"]
        decision = request["decision"]
        notes = request.get("notes", "")
        score = request.get("score", 0)
        
        await human_validator.receive_human_decision(
            validation_id=validation_id,
            decision=decision,
            notes=notes,
            score=score
        )
        
        logger.info(f"Validation humaine reçue: {validation_id} -> {decision}")
        
        return {"status": "received", "decision": decision}
        
    except Exception as e:
        logger.error(f"Erreur validation humaine: {str(e)}")
        return {"error": str(e)}, 500

@app.post("/api/kill-switch")
async def trigger_kill_switch(request: Dict = None):
    """Active le kill switch d'urgence"""
    
    try:
        # Arrêter tous les débats actifs
        for debate_id, debate_manager in active_debates.items():
            await debate_manager.force_stop("Kill switch activated")
        
        # Notifier tous les clients
        notification = {
            "type": "kill_switch_activated",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Tous les débats ont été arrêtés"
        }
        
        for client in connected_clients:
            await client.send_json(notification)
        
        logger.warning("🛑 Kill switch activé - Tous les débats arrêtés")
        
        return {"status": "activated", "debates_stopped": len(active_debates)}
        
    except Exception as e:
        logger.error(f"Erreur kill switch: {str(e)}")
        return {"error": str(e)}, 500

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour communication temps réel"""
    
    await websocket.accept()
    connected_clients.append(websocket)
    
    logger.info(f"Client WebSocket connecté. Total: {len(connected_clients)}")
    
    try:
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Traiter selon le type de message
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
            
            elif message.get("type") == "join_debate":
                debate_id = message.get("debate_id")
                if debate_id in active_debates:
                    active_debates[debate_id].websocket_clients.append(websocket)
                    await websocket.send_json({"type": "joined", "debate_id": debate_id})
            
            elif message.get("type") == "human_validation":
                # Traitement de la validation humaine
                await human_validator.receive_human_decision(
                    validation_id=message.get("validation_id"),
                    decision=message.get("decision"),
                    notes=message.get("notes", ""),
                    score=message.get("score", 0)
                )
            
            elif message.get("type") == "kill_switch":
                # Déclenchement kill switch depuis WebSocket
                await trigger_kill_switch()
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Client WebSocket déconnecté. Total: {len(connected_clients)}")
        
        # Nettoyer les références dans les débats actifs
        for debate_manager in active_debates.values():
            if websocket in debate_manager.websocket_clients:
                debate_manager.websocket_clients.remove(websocket)
    
    except Exception as e:
        logger.error(f"Erreur WebSocket: {str(e)}")
        connected_clients.remove(websocket)

@app.get("/api/debates")
async def get_active_debates():
    """Liste des débats actifs"""
    
    debates = []
    for debate_id, debate_manager in active_debates.items():
        debates.append({
            "id": debate_id,
            "current_round": debate_manager.current_round,
            "max_rounds": debate_manager.max_rounds,
            "phase": debate_manager.current_phase.value,
            "participants": len(debate_manager.participants),
            "messages_count": len(debate_manager.messages),
            "created_at": debate_manager.messages[0].timestamp.isoformat() if debate_manager.messages else None
        })
    
    return {"debates": debates, "total": len(debates)}

@app.get("/api/metrics")
async def get_metrics():
    """Métriques du système"""
    
    total_messages = sum(len(d.messages) for d in active_debates.values())
    
    return {
        "active_debates": len(active_debates),
        "connected_clients": len(connected_clients),
        "total_messages": total_messages,
        "average_rounds": sum(d.current_round for d in active_debates.values()) / max(len(active_debates), 1),
        "providers_health": await orchestrator.get_providers_health(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Servir les fichiers statiques React (en production)
import os
if os.path.exists("../frontend/build/static"):
    app.mount("/static", StaticFiles(directory="../frontend/build/static"), name="static")

if __name__ == "__main__":
    # Configuration de développement
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )