# 🚀 DÉMARRAGE RAPIDE - MODE 100% LOCAL AVEC OLLAMA

## ✅ Version simplifiée sans connexion externe!

Ce guide vous permet de démarrer le système multiagent en utilisant **uniquement Ollama** sur votre machine locale, sans aucune connexion Internet ou API externe.

---

## 📋 Prérequis

1. **Ollama installé** : [Télécharger Ollama](https://ollama.ai)
2. **Python 3.11+** installé
3. **Node.js 18+** installé
4. **8 GB RAM minimum** (16 GB recommandé)

---

## 🎯 Démarrage Ultra-Rapide (30 secondes)

### Option 1: Script automatique (Windows)

Double-cliquez sur:
```
start_ollama_only.bat
```

C'est tout! Le script fait tout automatiquement:
- ✅ Démarre Ollama
- ✅ Télécharge le modèle llama3.2 (si nécessaire)
- ✅ Lance le backend Python
- ✅ Lance le frontend React
- ✅ Ouvre votre navigateur

---

### Option 2: Démarrage manuel

#### Étape 1: Démarrer Ollama
```bash
ollama serve
```

#### Étape 2: Installer le modèle (première fois seulement)
```bash
ollama pull llama3.2
```

#### Étape 3: Démarrer le backend
```bash
cd backend
python main_ollama.py
```

#### Étape 4: Démarrer le frontend
```bash
cd frontend
npm start
```

#### Étape 5: Ouvrir le navigateur
Allez à: http://localhost:3000

---

## 🎮 Utilisation

### Interface Simple

1. **Écrivez votre question** dans le champ de texte
2. **Cliquez sur "Démarrer le débat"**
3. **Regardez les 3 experts débattre** en temps réel
4. **Le juge synthétise** à la fin de chaque tour
5. **Consensus atteint** = résultat final!

### Exemple de questions:

- "Quelle est la meilleure méthode pour valider un nouveau médicament?"
- "Comment optimiser la formulation d'un comprimé à libération prolongée?"
- "Quels sont les risques de contamination croisée en production?"

---

## 🔧 Configuration Simplifiée

### Changer de modèle Ollama

Éditez `backend/config/ollama_config.yaml`:
```yaml
ollama:
  default_model: "mistral:7b"  # ou "llama3.2", "qwen2.5:7b"
```

### Modèles recommandés par performance:

| Modèle | Taille | RAM nécessaire | Qualité | Vitesse |
|--------|--------|----------------|---------|---------|
| llama3.2:3b | 3.2 GB | 4 GB | Bonne | Rapide |
| mistral:7b | 4.1 GB | 8 GB | Très bonne | Moyenne |
| llama3.1:8b | 4.7 GB | 8 GB | Excellente | Moyenne |
| qwen2.5:7b | 4.4 GB | 8 GB | Excellente | Rapide |

### Installer d'autres modèles:
```bash
ollama pull mistral:7b
ollama pull qwen2.5:7b
```

---

## 🎯 Architecture Simplifiée

```
Votre PC (100% local)
│
├── Ollama (Port 11434)
│   └── Modèle llama3.2
│       ├── Expert 1
│       ├── Expert 2
│       ├── Expert 3
│       └── Juge
│
├── Backend Python (Port 8000)
│   └── Orchestrateur de débat
│
└── Frontend React (Port 3000)
    └── Interface utilisateur
```

---

## 🚨 Résolution de problèmes

### Ollama ne démarre pas
```bash
# Vérifier l'installation
ollama version

# Redémarrer le service
ollama serve
```

### Modèle trop lent
- Utilisez un modèle plus petit (llama3.2:3b)
- Fermez les autres applications
- Réduisez le nombre de tours de débat

### Port déjà utilisé
```bash
# Changer les ports dans .env.ollama
REACT_APP_API_URL=http://localhost:8001  # Backend sur 8001
```

---

## 💡 Astuces Performance

### 1. Pour PC avec peu de RAM (< 8GB)
- Utilisez `llama3.2:3b` ou `phi3:mini`
- Limitez à 3 tours de débat maximum
- Un seul expert + un juge

### 2. Pour PC Gaming (16GB+ RAM, GPU)
- Utilisez `llama3.1:8b` ou `mistral:7b`
- Jusqu'à 10 tours de débat
- 3-5 experts possibles

### 3. Optimisation GPU (NVIDIA)
```bash
# Activer l'accélération GPU
set OLLAMA_GPU=true
ollama serve
```

---

## 📊 Exemples de Débats

### Débat Pharmaceutique Simple
**Question**: "Validation d'un nouveau processus de stérilisation"

**Résultat typique**:
- Tour 1: Identification des risques
- Tour 2: Méthodes de validation proposées
- Tour 3: Consensus sur l'approche
- Synthèse: Plan d'action structuré

### Temps de réponse moyens
- Modèle 3B: ~5 secondes par réponse
- Modèle 7B: ~10 secondes par réponse
- Débat complet (3 tours): 2-3 minutes

---

## 🎉 C'est parti!

1. **Lancez** `start_ollama_only.bat`
2. **Posez** votre question
3. **Regardez** le débat
4. **Obtenez** des réponses validées!

**Aucune connexion Internet requise** ✅
**100% confidentiel sur votre PC** 🔒
**Gratuit et open source** 💚

---

## 📞 Support

- Problème? Créez une issue sur GitHub
- Question? Consultez la FAQ ci-dessous

### FAQ

**Q: Puis-je utiliser d'autres modèles?**
R: Oui! Tous les modèles Ollama sont compatibles.

**Q: Combien de RAM ai-je besoin?**
R: Minimum 4GB, recommandé 8GB+

**Q: Est-ce vraiment 100% local?**
R: Oui! Aucune donnée ne sort de votre PC.

**Q: Puis-je modifier les prompts des agents?**
R: Oui, dans `backend/config/ollama_config.yaml`

---

## 🏆 Commandes Utiles

```bash
# Voir les modèles installés
ollama list

# Supprimer un modèle
ollama rm llama3.2

# Voir l'utilisation mémoire
ollama ps

# Tester directement un modèle
ollama run llama3.2 "Bonjour!"
```

---

**Profitez du système multiagent 100% local! 🚀**