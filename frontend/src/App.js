// App.js - Application React principale
import React, { useState, useEffect } from 'react';
import { 
  ThemeProvider, 
  createTheme,
  CssBaseline,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Alert,
  Snackbar
} from '@mui/material';
import { 
  BiotechOutlined as PharmaIcon 
} from '@mui/icons-material';

import DebateChat from './components/DebateChat';
import StartDebatePanel from './components/StartDebatePanel';
import SystemStatus from './components/SystemStatus';
import { WebSocketService } from './services/websocket';

import './App.css';

// Thème pharma
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Bleu médical
      light: '#42a5f5',
      dark: '#1565c0'
    },
    secondary: {
      main: '#4caf50', // Vert validation
      light: '#81c784',
      dark: '#388e3c'
    },
    error: {
      main: '#f44336', // Rouge alerte
    },
    warning: {
      main: '#ff9800', // Orange attention
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600
    },
    h6: {
      fontWeight: 500
    }
  },
  shape: {
    borderRadius: 8
  }
});

function App() {
  const [debateActive, setDebateActive] = useState(false);
  const [debateId, setDebateId] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    healthy: false,
    providers: 0,
    loading: true
  });
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [ws, setWs] = useState(null);

  // Vérification du statut système au démarrage
  useEffect(() => {
    checkSystemHealth();
    const interval = setInterval(checkSystemHealth, 30000); // Check toutes les 30s
    return () => clearInterval(interval);
  }, []);

  // Initialisation WebSocket
  useEffect(() => {
    const websocket = new WebSocketService('ws://localhost:8000/ws');
    
    websocket.on('connect', () => {
      showNotification('Connexion WebSocket établie', 'success');
    });
    
    websocket.on('disconnect', () => {
      showNotification('Connexion WebSocket perdue', 'warning');
    });
    
    websocket.on('error', (error) => {
      showNotification(`Erreur WebSocket: ${error}`, 'error');
    });

    websocket.on('kill_switch_activated', (data) => {
      showNotification('🛑 Kill Switch activé - Tous les débats arrêtés', 'error');
      setDebateActive(false);
      setDebateId(null);
    });

    setWs(websocket);

    return () => {
      websocket.disconnect();
    };
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await fetch('/api/health');
      const data = await response.json();
      
      setSystemStatus({
        healthy: response.ok && data.status === 'healthy',
        providers: data.providers_status ? Object.keys(data.providers_status).length : 0,
        loading: false,
        details: data
      });
    } catch (error) {
      console.error('Health check failed:', error);
      setSystemStatus({
        healthy: false,
        providers: 0,
        loading: false,
        error: error.message
      });
    }
  };

  const handleStartDebate = async (config) => {
    try {
      const response = await fetch('/api/start-debate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });

      const data = await response.json();

      if (response.ok) {
        setDebateId(data.debate_id);
        setDebateActive(true);
        showNotification(`✅ Débat démarré avec ${data.participants} participants`, 'success');
      } else {
        showNotification(`❌ Erreur: ${data.error}`, 'error');
      }
    } catch (error) {
      showNotification(`❌ Erreur de connexion: ${error.message}`, 'error');
    }
  };

  const handleStopDebate = () => {
    setDebateActive(false);
    setDebateId(null);
    showNotification('Débat arrêté', 'info');
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const closeNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className="App">
        {/* Header */}
        <AppBar position="static" elevation={2}>
          <Toolbar>
            <PharmaIcon sx={{ mr: 2 }} />
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              🔬 Pharma MultiAgent - Système de Débat IA
            </Typography>
            <SystemStatus status={systemStatus} />
          </Toolbar>
        </AppBar>

        {/* Contenu principal */}
        <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
          {!systemStatus.healthy && !systemStatus.loading && (
            <Alert 
              severity="error" 
              sx={{ mb: 3 }}
              variant="filled"
            >
              ⚠️ Système non opérationnel - Vérifiez que le backend est démarré
            </Alert>
          )}

          {!debateActive ? (
            <Box>
              <Typography variant="h4" gutterBottom align="center" color="primary">
                🎭 Nouveau Débat Multiagent
              </Typography>
              <Typography variant="body1" align="center" color="textSecondary" sx={{ mb: 4 }}>
                Démarrez un débat entre IAs avec validation humaine pour éliminer les hallucinations
              </Typography>
              
              <StartDebatePanel 
                onStartDebate={handleStartDebate}
                systemReady={systemStatus.healthy}
                availableProviders={systemStatus.providers}
              />
            </Box>
          ) : (
            <DebateChat
              debateId={debateId}
              websocket={ws}
              onStopDebate={handleStopDebate}
              onNotification={showNotification}
            />
          )}
        </Container>

        {/* Notifications */}
        <Snackbar
          open={notification.open}
          autoHideDuration={6000}
          onClose={closeNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        >
          <Alert 
            onClose={closeNotification} 
            severity={notification.severity}
            variant="filled"
          >
            {notification.message}
          </Alert>
        </Snackbar>
      </div>
    </ThemeProvider>
  );
}

export default App;