# Quick Migration Steps - Multilingual Embeddings

## 🚀 3-Step Migration

### Step 1: Migrate Qdrant Collection (2 minutes)
```bash
cd backend
python scripts/migrate_qdrant_collection.py
# Type 'DELETE' when prompted
```

### Step 2: Rebuild Containers (3 minutes)
```bash
cd ..
docker-compose down
docker-compose up -d --build
```

### Step 3: Test (1 minute)
```bash
cd backend
python scripts/test_embeddings.py
```

## ✅ Success Indicators

**In logs:**
```
FastEmbed model loaded ✓ (multilingual-e5-small with Hindi support)
```

**Test output:**
```
ALL TESTS PASSED ✓
Multilingual embeddings are working correctly!
```

## 🎯 What This Enables

| Before | After |
|--------|-------|
| English only | Hindi + English + Hinglish |
| "Today I sold bananas" ✅ | "Aaj maine kele beche" ✅ |
| "Business was good" ✅ | "Dhanda achha tha" ✅ |
| Mixed language ❌ | "Aaj business achha tha" ✅ |

## 📝 Key Changes

1. **Model:** `BAAI/bge-small-en-v1.5` → `intfloat/multilingual-e5-small`
2. **Prefixes:** Now required (`query:` and `passage:`)
3. **Languages:** 1 → 100+ (including Hindi)
4. **Performance:** Same (384 dims, ~3ms, ~200MB RAM)

## ⚠️ Important Notes

- **Data Loss:** Old embeddings will be deleted (incompatible vector space)
- **Prefixes:** Automatically added by `embedding_service`
- **No Downtime:** Can migrate while system is running
- **Reversible:** Can rollback if needed (see full guide)

## 🔍 Verify Migration

```bash
# Check backend logs
docker logs voicetrace-backend | grep "FastEmbed"

# Should see:
# FastEmbed model loaded ✓ (multilingual-e5-small with Hindi support)
```

## 📚 Full Documentation

- **Complete Guide:** `EMBEDDING_MIGRATION_GUIDE.md`
- **Technical Details:** `MULTILINGUAL_EMBEDDING_SUMMARY.md`
- **Test Script:** `backend/scripts/test_embeddings.py`
- **Migration Script:** `backend/scripts/migrate_qdrant_collection.py`

## 🆘 Troubleshooting

**Issue:** Model not downloading
```bash
# Ensure internet connection
# FastEmbed auto-downloads on first use (~40MB)
```

**Issue:** Tests failing
```bash
# Check Python dependencies
pip install -r backend/requirements.txt
```

**Issue:** Qdrant connection error
```bash
# Verify QDRANT_URL and QDRANT_API_KEY in .env
```

## ✨ Ready to Use!

After migration, your system supports:
- ✅ Hindi voice recordings
- ✅ English voice recordings  
- ✅ Hinglish (code-mixed) recordings
- ✅ Multilingual VAPI queries
- ✅ Cross-language similarity search

**Total Migration Time:** ~6 minutes
