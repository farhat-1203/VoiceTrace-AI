# Deployment Checklist - VoiceTrace AI

## Pre-Deployment Checklist

### Environment Setup
- [ ] `.env` file configured with all required variables
- [ ] Supabase project created and configured
- [ ] Qdrant Cloud cluster created (free tier)
- [ ] Groq API key obtained
- [ ] Docker and Docker Compose installed

### Database Setup
- [ ] Run `migrations/001_initial_schema.sql` in Supabase
- [ ] Run `migrations/002_vendor_ledger_schema.sql` in Supabase
- [ ] Run `migrations/003_vendors_and_vapi.sql` in Supabase
- [ ] Verify all tables exist (11 tables total)
- [ ] Verify Row Level Security (RLS) policies are active
- [ ] Create Supabase Storage bucket: `audio-recordings` (private)

### Qdrant Setup
- [ ] Create collection: `vendor_memory`
- [ ] Vector size: 384 dimensions
- [ ] Distance metric: Cosine
- [ ] Run `backend/scripts/migrate_qdrant_collection.py` if migrating

### Backend Setup
- [ ] Build Docker image: `docker-compose build backend`
- [ ] Start backend: `docker-compose up -d backend`
- [ ] Check logs: `docker-compose logs -f backend`
- [ ] Verify health: `curl http://localhost:8000/health`
- [ ] Test transcription: `curl -X POST http://localhost:8000/transcribe`

### Frontend Setup
- [ ] Install dependencies: `cd frontend && pip install -r requirements.txt`
- [ ] Configure Streamlit: Check `.streamlit/config.toml`
- [ ] Start frontend: `streamlit run app.py`
- [ ] Test OAuth login
- [ ] Test audio recording
- [ ] Test audio upload

---

## Feature Testing Checklist

### Core Pipeline
- [ ] Audio upload works (wav, mp3, m4a)
- [ ] Transcription completes successfully
- [ ] Language detection works (Hindi/English/Hinglish)
- [ ] Guardrail blocks unsafe content
- [ ] Entity extraction returns structured data
- [ ] Memory storage in Qdrant works
- [ ] Memory retrieval works
- [ ] Response generation works

### Ledger Auto-Creation ✅
- [ ] Ledger entry created after audio upload
- [ ] Items extracted with confidence scores
- [ ] Expenses extracted with confidence scores
- [ ] Audio uploaded to Supabase Storage
- [ ] Presigned URL generated (7-day expiry)
- [ ] Audio segments stored with timestamps
- [ ] Uncertain items flagged (confidence < 0.7)
- [ ] Response includes `ledger_entry_id`
- [ ] Response includes `audio_url`

### API Endpoints
- [ ] `GET /health` - Returns healthy status
- [ ] `POST /process` - Full pipeline works
- [ ] `POST /transcribe` - Standalone transcription works
- [ ] `POST /analyze` - Text analysis works
- [ ] `GET /transcriptions` - Returns user history
- [ ] `GET /transcriptions/{id}` - Returns single transcription
- [ ] `GET /memories` - Returns important memories
- [ ] `GET /auth/me` - Returns current user

### Authentication
- [ ] Google OAuth works
- [ ] JWT tokens validated correctly
- [ ] User-scoped data isolation works
- [ ] Unauthorized requests blocked (401)

### Error Handling
- [ ] Invalid audio format rejected
- [ ] Audio too long rejected (>180s)
- [ ] Missing auth token returns 401
- [ ] Invalid token returns 401
- [ ] Pipeline errors logged but don't crash
- [ ] Ledger errors logged but don't crash

---

## Performance Testing Checklist

### Latency
- [ ] Audio upload: < 0.5s
- [ ] Transcription: 1-2s (3-min audio)
- [ ] Entity extraction: 0.5-1s
- [ ] Total pipeline: 3-4s
- [ ] Ledger creation: < 0.5s

### Throughput
- [ ] Handle 10 concurrent requests
- [ ] Handle 100 concurrent requests
- [ ] No memory leaks after 1000 requests
- [ ] Database connections properly pooled

### Storage
- [ ] Audio files stored correctly
- [ ] Presigned URLs work
- [ ] Old audio files can be cleaned up
- [ ] Database size reasonable

---

## Security Checklist

### Authentication & Authorization
- [ ] All endpoints require auth (except /health)
- [ ] JWT tokens validated on every request
- [ ] User can only access their own data
- [ ] RLS policies enforced in Supabase
- [ ] Service key not exposed to frontend

### Data Protection
- [ ] Audio files in private bucket
- [ ] Presigned URLs expire after 7 days
- [ ] PII not logged
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced in production

### Input Validation
- [ ] File size limits enforced
- [ ] File type validation
- [ ] Audio duration limits enforced
- [ ] SQL injection prevented (parameterized queries)
- [ ] XSS prevented (no raw HTML rendering)

### API Security
- [ ] CORS configured correctly
- [ ] Rate limiting implemented (if needed)
- [ ] API keys not in code
- [ ] Environment variables used for secrets

---

## Monitoring & Logging Checklist

### Logging
- [ ] All errors logged with context
- [ ] Request IDs for tracing
- [ ] Performance metrics logged
- [ ] User actions logged (audit trail)
- [ ] Log rotation configured

### Monitoring
- [ ] Health endpoint monitored
- [ ] Error rate monitored
- [ ] Latency monitored
- [ ] Storage usage monitored
- [ ] API quota usage monitored

### Alerts
- [ ] Alert on health check failure
- [ ] Alert on high error rate
- [ ] Alert on high latency
- [ ] Alert on storage quota
- [ ] Alert on API quota

---

## Documentation Checklist

### User Documentation
- [ ] README.md updated
- [ ] API documentation complete
- [ ] Authentication guide
- [ ] Troubleshooting guide
- [ ] FAQ

### Developer Documentation
- [ ] Architecture document complete
- [ ] Database schema documented
- [ ] API endpoints documented
- [ ] Environment variables documented
- [ ] Deployment guide

### Code Documentation
- [ ] All functions have docstrings
- [ ] Complex logic commented
- [ ] Type hints used
- [ ] Examples provided

---

## Production Deployment Checklist

### Infrastructure
- [ ] Production Supabase project created
- [ ] Production Qdrant cluster created
- [ ] Production domain configured
- [ ] SSL certificate installed
- [ ] CDN configured (if needed)

### Environment
- [ ] Production `.env` file configured
- [ ] All secrets rotated (new keys)
- [ ] Database backups enabled
- [ ] Monitoring enabled
- [ ] Logging enabled

### Deployment
- [ ] Build production Docker image
- [ ] Push to container registry
- [ ] Deploy to production server
- [ ] Run database migrations
- [ ] Verify health check
- [ ] Test critical paths

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Check performance metrics
- [ ] Verify user can sign in
- [ ] Verify audio upload works
- [ ] Verify ledger creation works
- [ ] Test from multiple devices

---

## Rollback Plan

### If Deployment Fails
1. [ ] Stop new deployment
2. [ ] Revert to previous Docker image
3. [ ] Rollback database migrations (if needed)
4. [ ] Verify old version works
5. [ ] Investigate failure
6. [ ] Fix and redeploy

### Database Rollback
```sql
-- If migration 003 needs rollback
DROP TABLE IF EXISTS vapi_calls;
DROP TABLE IF EXISTS pending_clarifications;
DROP TABLE IF EXISTS vendors;

-- If migration 002 needs rollback
DROP TABLE IF EXISTS audio_segments;
DROP TABLE IF EXISTS stock_suggestions;
DROP TABLE IF EXISTS anomaly_alerts;
DROP TABLE IF EXISTS vendor_patterns;
DROP TABLE IF EXISTS ledger_expenses;
DROP TABLE IF EXISTS ledger_items;
DROP TABLE IF EXISTS ledger_entries;
```

---

## Maintenance Checklist

### Daily
- [ ] Check error logs
- [ ] Monitor API usage
- [ ] Check storage usage
- [ ] Verify backups

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Review user feedback
- [ ] Clean up old audio files (>30 days)

### Monthly
- [ ] Update dependencies
- [ ] Review and optimize queries
- [ ] Analyze usage patterns
- [ ] Plan new features

---

## Testing Scenarios

### Happy Path
1. [ ] User signs in with Google
2. [ ] User records 3-minute audio
3. [ ] Audio transcribed successfully
4. [ ] Items and expenses extracted
5. [ ] Ledger entry created
6. [ ] User sees summary
7. [ ] User can play back audio

### Edge Cases
1. [ ] Very short audio (5 seconds)
2. [ ] Maximum length audio (180 seconds)
3. [ ] Silent audio
4. [ ] Noisy audio
5. [ ] Mixed Hindi/English
6. [ ] No items mentioned
7. [ ] No expenses mentioned
8. [ ] Vague descriptions

### Error Cases
1. [ ] Invalid audio format
2. [ ] Corrupted audio file
3. [ ] Network timeout
4. [ ] Groq API error
5. [ ] Supabase connection error
6. [ ] Qdrant connection error
7. [ ] Storage quota exceeded

---

## Success Metrics

### Technical Metrics
- [ ] 99% uptime
- [ ] < 5s average response time
- [ ] < 1% error rate
- [ ] < 100ms database query time

### Business Metrics
- [ ] 100+ daily active users
- [ ] 1000+ audio recordings processed
- [ ] 90%+ user retention
- [ ] < 5% support tickets

### Quality Metrics
- [ ] 95%+ transcription accuracy
- [ ] 90%+ entity extraction accuracy
- [ ] 80%+ confidence scores > 0.7
- [ ] < 10% items need confirmation

---

## Current Status

### Completed ✅
- [x] Core infrastructure
- [x] LangGraph pipeline
- [x] All services (100%)
- [x] Database schema
- [x] Ledger auto-creation
- [x] Audio storage
- [x] Confidence scoring
- [x] Documentation

### In Progress ⚠️
- [ ] API routes (40%)
- [ ] Testing (40%)

### Not Started ❌
- [ ] VAPI integration
- [ ] PDF export
- [ ] Pattern detection cron
- [ ] Production deployment

### Overall Progress: 72%

---

## Quick Commands

### Start Everything
```bash
docker-compose up -d --build
```

### Check Health
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
docker-compose logs -f backend
```

### Run Tests
```bash
cd backend
python test_ledger_integration.py
```

### Stop Everything
```bash
docker-compose down
```

### Clean Everything
```bash
docker-compose down -v
docker system prune -a
```

---

## Support Contacts

- **Supabase Support:** https://supabase.com/support
- **Qdrant Support:** https://qdrant.tech/support
- **Groq Support:** https://groq.com/support
- **Docker Support:** https://docs.docker.com/

---

**Last Updated:** March 28, 2026  
**Version:** 1.0  
**Status:** Ready for testing
