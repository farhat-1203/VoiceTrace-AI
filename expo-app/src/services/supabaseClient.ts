/**
 * VoiceTrace AI — Supabase Client
 *
 * Provides:
 *  - Supabase JS client (browser/native compatible)
 *  - Email/password auth helpers
 *  - Session persistence via expo-secure-store
 */
import 'react-native-url-polyfill/auto';
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';
import { SUPABASE_URL, SUPABASE_ANON_KEY } from '../config/api';

// ── Secure Storage Adapter for Supabase session persistence ──────────
const ExpoSecureStoreAdapter = {
  getItem: (key: string) => SecureStore.getItemAsync(key),
  setItem: (key: string, value: string) => SecureStore.setItemAsync(key, value),
  removeItem: (key: string) => SecureStore.deleteItemAsync(key),
};

// ── Supabase Client ───────────────────────────────────────────────────
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: ExpoSecureStoreAdapter as any,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});

// ── Auth Helpers ──────────────────────────────────────────────────────

/**
 * Sign up with email and password.
 * Returns { data, error }.
 */
export async function signUp(email: string, password: string) {
  return supabase.auth.signUp({ email, password });
}

/**
 * Sign in with email and password.
 * Returns { data, error } — data.session contains the JWT access_token.
 */
export async function signIn(email: string, password: string) {
  return supabase.auth.signInWithPassword({ email, password });
}

/**
 * Sign out the current user.
 */
export async function signOut() {
  return supabase.auth.signOut();
}

/**
 * Get the current active session.
 * Returns the session object or null.
 */
export async function getSession() {
  const { data } = await supabase.auth.getSession();
  return data.session;
}

/**
 * Get just the access token (JWT) for Authorization headers.
 * Returns empty string if not signed in.
 */
export async function getAccessToken(): Promise<string> {
  const session = await getSession();
  return session?.access_token ?? '';
}
