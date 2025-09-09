// DebateChat.js - Interface principale du débat visible
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  Avatar,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  Badge
} from '@mui/material';
import {
  StopCircleOutlined as StopIcon,
  PlayCircleOutlineOutlined as PlayIcon,
  PauseCircleOutlineOutlined as PauseIcon,
  AssessmentOutlined as MetricsIcon,
  GavelOutlined as JudgeIcon,
  SmartToyOutlined as AgentIcon,
  NotificationImportantOutlined as AlertIcon
} from '@mui/icons-material';

import VotingPanel from './VotingPanel';
import HumanValidation from './HumanValidation';
import PipelineViewer from './PipelineViewer';
import DebateMessage from './DebateMessage';

const DebateChat = ({ debateId, websocket, onStopDebate, onNotification }) => {
  const [messages, setMessages] = useState([]);
  const [debatePhase, setDebatePhase] = useState('initialization');
  const [currentRound, setCurrentRound] = useState(0);
  const [maxRounds, setMaxRounds] = useState(5);
  const [participants, setParticipants] = useState({});
  const [isVoting, setIsVoting] = useState(false);
  const [validationRequired, setValidationRequired] = useState(false);
  const [validationData, setValidationData] = useState(null);
  const [consensusLevel, setConsensusLevel] = useState(0);
  const [isRunning, setIsRunning] = useState(true);
  const [metrics, setMetrics] = useState({});
  const [showMetrics, setShowMetrics] = useState(false);

  const messagesEndRef = useRef(null);
  const debateContainerRef = useRef(null);

  useEffect(() => {
    if (!websocket) return;

    // Écouter les messages WebSocket
    websocket.on('message', handleIncomingMessage);
    websocket.on('debate_update', handleDebateUpdate);
    websocket.on('voting_required', handleVotingRequired);
    websocket.on('validation_required', handleValidationRequired);

    // Se joindre au débat
    websocket.send({
      type: 'join_debate',
      debate_id: debateId
    });

    return () => {
      websocket.off('message');
      websocket.off('debate_update');
      websocket.off('voting_required');
      websocket.off('validation_required');
    };
  }, [websocket, debateId]);

  useEffect(() => {
    // Auto-scroll vers le bas
    messagesEndRef.current?.scrollIntoView({ 
      behavior: 'smooth',
      block: 'nearest'
    });
  }, [messages]);

  const handleIncomingMessage = (msg) => {
    console.log('Message reçu:', msg);
    
    const newMessage = {
      id: msg.id,
      timestamp: msg.timestamp,
      agent: msg.agent_id,
      role: msg.role,
      content: msg.content,
      metadata: msg.metadata || {},
      confidence: msg.confidence_score || 0,
      votes: msg.votes_received || []
    };

    setMessages(prev => [...prev, newMessage]);

    // Mise à jour du compteur de tours
    if (msg.metadata?.round) {
      setCurrentRound(msg.metadata.round);
    }

    // Détection des changements de phase
    if (msg.metadata?.phase) {
      setDebatePhase(msg.metadata.phase);
    }
  };

  const handleDebateUpdate = (update) => {
    console.log('Mise à jour débat:', update);
    
    if (update.phase) setDebatePhase(update.phase);
    if (update.consensus_level !== undefined) setConsensusLevel(update.consensus_level);
    if (update.round) setCurrentRound(update.round);
    if (update.participants) setParticipants(update.participants);
    if (update.metrics) setMetrics(update.metrics);
  };

  const handleVotingRequired = (data) => {
    console.log('Vote requis:', data);
    setIsVoting(true);
    onNotification('🗳️ Phase de vote démarrée', 'info');
  };

  const handleValidationRequired = (data) => {
    console.log('Validation requise:', data);
    setValidationRequired(true);
    setValidationData(data);
    onNotification('👤 Validation humaine requise', 'warning');
  };

  const handleKillSwitch = async () => {
    try {
      const response = await fetch('/api/kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ debate_id: debateId })
      });

      if (response.ok) {
        onNotification('🛑 Kill Switch activé', 'error');
        setIsRunning(false);
      }
    } catch (error) {
      onNotification(`Erreur Kill Switch: ${error.message}`, 'error');
    }
  };

  const conductNextRound = async () => {
    try {
      const response = await fetch(`/api/debate/${debateId}/round`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: "Continue debate",
          context: { debate_id: debateId }
        })
      });

      const data = await response.json();
      console.log('Résultat tour:', data);

      if (data.requires_human_validation) {
        handleValidationRequired(data.validation_data);
      }
    } catch (error) {
      onNotification(`Erreur tour: ${error.message}`, 'error');
    }
  };

  const handleHumanValidation = async (decision, notes = '') => {
    try {
      await websocket.send({
        type: 'human_validation',
        validation_id: validationData?.id,
        decision: decision,
        notes: notes,
        timestamp: new Date().toISOString()
      });

      setValidationRequired(false);
      setValidationData(null);
      
      onNotification(`✅ Validation: ${decision}`, 'success');
    } catch (error) {
      onNotification(`Erreur validation: ${error.message}`, 'error');
    }
  };

  const getPhaseColor = (phase) => {
    const colors = {
      'initialization': 'default',
      'opening_statements': 'primary',
      'argumentation': 'secondary',
      'voting': 'warning',
      'human_validation': 'error',
      'synthesis': 'success',
      'completed': 'success'
    };
    return colors[phase] || 'default';
  };

  const getPhaseLabel = (phase) => {
    const labels = {
      'initialization': '🚀 Initialisation',
      'opening_statements': '📋 Déclarations',
      'argumentation': '💬 Argumentation', 
      'voting': '🗳️ Vote',
      'human_validation': '👤 Validation',
      'synthesis': '📊 Synthèse',
      'completed': '✅ Terminé'
    };
    return labels[phase] || phase;
  };

  const getAgentInfo = (agentId) => {
    const agents = {
      'expert_1': { name: '🤖 Expert Gemini', color: '#4285f4' },
      'expert_2': { name: '🦙 Expert Llama', color: '#00a67e' },
      'expert_3': { name: '🌊 Expert Mistral', color: '#ff6b6b' },
      'judge': { name: '⚖️ Juge IA', color: '#9b59b6' },
      'system': { name: '📋 Système', color: '#95a5a6' }
    };
    return agents[agentId] || { name: agentId, color: '#333' };
  };

  return (
    <Box sx={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Header du débat */}
      <Paper elevation={2} sx={{ p: 2, mb: 2 }}>
        <Grid container alignItems="center" spacing={2}>
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center" gap={2}>
              <Chip 
                label={getPhaseLabel(debatePhase)} 
                color={getPhaseColor(debatePhase)}
                variant="filled"
                size="medium"
              />
              <Typography variant="body2" color="textSecondary">
                Tour {currentRound}/{maxRounds}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box>
              <Typography variant="body2" gutterBottom>
                Consensus: {(consensusLevel * 100).toFixed(0)}%
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={consensusLevel * 100}
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'rgba(0,0,0,0.1)',
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(90deg, #f44336 0%, #ff9800 50%, #4caf50 100%)`
                  }
                }}
              />
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box display="flex" gap={1} justifyContent="flex-end">
              <Tooltip title="Métriques du débat">
                <IconButton 
                  onClick={() => setShowMetrics(true)}
                  color="primary"
                >
                  <Badge badgeContent={Object.keys(metrics).length} color="secondary">
                    <MetricsIcon />
                  </Badge>
                </IconButton>
              </Tooltip>
              
              {isRunning && debatePhase !== 'completed' && (
                <Tooltip title="Tour suivant">
                  <IconButton 
                    onClick={conductNextRound}
                    color="primary"
                    disabled={validationRequired}
                  >
                    <PlayIcon />
                  </IconButton>
                </Tooltip>
              )}

              <Tooltip title="🛑 KILL SWITCH">
                <IconButton 
                  onClick={handleKillSwitch}
                  color="error"
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: 'error.main',
                      color: 'white'
                    }
                  }}
                >
                  <StopIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Messages du débat */}
      <Paper 
        elevation={1} 
        sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          backgroundColor: '#f8f9fa'
        }}
        ref={debateContainerRef}
      >
        {messages.length === 0 ? (
          <Box 
            display="flex" 
            justifyContent="center" 
            alignItems="center" 
            height="100%"
            flexDirection="column"
          >
            <AgentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="textSecondary">
              En attente des premiers messages...
            </Typography>
          </Box>
        ) : (
          <Box>
            {messages.map((message, index) => (
              <DebateMessage
                key={message.id || index}
                message={message}
                agentInfo={getAgentInfo(message.agent)}
                showVotes={isVoting}
              />
            ))}
            <div ref={messagesEndRef} />
          </Box>
        )}
      </Paper>

      {/* Panel de vote */}
      {isVoting && (
        <Paper elevation={3} sx={{ mt: 2, p: 2 }}>
          <VotingPanel
            messages={messages.filter(m => m.role === 'expert')}
            onVoteComplete={() => {
              setIsVoting(false);
              onNotification('✅ Vote terminé', 'success');
            }}
          />
        </Paper>
      )}

      {/* Validation humaine */}
      {validationRequired && validationData && (
        <HumanValidation
          validationData={validationData}
          debateState={{
            messages,
            currentRound,
            consensusLevel,
            phase: debatePhase
          }}
          onValidate={handleHumanValidation}
          onCancel={() => {
            setValidationRequired(false);
            setValidationData(null);
          }}
        />
      )}

      {/* Dialog métriques */}
      <Dialog 
        open={showMetrics} 
        onClose={() => setShowMetrics(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>📊 Métriques du Débat</DialogTitle>
        <DialogContent>
          <PipelineViewer 
            debateId={debateId}
            metrics={metrics}
            messages={messages}
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default DebateChat;