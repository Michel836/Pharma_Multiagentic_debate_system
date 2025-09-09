// DebateMessage.js - Composant pour afficher un message de débat
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Avatar,
  IconButton,
  Collapse,
  Divider,
  LinearProgress,
  Tooltip,
  Grid
} from '@mui/material';
import {
  ExpandMoreOutlined as ExpandIcon,
  ExpandLessOutlined as CollapseIcon,
  ThumbUpOutlined as ThumbUpIcon,
  ThumbDownOutlined as ThumbDownIcon,
  InfoOutlined as InfoIcon,
  AccessTimeOutlined as TimeIcon,
  PsychologyOutlined as ConfidenceIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

const DebateMessage = ({ message, agentInfo, showVotes = false }) => {
  const [expanded, setExpanded] = useState(false);
  const [showMetadata, setShowMetadata] = useState(false);

  const {
    content,
    timestamp,
    confidence,
    metadata = {},
    votes = [],
    role
  } = message;

  const getMessageStyle = () => {
    const baseStyle = {
      mb: 2,
      transition: 'all 0.3s ease',
      '&:hover': {
        transform: 'translateY(-2px)',
        boxShadow: 3
      }
    };

    // Couleurs selon le rôle
    switch (role) {
      case 'expert':
        return {
          ...baseStyle,
          borderLeft: `4px solid ${agentInfo.color}`,
          backgroundColor: 'background.paper'
        };
      case 'judge':
        return {
          ...baseStyle,
          borderLeft: '4px solid #9b59b6',
          backgroundColor: '#f8f4ff'
        };
      case 'system':
        return {
          ...baseStyle,
          borderLeft: '4px solid #95a5a6',
          backgroundColor: '#f8f9fa',
          opacity: 0.9
        };
      default:
        return baseStyle;
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'success';
    if (confidence >= 0.6) return 'warning';
    return 'error';
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return formatDistanceToNow(date, { 
        addSuffix: true, 
        locale: fr 
      });
    } catch (error) {
      return 'Date inconnue';
    }
  };

  const renderMessageContent = () => {
    // Messages système en simple texte
    if (role === 'system') {
      return (
        <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
          {content}
        </Typography>
      );
    }

    // Messages d'agents avec markdown
    return (
      <Box>
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <Typography variant="body1" paragraph sx={{ mb: 1 }}>
                {children}
              </Typography>
            ),
            strong: ({ children }) => (
              <Typography component="strong" sx={{ fontWeight: 600 }}>
                {children}
              </Typography>
            ),
            em: ({ children }) => (
              <Typography component="em" sx={{ fontStyle: 'italic' }}>
                {children}
              </Typography>
            ),
            ul: ({ children }) => (
              <Box component="ul" sx={{ pl: 2, my: 1 }}>
                {children}
              </Box>
            ),
            li: ({ children }) => (
              <Typography component="li" variant="body2">
                {children}
              </Typography>
            )
          }}
        >
          {content}
        </ReactMarkdown>
      </Box>
    );
  };

  const renderVotes = () => {
    if (!showVotes || votes.length === 0) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Divider sx={{ mb: 1 }} />
        <Typography variant="caption" color="textSecondary" gutterBottom>
          Votes reçus:
        </Typography>
        <Box display="flex" gap={1} flexWrap="wrap">
          {votes.map((vote, index) => (
            <Chip
              key={index}
              label={`${vote.voter}: ${vote.score.toFixed(1)}`}
              size="small"
              variant="outlined"
              color={vote.score > 0.7 ? 'success' : vote.score > 0.4 ? 'warning' : 'error'}
            />
          ))}
        </Box>
      </Box>
    );
  };

  const renderMetadata = () => {
    if (!showMetadata || !metadata || Object.keys(metadata).length === 0) {
      return null;
    }

    return (
      <Collapse in={showMetadata}>
        <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            📋 Métadonnées techniques
          </Typography>
          <Grid container spacing={2}>
            {metadata.model && (
              <Grid item xs={6}>
                <Typography variant="caption" color="textSecondary">
                  Modèle: {metadata.model}
                </Typography>
              </Grid>
            )}
            {metadata.temperature !== undefined && (
              <Grid item xs={6}>
                <Typography variant="caption" color="textSecondary">
                  Température: {metadata.temperature}
                </Typography>
              </Grid>
            )}
            {metadata.duration_ms && (
              <Grid item xs={6}>
                <Typography variant="caption" color="textSecondary">
                  Durée: {metadata.duration_ms.toFixed(0)}ms
                </Typography>
              </Grid>
            )}
            {metadata.tokens_used && (
              <Grid item xs={6}>
                <Typography variant="caption" color="textSecondary">
                  Tokens: {metadata.tokens_used}
                </Typography>
              </Grid>
            )}
          </Grid>
        </Box>
      </Collapse>
    );
  };

  return (
    <Card sx={getMessageStyle()} elevation={1}>
      <CardContent sx={{ pb: '16px !important' }}>
        {/* Header du message */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <Avatar 
              sx={{ 
                width: 32, 
                height: 32, 
                bgcolor: agentInfo.color,
                fontSize: '0.875rem'
              }}
            >
              {agentInfo.name.charAt(0)}
            </Avatar>
            
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {agentInfo.name}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                <TimeIcon sx={{ fontSize: 12, mr: 0.5 }} />
                {formatTimestamp(timestamp)}
              </Typography>
            </Box>
          </Box>

          <Box display="flex" alignItems="center" gap={1}>
            {/* Score de confiance */}
            {confidence > 0 && role === 'expert' && (
              <Tooltip title={`Niveau de confiance: ${(confidence * 100).toFixed(0)}%`}>
                <Box display="flex" alignItems="center" gap={0.5}>
                  <ConfidenceIcon 
                    sx={{ 
                      fontSize: 16, 
                      color: `${getConfidenceColor(confidence)}.main` 
                    }} 
                  />
                  <LinearProgress
                    variant="determinate"
                    value={confidence * 100}
                    color={getConfidenceColor(confidence)}
                    sx={{ width: 40, height: 4 }}
                  />
                </Box>
              </Tooltip>
            )}

            {/* Bouton métadonnées */}
            {metadata && Object.keys(metadata).length > 0 && (
              <Tooltip title="Métadonnées techniques">
                <IconButton 
                  size="small" 
                  onClick={() => setShowMetadata(!showMetadata)}
                  color={showMetadata ? 'primary' : 'default'}
                >
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Contenu du message */}
        <Box sx={{ mt: 1 }}>
          {renderMessageContent()}
        </Box>

        {/* Votes */}
        {renderVotes()}

        {/* Métadonnées */}
        {renderMetadata()}

        {/* Actions pour messages longs */}
        {content.length > 500 && (
          <Box sx={{ mt: 1, textAlign: 'center' }}>
            <IconButton 
              size="small" 
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <CollapseIcon /> : <ExpandIcon />}
            </IconButton>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default DebateMessage;