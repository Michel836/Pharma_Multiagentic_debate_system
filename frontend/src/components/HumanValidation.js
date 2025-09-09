// HumanValidation.js - Interface de validation humaine obligatoire
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  Divider,
  Alert,
  Grid,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  CheckCircleOutlined as ApproveIcon,
  CancelOutlined as RejectIcon,
  HelpOutlineOutlined as ClarificationIcon,
  RefreshOutlined as MoreDebateIcon,
  EditOutlined as OverrideIcon,
  WarningOutlined as WarningIcon,
  InfoOutlined as InfoIcon,
  ExpandMoreOutlined as ExpandIcon,
  PsychologyOutlined as ConsensusIcon,
  GroupOutlined as ParticipantsIcon,
  MessageOutlined as MessagesIcon
} from '@mui/icons-material';

const HumanValidation = ({ 
  validationData, 
  debateState, 
  onValidate, 
  onCancel 
}) => {
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [showDetails, setShowDetails] = useState(false);

  const {
    debate_id,
    current_round,
    consensus_score,
    voting_results,
    key_arguments,
    risk_assessment
  } = validationData;

  const {
    messages,
    currentRound,
    consensusLevel,
    phase
  } = debateState;

  const handleValidate = () => {
    if (!decision) return;
    
    onValidate(decision, notes);
  };

  const getDecisionIcon = (decisionType) => {
    switch (decisionType) {
      case 'approve':
        return <ApproveIcon color="success" />;
      case 'reject':
        return <RejectIcon color="error" />;
      case 'clarification':
        return <ClarificationIcon color="info" />;
      case 'more_debate':
        return <MoreDebateIcon color="warning" />;
      case 'override':
        return <OverrideIcon color="primary" />;
      default:
        return <InfoIcon />;
    }
  };

  const getDecisionColor = (decisionType) => {
    switch (decisionType) {
      case 'approve':
        return 'success';
      case 'reject':
        return 'error';
      case 'clarification':
        return 'info';
      case 'more_debate':
        return 'warning';
      case 'override':
        return 'primary';
      default:
        return 'default';
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'LOW':
        return 'success';
      case 'MEDIUM':
        return 'warning';
      case 'HIGH':
        return 'error';
      case 'CRITICAL':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatArguments = (arguments_list) => {
    if (!arguments_list || arguments_list.length === 0) {
      return 'Aucun argument clé identifié';
    }

    return arguments_list.map((arg, index) => (
      <Card key={index} variant="outlined" sx={{ mb: 1 }}>
        <CardContent sx={{ py: 1 }}>
          <Box display="flex" alignItems="center" gap={1} mb={1}>
            <Chip 
              label={arg.agent} 
              size="small" 
              color="primary" 
              variant="outlined"
            />
            <Chip 
              label={`${(arg.confidence * 100).toFixed(0)}% confiance`}
              size="small"
              color={arg.confidence > 0.7 ? 'success' : 'warning'}
            />
          </Box>
          <Typography variant="body2">
            {arg.content}
          </Typography>
        </CardContent>
      </Card>
    ));
  };

  return (
    <Dialog
      open={true}
      onClose={onCancel}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          minHeight: '60vh',
          maxHeight: '90vh'
        }
      }}
    >
      <DialogTitle sx={{ 
        bgcolor: 'warning.light', 
        color: 'warning.contrastText',
        display: 'flex',
        alignItems: 'center',
        gap: 1
      }}>
        <WarningIcon />
        👤 Validation Humaine Requise
      </DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        {/* Alerte importante */}
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>⚠️ Validation obligatoire :</strong> Cette décision nécessite une intervention humaine 
            dans le cadre pharmaceutique. Veuillez examiner attentivement les arguments et prendre une décision éclairée.
          </Typography>
        </Alert>

        {/* Résumé du débat */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom color="primary">
              📊 Résumé du Débat
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="primary">
                    {current_round}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Tours complétés
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="secondary">
                    {messages.filter(m => m.role === 'expert').length}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Messages d'experts
                  </Typography>
                </Box>
              </Grid>
              
              <Grid item xs={4}>
                <Box textAlign="center">
                  <Typography variant="h4" color="success.main">
                    {(consensusLevel * 100).toFixed(0)}%
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Niveau consensus
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Progression du consensus
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={consensusLevel * 100}
                sx={{ 
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    background: `linear-gradient(90deg, #f44336 0%, #ff9800 50%, #4caf50 100%)`
                  }
                }}
              />
            </Box>
          </CardContent>
        </Card>

        {/* Évaluation des risques */}
        {risk_assessment && (
          <Card variant="outlined" sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                <WarningIcon color="warning" />
                <Typography variant="h6" color="warning.main">
                  Évaluation des Risques
                </Typography>
                <Chip 
                  label={risk_assessment.risk_level}
                  color={getRiskLevelColor(risk_assessment.risk_level)}
                  size="small"
                />
              </Box>

              <LinearProgress 
                variant="determinate" 
                value={risk_assessment.risk_score * 100}
                color={getRiskLevelColor(risk_assessment.risk_level)}
                sx={{ mb: 2, height: 6, borderRadius: 3 }}
              />

              {risk_assessment.risk_factors && risk_assessment.risk_factors.length > 0 && (
                <Box>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Facteurs de risque identifiés :
                  </Typography>
                  <List dense>
                    {risk_assessment.risk_factors.map((factor, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <WarningIcon color="warning" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText primary={factor} />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        {/* Arguments clés */}
        <Accordion expanded={showDetails} onChange={(e, expanded) => setShowDetails(expanded)}>
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Typography variant="h6">
              🔍 Arguments Clés du Débat
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {key_arguments && key_arguments.length > 0 ? (
              formatArguments(key_arguments)
            ) : (
              <Typography variant="body2" color="textSecondary">
                Aucun argument clé disponible pour cette validation
              </Typography>
            )}
          </AccordionDetails>
        </Accordion>

        <Divider sx={{ my: 3 }} />

        {/* Options de décision */}
        <Typography variant="h6" gutterBottom color="primary">
          🎯 Votre Décision
        </Typography>

        <RadioGroup
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
        >
          <FormControlLabel
            value="approve"
            control={<Radio />}
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <ApproveIcon color="success" />
                <Box>
                  <Typography variant="body1">
                    <strong>Approuver</strong>
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Le consensus est satisfaisant, procéder à la synthèse
                  </Typography>
                </Box>
              </Box>
            }
          />

          <FormControlLabel
            value="more_debate"
            control={<Radio />}
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <MoreDebateIcon color="warning" />
                <Box>
                  <Typography variant="body1">
                    <strong>Demander plus de débat</strong>
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Les arguments ne sont pas suffisamment développés
                  </Typography>
                </Box>
              </Box>
            }
          />

          <FormControlLabel
            value="clarification"
            control={<Radio />}
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <ClarificationIcon color="info" />
                <Box>
                  <Typography variant="body1">
                    <strong>Demander des clarifications</strong>
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Certains points nécessitent des précisions
                  </Typography>
                </Box>
              </Box>
            }
          />

          <FormControlLabel
            value="reject"
            control={<Radio />}
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <RejectIcon color="error" />
                <Box>
                  <Typography variant="body1">
                    <strong>Rejeter</strong>
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Le débat présente des problèmes fondamentaux
                  </Typography>
                </Box>
              </Box>
            }
          />

          <FormControlLabel
            value="override"
            control={<Radio />}
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <OverrideIcon color="primary" />
                <Box>
                  <Typography variant="body1">
                    <strong>Validation avec override</strong>
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Approuver malgré les réserves avec justification
                  </Typography>
                </Box>
              </Box>
            }
          />
        </RadioGroup>

        {/* Zone de commentaires */}
        <TextField
          fullWidth
          multiline
          rows={3}
          label="Notes et justifications (obligatoire)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          sx={{ mt: 3 }}
          placeholder="Veuillez justifier votre décision pour la traçabilité..."
          required
        />
      </DialogContent>

      <DialogActions sx={{ p: 3, bgcolor: 'grey.50' }}>
        <Button
          onClick={onCancel}
          color="inherit"
          variant="outlined"
        >
          Annuler
        </Button>
        
        <Button
          onClick={handleValidate}
          color={getDecisionColor(decision)}
          variant="contained"
          disabled={!decision || !notes.trim()}
          startIcon={getDecisionIcon(decision)}
          sx={{ ml: 2 }}
        >
          Valider la décision
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default HumanValidation;