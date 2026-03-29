/**
 * VoiceTrace AI — Centralized API Configuration
 *
 * All values come from the expo-app/.env file.
 * Expo requires the EXPO_PUBLIC_ prefix for any variable
 * that should be accessible in client-side (JS) code.
 *
 * Never put secret keys (service_role, private VAPI key, AWS secret)
 * here — those belong only in the backend .env.
 */

// ── Backend (ngrok tunnel → FastAPI) ─────────────────────────────────
export const BACKEND_URL =
  process.env.EXPO_PUBLIC_BACKEND_URL ?? 'https://ba02-32-192-28-123.ngrok-free.app';

// ── Supabase ─────────────────────────────────────────────────────────
export const SUPABASE_URL =
  process.env.EXPO_PUBLIC_SUPABASE_URL ?? 'https://dgrsyrtupqpmqgxsqcsp.supabase.co';

export const SUPABASE_ANON_KEY =
  process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? '';

// ── VAPI ─────────────────────────────────────────────────────────────
// Public key from https://vapi.ai/dashboard → API Keys (safe for client)
export const VAPI_PUBLIC_KEY =
  process.env.EXPO_PUBLIC_VAPI_PUBLIC_KEY ?? '0ff4c6e2-f522-4e5a-8c05-e2b934fdaeef';

export const VAPI_ASSISTANT_ID =
  process.env.EXPO_PUBLIC_VAPI_ASSISTANT_ID ?? 'a95d9e0c-c4cd-4ebb-ada5-61dc5e741cfa';

// ── VAPI webhook endpoints (routers/vapi.py on the backend) ──────────
export const VAPI_SESSION_START_URL = `${BACKEND_URL}/vapi/session/start`;
export const VAPI_WEBHOOK_CALL_START = `${BACKEND_URL}/vapi/webhook/call-start`;
export const VAPI_WEBHOOK_CALL_END   = `${BACKEND_URL}/vapi/webhook/call-end`;
export const VAPI_WEBHOOK_MESSAGE    = `${BACKEND_URL}/vapi/webhook/message`;
