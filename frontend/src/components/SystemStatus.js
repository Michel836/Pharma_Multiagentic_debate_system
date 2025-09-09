// SystemStatus.js - Composant d'affichage du statut système
import React, { useState } from 'react';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Computer as ProviderIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon
} from '@mui/icons-material';

const SystemStatus = ({ status }) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Détermine l'icône et la couleur selon le statut
  const getStatusDisplay = () => {
    if (status.loading) {
      return {
        icon: <CircularProgress size={16} />,
        color: 'default',
        label: 'Vérification...',
        tooltip: 'Vérification du statut système en cours'
      };
    }

    if (status.healthy) {
      return {
        icon: <HealthyIcon sx={{ fontSize: 16 }} />,
        color: 'success',
        label: `Opérationnel (${status.providers} IA)`,
        tooltip: `Système opérationnel avec ${status.providers} provider(s) IA disponible(s)`
      };
    } else {
      return {
        icon: <ErrorIcon sx={{ fontSize: 16 }} />,
        color: 'error',
        label: status.providers > 0 ? `Partiel (${status.providers} IA)` : 'Hors ligne',
        tooltip: status.error || 'Système non opérationnel - Vérifiez la connexion backend'
      };
    }
  };

  const statusDisplay = getStatusDisplay();

  // Formatage des détails du statut
  const formatStatusDetails = () => {
    if (!status.details) return null;

    const details = status.details;
    const items = [];

    // Statut général
    items.push({
      icon: details.status === 'healthy' ? <HealthyIcon color="success" /> : <ErrorIcon color="error" />,
      primary: 'Statut Général',
      secondary: details.status === 'healthy' ? 'Système opérationnel' : 'Problème détecté'
    });

    // Informations système
    if (details.system_info) {
      const sysInfo = details.system_info;
      items.push({
        icon: <MemoryIcon color="primary" />,
        primary: 'Mémoire',
        secondary: `${sysInfo.memory_usage?.toFixed(1) || 'N/A'}% utilisée`
      });
      
      items.push({
        icon: <SpeedIcon color="primary" />,
        primary: 'CPU',
        secondary: `${sysInfo.cpu_usage?.toFixed(1) || 'N/A'}% utilisé`
      });
    }

    // Providers IA
    if (details.providers_status) {
      Object.entries(details.providers_status).forEach(([provider, info]) => {
        items.push({
          icon: <ProviderIcon color={info.available ? "success" : "error"} />,
          primary: `Provider ${provider}`,
          secondary: info.available 
            ? `Disponible${info.model ? ` (${info.model})` : ''}`
            : `Indisponible: ${info.error || 'Erreur inconnue'}`
        });
      });
    }

    // Timestamp
    if (details.timestamp) {
      items.push({
        icon: <InfoIcon color="primary" />,
        primary: 'Dernière vérification',
        secondary: new Date(details.timestamp).toLocaleString('fr-FR')
      });
    }

    return items;
  };

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title={statusDisplay.tooltip}>
        <Chip
          icon={statusDisplay.icon}
          label={statusDisplay.label}
          color={statusDisplay.color}
          variant="outlined"
          size="small"
          onClick={() => setDetailsOpen(true)}
          sx={{ 
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)'
            }
          }}
        />
      </Tooltip>

      {/* Bouton de rafraîchissement si le système est en erreur */}
      {!status.loading && !status.healthy && (
        <Tooltip title="Actualiser le statut">
          <IconButton 
            size="small" 
            onClick={() => window.location.reload()}
            sx={{ color: 'white' }}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}

      {/* Dialog des détails */}
      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {statusDisplay.icon}
            <Typography variant="h6">
              Statut Système Détaillé
            </Typography>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          {status.loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <CircularProgress />
              <Typography sx={{ ml: 2 }}>Chargement des informations système...</Typography>
            </Box>
          ) : (
            <>
              {/* Résumé rapide */}
              <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Résumé
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  {status.healthy 
                    ? `Système opérationnel avec ${status.providers} provider(s) IA disponible(s)`
                    : `Système ${status.providers > 0 ? 'partiellement' : 'complètement'} indisponible`
                  }
                </Typography>
              </Box>

              {/* Détails */}
              {formatStatusDetails() && (
                <List dense>
                  {formatStatusDetails().map((item, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemIcon sx={{ minWidth: 36 }}>
                          {item.icon}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.primary}
                          secondary={item.secondary}
                        />
                      </ListItem>
                      {index < formatStatusDetails().length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}

              {/* Message d'erreur si présent */}
              {status.error && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'error.light', borderRadius: 1 }}>
                  <Typography variant="subtitle2" color="error.contrastText">
                    Erreur détectée:
                  </Typography>
                  <Typography variant="body2" color="error.contrastText">
                    {status.error}
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>
            Fermer
          </Button>
          <Button 
            onClick={() => window.location.reload()} 
            variant="outlined"
            startIcon={<RefreshIcon />}
          >
            Actualiser
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SystemStatus;