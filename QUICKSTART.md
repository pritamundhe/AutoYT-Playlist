# Quick Start Guide - YouTube Playlist Generator

## 🚀 Get Started in 5 Minutes

### Step 1: Get YouTube API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Copy your API key

### Step 2: Setup Environment

**Option A: Docker (Easiest)**

```bash
# Navigate to project
cd c:\Users\Acer\Documents\GitHub\AutoYT-Playlist

# Create environment file
echo YOUTUBE_API_KEY=your_api_key_here > .env

# Start all services
docker-compose up --build

# Wait for services to start (2-3 minutes)
# Access: http://localhost:3000
```

**Option B: Manual Setup**

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download NLP model
python -m spacy download en_core_web_sm

# Setup environment
copy .env.example .env
# Edit .env and add:
# - YOUTUBE_API_KEY=your_key
# - DATABASE_URL=postgresql://postgres:password@localhost:5432/youtube_playlist
# - REDIS_URL=redis://localhost:6379/0

# Start PostgreSQL and Redis (install separately or use Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
docker run -d -p 6379:6379 redis:7

# Run backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Step 3: Test the System

1. **Open browser**: http://localhost:3000

2. **Upload sample syllabus**:
   - Use provided sample: `data/sample_syllabi/ml_course_syllabus.txt`
   - Or upload your own PDF/DOCX/TXT

3. **Wait for processing** (~10-20 seconds):
   - Document upload
   - Topic extraction
   - Automatic redirect to topics page

4. **Generate playlist**:
   - Review extracted topics
   - Adjust ranking weights (optional)
   - Click "Generate Playlist"
   - Wait for YouTube search and ranking

5. **View results**:
   - Browse curated videos
   - See scores and rankings
   - Export to JSON/CSV/Markdown

### Step 4: API Testing

**Swagger UI**: http://localhost:8000/docs

**Example API Calls:**

```bash
# Upload document
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@syllabus.pdf"

# Extract topics
curl -X POST "http://localhost:8000/api/extract-topics/{document_id}"

# Generate playlist
curl -X POST "http://localhost:8000/api/generate-playlist" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "uuid",
    "name": "My Playlist",
    "weights": {
      "views": 0.15,
      "likes": 0.20,
      "subscribers": 0.10,
      "relevance": 0.40,
      "recency": 0.10,
      "duration_penalty": 0.05
    },
    "videos_per_topic": 5,
    "use_ml_ranking": true
  }'
```

---

## 🔧 Troubleshooting

### Issue: "YouTube API quota exceeded"
**Solution**: Default quota is 10,000 units/day. Each search costs 100 units. Reduce `videos_per_topic` or wait 24 hours.

### Issue: "Database connection failed"
**Solution**: Ensure PostgreSQL is running on port 5432. Check `DATABASE_URL` in `.env`.

### Issue: "Redis connection failed"
**Solution**: Ensure Redis is running on port 6379. Check `REDIS_URL` in `.env`.

### Issue: "spaCy model not found"
**Solution**: Run `python -m spacy download en_core_web_sm`

### Issue: "Frontend can't connect to backend"
**Solution**: Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` points to `http://localhost:8000`

---

## 📊 System Requirements

**Minimum:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 2 GB
- Internet: Required for YouTube API

**Recommended:**
- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 5 GB
- Internet: Stable connection

---

## 🎓 For Research/Academic Use

### Running Evaluation

```bash
# Generate playlist first, then:
curl -X POST "http://localhost:8000/api/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"playlist_id": "uuid"}'

# View metrics
curl "http://localhost:8000/api/evaluation/{playlist_id}"
```

### Collecting User Feedback

```bash
curl -X POST "http://localhost:8000/api/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_item_id": "uuid",
    "rating": 5,
    "relevance_score": 5,
    "quality_score": 4,
    "comment": "Excellent video!"
  }'
```

### Exporting Data

```bash
# Export playlist
curl -X POST "http://localhost:8000/api/export-playlist" \
  -H "Content-Type: application/json" \
  -d '{
    "playlist_id": "uuid",
    "format": "json"
  }'

# Files saved to: data/exports/
```

---

## 📈 Performance Monitoring

**Check API quota usage:**
```python
from app.services.youtube_service import YouTubeService

service = YouTubeService()
usage = service.get_quota_usage()
print(f"Used: {usage['used']}/{usage['limit']}")
```

**Monitor Redis cache:**
```bash
redis-cli
> KEYS youtube:*
> GET youtube:search:{query}
```

**Database statistics:**
```sql
-- Connect to PostgreSQL
psql -U postgres -d youtube_playlist

-- Count records
SELECT 
  (SELECT COUNT(*) FROM documents) as documents,
  (SELECT COUNT(*) FROM topics) as topics,
  (SELECT COUNT(*) FROM videos) as videos,
  (SELECT COUNT(*) FROM playlists) as playlists;
```

---

## 🎯 Next Steps

1. **Test with your syllabus**: Upload a real course syllabus
2. **Adjust weights**: Experiment with different ranking configurations
3. **Evaluate results**: Run evaluation metrics
4. **Collect feedback**: Have users rate videos
5. **Train ML model**: Use feedback to train XGBoost ranker
6. **Write paper**: Document your findings

---

## 📚 Additional Resources

- **Full Documentation**: [README.md](file:///c:/Users/Acer/Documents/GitHub/AutoYT-Playlist/README.md)
- **Architecture**: [architecture.md](file:///C:/Users/Acer/.gemini/antigravity/brain/d2a846c7-b715-4cbf-bd5b-88a979ee39e8/architecture.md)
- **Walkthrough**: [walkthrough.md](file:///C:/Users/Acer/.gemini/antigravity/brain/d2a846c7-b715-4cbf-bd5b-88a979ee39e8/walkthrough.md)
- **API Docs**: http://localhost:8000/docs
- **YouTube API**: https://developers.google.com/youtube/v3

---

## 💡 Tips for Best Results

1. **Use structured syllabi**: Clear headings and bullet points work best
2. **Adjust relevance weight**: Increase to 0.5-0.6 for more topic-focused results
3. **Filter by views**: Set `min_views: 10000` to get popular videos
4. **Enable captions**: Set `has_captions: true` for accessibility
5. **Limit duration**: Set `max_duration: 1200` (20 min) for concise videos

---

## 🤝 Support

For issues or questions:
1. Check [troubleshooting](#troubleshooting) section
2. Review API documentation
3. Check logs in `logs/app.log`
4. Open GitHub issue (if repository is public)

---

**Happy playlist generating! 🎉**
