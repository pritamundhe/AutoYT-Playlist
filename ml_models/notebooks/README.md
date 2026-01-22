# Model Training Notebooks

यह folder में तीन Jupyter notebooks हैं जो आप **Kaggle पर चला सकते हैं** और trained models को download करके इस project में use कर सकते हैं।

## 📚 Notebooks

### 1. [01_topic_extraction_training.ipynb](01_topic_extraction_training.ipynb)
**Purpose**: Syllabus से topics extract करने के लिए model train करता है।

**Output**: `topic_extractor.pkl`

**What it does**:
- PDF/DOCX/TXT से topics निकालता है
- Unit, Chapter, Week patterns को detect करता है
- Subtopics को identify करता है
- Clustering-based topic extraction

**Place output in**: `ml_models/nlp/topic_extractor.pkl`

---

### 2. [02_embedding_generation.ipynb](02_embedding_generation.ipynb)
**Purpose**: Video relevance scoring के लिए embeddings generate करता है।

**Output**: `embeddings.pkl`

**What it does**:
- Sentence-BERT model load करता है
- Text को vector embeddings में convert करता है
- Semantic similarity calculate करता है
- Fast caching के साथ

**Place output in**: `ml_models/nlp/embeddings.pkl`

---

### 3. [03_xgboost_ranker_training.ipynb](03_xgboost_ranker_training.ipynb)
**Purpose**: Videos को rank करने के लिए ML model train करता है।

**Output**: `xgboost_ranker.pkl`

**What it does**:
- Learning-to-Rank model train करता है
- Multiple features use करता है (views, likes, relevance, etc.)
- nDCG metric से evaluate करता है
- Feature importance दिखाता है

**Place output in**: `ml_models/ranking/xgboost_ranker.pkl`

---

## 🚀 Kaggle पर कैसे चलाएं?

### Step 1: Kaggle Account बनाएं
1. [kaggle.com](https://www.kaggle.com) पर जाएं
2. Sign up करें (free है!)

### Step 2: New Notebook बनाएं
1. Kaggle पर "Code" → "New Notebook" click करें
2. "File" → "Upload Notebook" से notebook upload करें
3. या फिर code को copy-paste करें

### Step 3: Run करें
1. सभी cells को run करें (Shift + Enter)
2. या "Run All" button click करें
3. Wait करें जब तक model train हो जाए

### Step 4: Download करें
1. Output section में `.pkl` file दिखेगी
2. Download करें
3. अपने project के सही folder में paste करें

---

## 📁 File Placement

Models को download करने के बाद यहां रखें:

```
AutoYT-Playlist/
└── ml_models/
    ├── nlp/
    │   ├── topic_extractor.pkl    ← Notebook 1 से
    │   └── embeddings.pkl          ← Notebook 2 से
    └── ranking/
        └── xgboost_ranker.pkl      ← Notebook 3 से
```

---

## ⚙️ System Integration

जब आप `.pkl` files को सही जगह रखेंगे:

1. **Backend automatically detect करेगा** कि models available हैं
2. **Rule-based fallback से switch होगा** ML-based processing पर
3. **Better results मिलेंगे** topic extraction और ranking में

---

## 🔧 Customization

### अपना data use करना चाहते हैं?

**Notebook 1 & 2**: 
- अपनी syllabus files upload करें Kaggle dataset में
- Sample data को replace करें

**Notebook 3**:
- Real user feedback data use करें
- Synthetic data को replace करें
- Features add/remove करें

### Hyperparameters tune करना चाहते हैं?

हर notebook में parameters section है:
- Learning rate
- Model depth
- Clustering parameters
- etc.

---

## 📊 Expected Performance

| Model | Metric | Expected Value |
|-------|--------|----------------|
| Topic Extractor | Accuracy | 85-95% |
| Embeddings | Similarity | Cosine 0-1 |
| XGBoost Ranker | nDCG@10 | 0.70-0.85 |

---

## ❓ Troubleshooting

### "Out of Memory" error?
- Kaggle में GPU/TPU enable करें
- Batch size कम करें
- Smaller model use करें

### Model load नहीं हो रहा?
- Check करें file path सही है
- Verify करें `.pkl` extension है
- Backend logs देखें

### Results अच्छे नहीं हैं?
- More training data use करें
- Hyperparameters tune करें
- Features add करें

---

## 🎯 Next Steps

1. ✅ तीनों notebooks Kaggle पर run करें
2. ✅ `.pkl` files download करें
3. ✅ सही folders में place करें
4. ✅ Backend restart करें
5. ✅ Test करें!

---

## 📞 Need Help?

- Kaggle documentation: [kaggle.com/docs](https://www.kaggle.com/docs)
- XGBoost docs: [xgboost.readthedocs.io](https://xgboost.readthedocs.io/)
- Sentence-BERT: [sbert.net](https://www.sbert.net/)

Happy Training! 🚀
