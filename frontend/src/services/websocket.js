// WebSocket Service - Gestion des connexions temps réel
export class WebSocketService {
  constructor(url) {
    this.url = url;
    this.socket = null;
    this.listeners = {};
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.isConnecting = false;
    
    this.connect();
  }

  connect() {
    if (this.isConnecting || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
      return;
    }

    this.isConnecting = true;
    
    try {
      this.socket = new WebSocket(this.url);
      
      this.socket.onopen = (event) => {
        console.log('WebSocket connected:', this.url);
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.emit('connect', event);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          // Émets l'événement avec le type de message comme nom d'événement
          if (data.type) {
            this.emit(data.type, data);
          }
          
          // Émets aussi un événement générique 'message'
          this.emit('message', data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          this.emit('error', { message: 'Failed to parse message', error });
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.emit('disconnect', event);
        
        // Tentative de reconnexion automatique
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          
          setTimeout(() => {
            this.connect();
          }, this.reconnectDelay * this.reconnectAttempts);
        } else {
          console.error('Max reconnection attempts reached');
          this.emit('max_reconnect_attempts', { attempts: this.reconnectAttempts });
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        this.emit('error', { message: 'WebSocket error', error });
      };
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
      this.emit('error', { message: 'Failed to connect', error });
    }
  }

  // Ajoute un écouteur d'événements
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  // Supprime un écouteur d'événements
  off(event, callback) {
    if (!this.listeners[event]) return;
    
    const index = this.listeners[event].indexOf(callback);
    if (index > -1) {
      this.listeners[event].splice(index, 1);
    }
  }

  // Émet un événement vers tous les écouteurs
  emit(event, data) {
    if (!this.listeners[event]) return;
    
    this.listeners[event].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error('Error in event listener:', error);
      }
    });
  }

  // Envoie un message via WebSocket
  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      try {
        const message = typeof data === 'string' ? data : JSON.stringify(data);
        this.socket.send(message);
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        this.emit('error', { message: 'Failed to send message', error });
        return false;
      }
    } else {
      console.warn('WebSocket not connected, cannot send message');
      this.emit('error', { message: 'WebSocket not connected' });
      return false;
    }
  }

  // Ferme la connexion WebSocket
  disconnect() {
    this.reconnectAttempts = this.maxReconnectAttempts; // Empêche la reconnexion automatique
    
    if (this.socket) {
      this.socket.close(1000, 'Client disconnect');
      this.socket = null;
    }
    
    // Nettoie tous les écouteurs
    this.listeners = {};
  }

  // Vérifie l'état de la connexion
  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }

  // Obtient l'état de la connexion
  getReadyState() {
    if (!this.socket) return 'CLOSED';
    
    switch (this.socket.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }

  // Force une reconnexion
  reconnect() {
    this.disconnect();
    this.reconnectAttempts = 0;
    setTimeout(() => {
      this.connect();
    }, 1000);
  }
}

export default WebSocketService;