# OAuth Authentication Fix Guide

## The Problem
You're getting: `Unable to exchange external code: 4/0A`

This error occurs when the OAuth code exchange fails between Google → Supabase → Your App.

## Root Causes & Solutions

### 1. Redirect URI Mismatch

**In Google Cloud Console:**
- Go to: https://console.cloud.google.com/
- Navigate to: APIs & Services → Credentials
- Click your OAuth 2.0 Client ID
- Under "Authorized redirect URIs", add BOTH:
  ```
  https://YOUR-PROJECT-REF.supabase.co/auth/v1/callback
  http://localhost:8501
  ```
  Replace `YOUR-PROJECT-REF` with your actual Supabase project reference (e.g., `dgrsyrtupqpmqgxsqcsp`)

### 2. Supabase Configuration

**In Supabase Dashboard:**

1. Go to: Authentication → Providers → Google
2. Enable Google provider
3. Add your Google OAuth credentials:
   - Client ID (from Google Cloud Console)
   - Client Secret (from Google Cloud Console)
4. Go to: Authentication → URL Configuration
5. Set **Site URL**: `http://localhost:8501`
6. Add to **Redirect URLs**:
   ```
   http://localhost:8501
   http://localhost:8501/**
   ```

### 3. Environment Variables

Make sure your `.env` file has:
```env
SUPABASE_URL=https://YOUR-PROJECT-REF.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key-here
```

Find these keys in: Supabase Dashboard → Settings → API

### 4. OAuth Consent Screen

**In Google Cloud Console:**
- Go to: APIs & Services → OAuth consent screen
- If in "Testing" mode, add your email to "Test users"
- Or publish the app (for production)

## Testing the Fix

1. Restart your containers:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

2. Clear browser cache or use incognito mode

3. Go to `http://localhost:8501`

4. Click "Sign in with Google"

5. You should be redirected to Google, then back to your app successfully

## Common Issues

### Issue: "Access blocked: This app's request is invalid"
**Solution**: Check that redirect URIs in Google Console exactly match Supabase callback URL

### Issue: "redirect_uri_mismatch"
**Solution**: The redirect URI in your request doesn't match any authorized redirect URIs in Google Console

### Issue: Session expires immediately
**Solution**: Check that `SUPABASE_ANON_KEY` is the anon/public key, not the service role key

## Code Changes Made

1. **Simplified OAuth flow** - Removed complex PKCE implementation that was causing session state issues
2. **Added error logging** - Better visibility into what's failing
3. **Improved error handling** - Clear error messages for debugging

## Next Steps After OAuth Works

Once authentication is working, you can:
1. Test voice recording feature
2. Upload audio files
3. See transcriptions with detected language (Hindi/English/Hinglish)
4. View extracted business data
5. Access the ledger system

## Need Help?

If OAuth still doesn't work:
1. Check browser console for errors (F12)
2. Check backend logs: `docker logs voicetrace-backend`
3. Check frontend logs: `docker logs voicetrace-streamlit`
4. Verify all redirect URIs match exactly (no trailing slashes, correct protocol)
