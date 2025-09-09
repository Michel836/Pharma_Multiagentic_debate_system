# main_ollama.py - Version simplifiée pour Ollama uniquement
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Dict, List
import json
from datetime import datetime
import logging
import sys
import os

# Ajouter le chemin parent pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.ollama_orchestrator import OllamaOnlyOrchestrator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application FastAPI
app = FastAPI(
    title="Pharma MultiAgent Ollama - 100% Local",
    description="Système de débat multiagent utilisant uniquement Ollama en local",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permettre toutes les origines en dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gestionnaires globaux
orchestrator = OllamaOnlyOrchestrator()
active_debates = {}
connected_clients: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    logger.info("🚀 Démarrage du système multiagent Ollama...")
    
    try:
        await orchestrator.initialize()
        status = await orchestrator.get_status()
        logger.info(f"✅ Système initialisé avec {status['agents_count']} agents")
        logger.info(f"📋 Modèles disponibles: {status.get('available_models', [])}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation: {e}")
        logger.info("💡 Assurez-vous qu'Ollama est démarré: 'ollama serve'")

@app.get("/")
async def root():
    """Page d'accueil"""
    return {
        "message": "Système MultiAgent Ollama - 100% Local",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "start_debate": "/api/start-debate",
            "websocket": "/ws"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état du système"""
    status = await orchestrator.get_status()
    
    return {
        "status": "healthy" if status['ollama_connected'] else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "providers_status": {
            "ollama": {
                "connected": status['ollama_connected'],
                "host": status['ollama_host'],
                "models": status.get('available_models', [])
            }
        },
        "agents": status['agents'],
        "active_debates": len(active_debates),
        "connected_clients": len(connected_clients)
    }

@app.post("/api/start-debate")
async def start_debate(request: Dict):
    """Démarre un nouveau débat"""
    try:
        query = request.get("query", "")
        max_rounds = request.get("max_rounds", 3)
        
        if not query:
            return {"error": "Query is required"}, 400
        
        # Générer un ID unique pour le débat
        debate_id = f"debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Créer une tâche asynchrone pour le débat
        async def run_debate():
            try:
                result = await orchestrator.run_full_debate(query, max_rounds)
                active_debates[debate_id]['result'] = result
                active_debates[debate_id]['status'] = 'completed'
                
                # Notifier les clients WebSocket
                await notify_clients({
                    "type": "debate_completed",
                    "debate_id": debate_id,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Erreur dans le débat {debate_id}: {e}")
                active_debates[debate_id]['status'] = 'error'
                active_debates[debate_id]['error'] = str(e)
        
        # Stocker le débat et lancer la tâche
        active_debates[debate_id] = {
            "id": debate_id,
            "query": query,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "max_rounds": max_rounds
        }
        
        asyncio.create_task(run_debate())
        
        logger.info(f"Débat démarré: {debate_id} - '{query[:50]}...'")
        
        return {
            "debate_id": debate_id,
            "status": "started",
            "query": query,
            "max_rounds": max_rounds,
            "message": "Débat démarré avec Ollama"
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du démarrage du débat: {e}")
        return {"error": str(e)}, 500

@app.post("/api/debate/{debate_id}/round")
async def conduct_round(debate_id: str, context: Dict = None):
    """Lance un tour de débat spécifique"""
    
    if debate_id not in active_debates:
        return {"error": "Débat non trouvé"}, 404
    
    try:
        query = context.get("query", active_debates[debate_id]["query"])
        round_number = context.get("round", 1)
        
        result = await orchestrator.conduct_debate_round(query, round_number)
        
        # Notifier les clients WebSocket
        await notify_clients({
            "type": "round_completed",
            "debate_id": debate_id,
            "round": round_number,
            "result": result
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur tour de débat {debate_id}: {e}")
        return {"error": str(e)}, 500

@app.get("/api/debates")
async def get_active_debates():
    """Liste des débats actifs"""
    debates = []
    for debate_id, debate_info in active_debates.items():
        debates.append({
            "id": debate_id,
            "query": debate_info["query"],
            "status": debate_info["status"],
            "start_time": debate_info["start_time"],
            "max_rounds": debate_info.get("max_rounds", 3)
        })
    
    return {"debates": debates, "total": len(debates)}

@app.get("/api/debate/{debate_id}")
async def get_debate_result(debate_id: str):
    """Récupère le résultat d'un débat"""
    
    if debate_id not in active_debates:
        return {"error": "Débat non trouvé"}, 404
    
    debate = active_debates[debate_id]
    
    return {
        "id": debate_id,
        "status": debate["status"],
        "query": debate["query"],
        "result": debate.get("result"),
        "error": debate.get("error")
    }

@app.post("/api/kill-switch")
async def trigger_kill_switch():
    """Active le kill switch d'urgence"""
    try:
        # Arrêter tous les débats actifs
        for debate_id in list(active_debates.keys()):
            active_debates[debate_id]['status'] = 'stopped'
        
        # Notifier tous les clients
        await notify_clients({
            "type": "kill_switch_activated",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Tous les débats ont été arrêtés"
        })
        
        logger.warning("🛑 Kill switch activé - Tous les débats arrêtés")
        
        return {"status": "activated", "debates_stopped": len(active_debates)}
        
    except Exception as e:
        logger.error(f"Erreur kill switch: {e}")
        return {"error": str(e)}, 500

async def notify_clients(message: Dict):
    """Notifie tous les clients WebSocket connectés"""
    disconnected_clients = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected_clients.append(client)
    
    # Nettoyer les clients déconnectés
    for client in disconnected_clients:
        if client in connected_clients:
            connected_clients.remove(client)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour communication temps réel"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    logger.info(f"Client WebSocket connecté. Total: {len(connected_clients)}")
    
    # Envoyer le statut initial
    status = await orchestrator.get_status()
    await websocket.send_json({
        "type": "connection_established",
        "status": status,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            # Recevoir les messages du client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Traiter selon le type de message
            if message.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message.get("type") == "get_status":
                status = await orchestrator.get_status()
                await websocket.send_json({
                    "type": "status_update",
                    "status": status
                })
            
            elif message.get("type") == "start_debate":
                # Démarrer un débat via WebSocket
                result = await start_debate(message.get("data", {}))
                await websocket.send_json({
                    "type": "debate_started",
                    "result": result
                })
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Client WebSocket déconnecté. Total: {len(connected_clients)}")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/api/metrics")
async def get_metrics():
    """Métriques du système"""
    status = await orchestrator.get_status()
    
    return {
        "active_debates": len(active_debates),
        "connected_clients": len(connected_clients),
        "ollama_connected": status['ollama_connected'],
        "agents_count": status['agents_count'],
        "models_available": len(status.get('available_models', [])),
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    # Configuration pour le développement
    print("\n" + "="*50)
    print("  SYSTEME MULTIAGENT OLLAMA - 100% LOCAL")
    print("="*50)
    print("\n✅ Backend démarré sur http://localhost:8000")
    print("📖 Documentation API: http://localhost:8000/docs")
    print("\n⚠️  Assurez-vous qu'Ollama est démarré!")
    print("💡 Commande: ollama serve")
    print("\n" + "="*50 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )