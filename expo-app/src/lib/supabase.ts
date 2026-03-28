import * as SecureStore from 'expo-secure-store';
import { createClient } from '@supabase/supabase-js';

// SecureStore-backed synchronous-style adapter for Supabase auth.
// Supabase auth-js calls setItem/removeItem fire-and-forget and
// calls getItem expecting a string | null (or a promise).
const ExpoSecureStoreAdapter = {
  getItem: (key: string): Promise<string | null> => {
    return SecureStore.getItemAsync(key);
  },
  setItem: (key: string, value: string): void => {
    SecureStore.setItemAsync(key, value).catch(console.error);
  },
  removeItem: (key: string): void => {
    SecureStore.deleteItemAsync(key).catch(console.error);
  },
};

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_KEY || '';

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: ExpoSecureStoreAdapter,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
