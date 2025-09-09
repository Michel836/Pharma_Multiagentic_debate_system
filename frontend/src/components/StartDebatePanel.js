// StartDebatePanel.js - Panneau pour configurer et démarrer un nouveau débat
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Box,
  Grid,
  Chip,
  Alert,
  Slider,
  FormControlLabel,
  Switch,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Paper
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as StartIcon,
  Settings as SettingsIcon,
  Group as GroupIcon,
  Topic as TopicIcon,
  Timer as TimerIcon,
  Security as SecurityIcon,
  Info as InfoIcon
} from '@mui/icons-material';

const StartDebatePanel = ({ onStartDebate, systemReady, availableProviders }) => {
  const [config, setConfig] = useState({
    topic: '',
    participants: 3,
    max_rounds: 5,
    time_limit: 30,
    require_human_validation: true,
    providers: ['openai', 'anthropic', 'mistral'],
    debate_style: 'structured',
    temperature: 0.7,
    enable_fact_checking: true,
    auto_moderation: true
  });

  const [errors, setErrors] = useState({});

  // Styles de débat disponibles
  const debateStyles = [
    { value: 'structured', label: 'Structuré', description: 'Débat formel avec tours de parole' },
    { value: 'free_form', label: 'Libre', description: 'Discussion ouverte sans contraintes' },
    { value: 'adversarial', label: 'Contradictoire', description: 'Débat avec positions opposées' },
    { value: 'collaborative', label: 'Collaboratif', description: 'Recherche de consensus' }
  ];

  // Providers IA disponibles
  const availableAIProviders = [
    { value: 'openai', label: 'OpenAI GPT', color: 'primary' },
    { value: 'anthropic', label: 'Anthropic Claude', color: 'secondary' },
    { value: 'mistral', label: 'Mistral AI', color: 'info' },
    { value: 'cohere', label: 'Cohere', color: 'warning' },
    { value: 'google', label: 'Google Gemini', color: 'success' }
  ];

  const handleConfigChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error for this field
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  const handleProviderToggle = (provider) => {
    setConfig(prev => ({
      ...prev,
      providers: prev.providers.includes(provider)
        ? prev.providers.filter(p => p !== provider)
        : [...prev.providers, provider]
    }));
  };

  const validateConfig = () => {
    const newErrors = {};

    if (!config.topic.trim()) {
      newErrors.topic = 'Le sujet du débat est requis';
    } else if (config.topic.length < 10) {
      newErrors.topic = 'Le sujet doit contenir au moins 10 caractères';
    }

    if (config.participants < 2) {
      newErrors.participants = 'Au moins 2 participants sont nécessaires';
    } else if (config.participants > 10) {
      newErrors.participants = 'Maximum 10 participants autorisés';
    }

    if (config.providers.length === 0) {
      newErrors.providers = 'Au moins un provider IA doit être sélectionné';
    }

    if (config.max_rounds < 1 || config.max_rounds > 20) {
      newErrors.max_rounds = 'Nombre de tours doit être entre 1 et 20';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleStartDebate = () => {
    if (!validateConfig()) {
      return;
    }

    onStartDebate(config);
  };

  const getEstimatedDuration = () => {
    const baseTime = config.max_rounds * config.participants * 2; // 2 min par participant par tour
    const validationTime = config.require_human_validation ? config.max_rounds * 3 : 0; // 3 min validation par tour
    return baseTime + validationTime;
  };

  return (
    <Card elevation={3} sx={{ maxWidth: 800, mx: 'auto' }}>
      <CardContent>
        {/* En-tête */}
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <TopicIcon color="primary" sx={{ mr: 2 }} />
          <Typography variant="h5" component="h2">
            Configuration du Débat
          </Typography>
        </Box>

        {/* Alerte si système non prêt */}
        {!systemReady && (
          <Alert 
            severity="warning" 
            sx={{ mb: 3 }}
            icon={<SecurityIcon />}
          >
            Système non opérationnel - {availableProviders} provider(s) disponible(s)
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Sujet du débat */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Sujet du débat"
              value={config.topic}
              onChange={(e) => handleConfigChange('topic', e.target.value)}
              error={!!errors.topic}
              helperText={errors.topic || 'Décrivez le sujet que les IAs vont débattre'}
              multiline
              rows={3}
              placeholder="Ex: Les avantages et inconvénients de l'intelligence artificielle dans le diagnostic médical..."
            />
          </Grid>

          {/* Configuration de base */}
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth error={!!errors.participants}>
              <InputLabel>Nombre de participants</InputLabel>
              <Select
                value={config.participants}
                label="Nombre de participants"
                onChange={(e) => handleConfigChange('participants', e.target.value)}
              >
                {[2, 3, 4, 5, 6, 7, 8].map(num => (
                  <MenuItem key={num} value={num}>
                    {num} participants IA
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Style de débat</InputLabel>
              <Select
                value={config.debate_style}
                label="Style de débat"
                onChange={(e) => handleConfigChange('debate_style', e.target.value)}
              >
                {debateStyles.map(style => (
                  <MenuItem key={style.value} value={style.value}>
                    <Tooltip title={style.description} arrow>
                      <span>{style.label}</span>
                    </Tooltip>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Providers IA */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" gutterBottom>
              <GroupIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Providers IA ({config.providers.length} sélectionné{config.providers.length > 1 ? 's' : ''})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {availableAIProviders.map(provider => (
                <Chip
                  key={provider.value}
                  label={provider.label}
                  color={config.providers.includes(provider.value) ? provider.color : 'default'}
                  variant={config.providers.includes(provider.value) ? 'filled' : 'outlined'}
                  onClick={() => handleProviderToggle(provider.value)}
                  clickable
                />
              ))}
            </Box>
            {errors.providers && (
              <Typography color="error" variant="caption" sx={{ mt: 1, display: 'block' }}>
                {errors.providers}
              </Typography>
            )}
          </Grid>
        </Grid>

        {/* Paramètres avancés */}
        <Accordion sx={{ mt: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <SettingsIcon sx={{ mr: 1 }} />
            <Typography>Paramètres avancés</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={3}>
              {/* Nombre de tours */}
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>
                  Tours maximum: {config.max_rounds}
                </Typography>
                <Slider
                  value={config.max_rounds}
                  onChange={(_, value) => handleConfigChange('max_rounds', value)}
                  min={1}
                  max={20}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Temps limite */}
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>
                  Temps limite par réponse: {config.time_limit}s
                </Typography>
                <Slider
                  value={config.time_limit}
                  onChange={(_, value) => handleConfigChange('time_limit', value)}
                  min={10}
                  max={120}
                  step={5}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Température */}
              <Grid item xs={12} sm={6}>
                <Typography gutterBottom>
                  Créativité (température): {config.temperature}
                </Typography>
                <Slider
                  value={config.temperature}
                  onChange={(_, value) => handleConfigChange('temperature', value)}
                  min={0}
                  max={1}
                  step={0.1}
                  valueLabelDisplay="auto"
                />
              </Grid>

              {/* Options */}
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.require_human_validation}
                      onChange={(e) => handleConfigChange('require_human_validation', e.target.checked)}
                    />
                  }
                  label="Validation humaine requise"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.enable_fact_checking}
                      onChange={(e) => handleConfigChange('enable_fact_checking', e.target.checked)}
                    />
                  }
                  label="Vérification des faits"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.auto_moderation}
                      onChange={(e) => handleConfigChange('auto_moderation', e.target.checked)}
                    />
                  }
                  label="Modération automatique"
                />
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>

        {/* Estimation de durée */}
        <Paper sx={{ p: 2, mt: 3, bgcolor: 'grey.50' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <TimerIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="body2">
              <strong>Durée estimée:</strong> ~{getEstimatedDuration()} minutes
            </Typography>
            <Tooltip title="Estimation basée sur le nombre de tours, participants et options de validation">
              <InfoIcon sx={{ ml: 1, fontSize: 16, color: 'text.secondary' }} />
            </Tooltip>
          </Box>
        </Paper>
      </CardContent>

      <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<StartIcon />}
          onClick={handleStartDebate}
          disabled={!systemReady || !config.topic.trim()}
          sx={{ minWidth: 200 }}
        >
          {systemReady ? 'Démarrer le Débat' : 'Système non prêt'}
        </Button>
      </CardActions>
    </Card>
  );
};

export default StartDebatePanel;