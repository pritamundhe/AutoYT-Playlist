# Setup Instructions for Minimal Installation

## Quick Setup (No Heavy ML Libraries)

This setup skips PyTorch, Transformers, and spaCy. You'll train models on Kaggle and download the pre-trained files.

### 1. Install Minimal Dependencies

```powershell
cd c:\Users\Acer\Documents\GitHub\AutoYT-Playlist\backend

# Install minimal requirements (much faster!)
pip install -r requirements-minimal.txt
```

### 2. Train Models on Kaggle

Create a Kaggle notebook to train:

**A. Topic Extraction Model**
- Use Sentence-BERT or similar
- Train on academic syllabi
- Save as `topic_extractor.pkl`

**B. Embedding Model**
- Use pre-trained sentence embeddings
- Save as `embeddings.pkl`

**C. Ranking Model (Optional)**
- Train XGBoost on user feedback
- Save as `xgboost_ranker.pkl`

### 3. Download and Place Models

```
AutoYT-Playlist/
└── ml_models/
    ├── nlp/
    │   ├── topic_extractor.pkl    # From Kaggle
    │   └── embeddings.pkl          # From Kaggle
    └── ranking/
        └── xgboost_ranker.pkl      # From Kaggle (optional)
```

### 4. Update Code to Use Simple Versions

The system will automatically:
- Use `nlp_processor_simple.py` (rule-based fallback if no model)
- Use `relevance_scorer_simple.py` (keyword matching fallback)
- Load your Kaggle models if available

### 5. Start the Server

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

## What Works Without Models

Even without trained models, the system will work using:
- **Rule-based topic extraction**: Looks for "Unit 1", "Chapter 1", etc.
- **Keyword matching**: Compares topic keywords with video titles
- **Multi-criteria ranking**: Still uses views, likes, recency, etc.

## Kaggle Training Template

```python
# Kaggle Notebook: Train Topic Extractor

from sentence_transformers import SentenceTransformer
import pickle

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Your training code here...

# Save model
with open('topic_extractor.pkl', 'wb') as f:
    pickle.dump(model, f)

# Download the .pkl file
```

## Benefits of This Approach

✅ **Fast installation** (2-3 minutes vs 10-15 minutes)
✅ **Smaller package size** (~500MB vs ~5GB)
✅ **Works on low-end machines**
✅ **Train on Kaggle's free GPUs**
✅ **Easy model updates** (just replace .pkl files)

## Next Steps

1. Install minimal requirements
2. Test with rule-based fallback
3. Train models on Kaggle when ready
4. Download and add .pkl files
5. System automatically uses trained models
