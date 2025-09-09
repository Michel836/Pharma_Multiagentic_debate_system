import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  StepConnector,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  Collapse,
  IconButton
} from '@mui/material';
import { styled } from '@mui/material/styles';
import {
  Search,
  FactCheck,
  Psychology,
  Share,
  CheckCircle,
  Error,
  HourglassEmpty,
  ExpandMore,
  ExpandLess,
  AutoAwesome,
  Storage,
  Group
} from '@mui/icons-material';

// Connecteur personnalisé pour le Stepper
const CustomConnector = styled(StepConnector)(({ theme }) => ({
  '& .MuiStepConnector-line': {
    borderColor: theme.palette.mode === 'dark' ? theme.palette.grey[800] : '#eaeaf0',
    borderLeftWidth: 3,
    minHeight: 40,
  },
  '&.Mui-active .MuiStepConnector-line': {
    borderColor: theme.palette.primary.main,
  },
  '&.Mui-completed .MuiStepConnector-line': {
    borderColor: theme.palette.success.main,
  },
}));

const PipelineViewer = ({ 
  currentPhase, 
  pipelineStatus, 
  ragSources,
  extractedData,
  validationResults,
  synthesisOutput 
}) => {
  const [expanded, setExpanded] = React.useState(true);
  const [expandedSteps, setExpandedSteps] = React.useState({});

  // Définition des étapes du pipeline
  const pipelineSteps = [
    {
      label: 'Extraction',
      icon: <Search />,
      description: 'Recherche et extraction des données depuis les sources RAG',
      status: pipelineStatus?.extraction || 'pending',
      details: extractedData
    },
    {
      label: 'Validation',
      icon: <FactCheck />,
      description: 'Validation croisée par les agents experts',
      status: pipelineStatus?.validation || 'pending',
      details: validationResults
    },
    {
      label: 'Synthèse',
      icon: <Psychology />,
      description: 'Synthèse et structuration des résultats validés',
      status: pipelineStatus?.synthesis || 'pending',
      details: synthesisOutput
    },
    {
      label: 'Partage',
      icon: <Share />,
      description: 'Distribution des résultats et recommandations',
      status: pipelineStatus?.sharing || 'pending',
      details: null
    }
  ];

  const getStepIcon = (step, index) => {
    const isActive = currentPhase === step.label.toLowerCase();
    const isCompleted = step.status === 'completed';
    const isFailed = step.status === 'failed';
    
    if (isFailed) {
      return (
        <Box sx={{ 
          bgcolor: 'error.main', 
          borderRadius: '50%', 
          p: 1, 
          display: 'flex',
          color: 'white'
        }}>
          <Error />
        </Box>
      );
    }
    
    if (isCompleted) {
      return (
        <Box sx={{ 
          bgcolor: 'success.main', 
          borderRadius: '50%', 
          p: 1, 
          display: 'flex',
          color: 'white'
        }}>
          <CheckCircle />
        </Box>
      );
    }
    
    if (isActive) {
      return (
        <Box sx={{ position: 'relative' }}>
          <CircularProgress size={40} thickness={4} />
          <Box sx={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)',
            color: 'primary.main'
          }}>
            {step.icon}
          </Box>
        </Box>
      );
    }
    
    return (
      <Box sx={{ 
        bgcolor: 'grey.300', 
        borderRadius: '50%', 
        p: 1, 
        display: 'flex',
        color: 'grey.600'
      }}>
        {step.icon}
      </Box>
    );
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'success';
      case 'active': return 'primary';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const toggleStepExpansion = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AutoAwesome color="primary" />
          <Typography variant="h6">Pipeline de Traitement</Typography>
        </Box>
        <IconButton onClick={() => setExpanded(!expanded)} size="small">
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>

      <Collapse in={expanded}>
        {/* Sources RAG */}
        {ragSources && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Storage fontSize="small" color="primary" />
              <Typography variant="subtitle2" fontWeight="bold">
                Sources RAG Actives
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {ragSources.enterprise && (
                <Chip 
                  label="Enterprise RAG" 
                  size="small" 
                  color="primary"
                  icon={<CheckCircle />}
                />
              )}
              {ragSources.personal && (
                <Chip 
                  label="Personal RAG" 
                  size="small" 
                  color="secondary"
                  icon={<CheckCircle />}
                />
              )}
              {ragSources.contacts && (
                <Chip 
                  label="Contacts/Emails" 
                  size="small" 
                  color="info"
                  icon={<Group />}
                />
              )}
            </Box>
          </Box>
        )}

        {/* Stepper du pipeline */}
        <Stepper 
          activeStep={pipelineSteps.findIndex(s => s.label.toLowerCase() === currentPhase)}
          orientation="vertical"
          connector={<CustomConnector />}
        >
          {pipelineSteps.map((step, index) => (
            <Step key={step.label} completed={step.status === 'completed'}>
              <StepLabel
                StepIconComponent={() => getStepIcon(step, index)}
                optional={
                  <Typography variant="caption" color="text.secondary">
                    {step.description}
                  </Typography>
                }
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="subtitle1" fontWeight="bold">
                    {step.label}
                  </Typography>
                  <Chip 
                    label={step.status}
                    size="small"
                    color={getStatusColor(step.status)}
                  />
                </Box>
              </StepLabel>
              
              <StepContent>
                {/* Détails de l'étape si disponibles */}
                {step.details && (
                  <Box sx={{ mt: 1, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        Détails de l'étape
                      </Typography>
                      <IconButton 
                        size="small"
                        onClick={() => toggleStepExpansion(index)}
                      >
                        {expandedSteps[index] ? <ExpandLess /> : <ExpandMore />}
                      </IconButton>
                    </Box>
                    
                    <Collapse in={expandedSteps[index]}>
                      <Box sx={{ mt: 1 }}>
                        {typeof step.details === 'string' ? (
                          <Typography variant="body2">
                            {step.details}
                          </Typography>
                        ) : (
                          <pre style={{ 
                            fontSize: '0.85em', 
                            overflow: 'auto',
                            background: 'white',
                            padding: '8px',
                            borderRadius: '4px'
                          }}>
                            {JSON.stringify(step.details, null, 2)}
                          </pre>
                        )}
                      </Box>
                    </Collapse>
                  </Box>
                )}
                
                {/* Barre de progression pour l'étape active */}
                {step.status === 'active' && (
                  <Box sx={{ mt: 2 }}>
                    <LinearProgress />
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      Traitement en cours...
                    </Typography>
                  </Box>
                )}
                
                {/* Message d'erreur si l'étape a échoué */}
                {step.status === 'failed' && (
                  <Alert severity="error" sx={{ mt: 1 }}>
                    Cette étape a rencontré une erreur. Vérifiez les logs.
                  </Alert>
                )}
              </StepContent>
            </Step>
          ))}
        </Stepper>

        {/* Résumé global */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.light', borderRadius: 2 }}>
          <Typography variant="body2" color="primary.contrastText">
            <strong>État global:</strong> {
              pipelineStatus?.overall === 'completed' ? 'Pipeline terminé avec succès' :
              pipelineStatus?.overall === 'failed' ? 'Pipeline interrompu suite à une erreur' :
              'Pipeline en cours de traitement'
            }
          </Typography>
          {pipelineStatus?.duration && (
            <Typography variant="caption" color="primary.contrastText">
              Durée: {pipelineStatus.duration}ms
            </Typography>
          )}
        </Box>
      </Collapse>
    </Paper>
  );
};

export default PipelineViewer;