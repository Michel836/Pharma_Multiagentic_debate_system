import React from 'react';
import {
  Box,
  Paper,
  Typography,
  LinearProgress,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  ThumbUp,
  ThumbDown,
  HowToVote,
  CheckCircle,
  Cancel,
  Pending
} from '@mui/icons-material';

const VotingPanel = ({ votes, consensus, onVote, currentRound, maxRounds }) => {
  // Calculer les statistiques de vote
  const calculateVoteStats = () => {
    if (!votes || votes.length === 0) return { for: 0, against: 0, abstain: 0 };
    
    const stats = votes.reduce((acc, vote) => {
      if (vote.decision === 'approve') acc.for++;
      else if (vote.decision === 'reject') acc.against++;
      else acc.abstain++;
      return acc;
    }, { for: 0, against: 0, abstain: 0 });
    
    return stats;
  };

  const stats = calculateVoteStats();
  const totalVotes = votes ? votes.length : 0;
  const consensusPercentage = consensus ? consensus * 100 : 0;

  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3, bgcolor: 'background.paper' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <HowToVote color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6" component="h2">
          Panel de Vote - Tour {currentRound}/{maxRounds}
        </Typography>
      </Box>

      {/* Barre de consensus */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Niveau de Consensus
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            {consensusPercentage.toFixed(1)}%
          </Typography>
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={consensusPercentage}
          sx={{
            height: 10,
            borderRadius: 5,
            backgroundColor: 'grey.300',
            '& .MuiLinearProgress-bar': {
              borderRadius: 5,
              background: consensusPercentage > 80 
                ? 'linear-gradient(90deg, #4CAF50, #8BC34A)'
                : consensusPercentage > 50
                ? 'linear-gradient(90deg, #FF9800, #FFB74D)'
                : 'linear-gradient(90deg, #f44336, #ef5350)'
            }
          }}
        />
        {consensusPercentage > 80 && (
          <Alert severity="success" sx={{ mt: 1 }}>
            Consensus fort atteint! Décision validée.
          </Alert>
        )}
      </Box>

      {/* Statistiques de vote */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Paper sx={{ flex: 1, p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
          <ThumbUp color="success" />
          <Typography variant="h4">{stats.for}</Typography>
          <Typography variant="body2" color="text.secondary">Pour</Typography>
        </Paper>
        
        <Paper sx={{ flex: 1, p: 2, textAlign: 'center', bgcolor: 'error.light' }}>
          <ThumbDown color="error" />
          <Typography variant="h4">{stats.against}</Typography>
          <Typography variant="body2" color="text.secondary">Contre</Typography>
        </Paper>
        
        <Paper sx={{ flex: 1, p: 2, textAlign: 'center', bgcolor: 'grey.200' }}>
          <Pending />
          <Typography variant="h4">{stats.abstain}</Typography>
          <Typography variant="body2" color="text.secondary">Abstention</Typography>
        </Paper>
      </Stack>

      {/* Détail des votes par agent */}
      {votes && votes.length > 0 && (
        <Box>
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
            Votes des Agents:
          </Typography>
          <Stack spacing={1}>
            {votes.map((vote, index) => (
              <Box 
                key={index}
                sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  p: 1,
                  borderRadius: 1,
                  bgcolor: 'grey.50'
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Chip
                    label={vote.agent}
                    size="small"
                    color={vote.role === 'judge' ? 'primary' : 'default'}
                  />
                  <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                    "{vote.reasoning?.substring(0, 100)}..."
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {vote.decision === 'approve' && (
                    <CheckCircle color="success" />
                  )}
                  {vote.decision === 'reject' && (
                    <Cancel color="error" />
                  )}
                  {vote.decision === 'abstain' && (
                    <Pending color="disabled" />
                  )}
                  <Typography 
                    variant="body2" 
                    sx={{ ml: 1, fontWeight: 'bold' }}
                    color={
                      vote.decision === 'approve' ? 'success.main' : 
                      vote.decision === 'reject' ? 'error.main' : 
                      'text.disabled'
                    }
                  >
                    {vote.confidence ? `${(vote.confidence * 100).toFixed(0)}%` : ''}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        </Box>
      )}

      {/* Boutons d'action pour vote manuel */}
      {onVote && (
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
          <Tooltip title="Approuver la proposition">
            <IconButton 
              color="success" 
              size="large"
              onClick={() => onVote('approve')}
              sx={{ 
                bgcolor: 'success.light',
                '&:hover': { bgcolor: 'success.main', color: 'white' }
              }}
            >
              <ThumbUp />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Rejeter la proposition">
            <IconButton 
              color="error" 
              size="large"
              onClick={() => onVote('reject')}
              sx={{ 
                bgcolor: 'error.light',
                '&:hover': { bgcolor: 'error.main', color: 'white' }
              }}
            >
              <ThumbDown />
            </IconButton>
          </Tooltip>
          
          <Tooltip title="S'abstenir">
            <IconButton 
              size="large"
              onClick={() => onVote('abstain')}
              sx={{ 
                bgcolor: 'grey.300',
                '&:hover': { bgcolor: 'grey.500', color: 'white' }
              }}
            >
              <Pending />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Indicateur de tour */}
      <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            Progression du débat
          </Typography>
          <Chip 
            label={`${currentRound}/${maxRounds} tours`}
            size="small"
            color={currentRound >= maxRounds ? 'error' : 'primary'}
          />
        </Box>
        <LinearProgress 
          variant="determinate" 
          value={(currentRound / maxRounds) * 100}
          sx={{ mt: 1, height: 6, borderRadius: 3 }}
        />
      </Box>
    </Paper>
  );
};

export default VotingPanel;