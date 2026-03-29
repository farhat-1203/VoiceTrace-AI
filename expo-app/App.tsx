/**
 * VoiceTrace AI — App Entry Point
 *
 * Auth flow:
 *  1. App boots → check persisted Supabase session (SecureStore).
 *  2. If session exists → show MainTabNavigator.
 *  3. If not → show SignInScreen.
 *  4. onAuthStateChange keeps the session in sync throughout the session.
 */
import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { View, ActivityIndicator } from 'react-native';
import type { Session } from '@supabase/supabase-js';

import { supabase } from './src/services/supabaseClient';
import MainTabNavigator from './src/navigation/MainTabNavigator';
import SignInScreen from './src/screens/SignInScreen';

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // ── 1. Restore persisted session on boot ─────────────────────────
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // ── 2. Subscribe to auth changes (sign in / sign out / refresh) ──
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    // Show a full-screen green spinner while checking persisted session
    return (
      <View
        style={{ flex: 1, backgroundColor: '#0F761B', alignItems: 'center', justifyContent: 'center' }}
      >
        <ActivityIndicator size="large" color="#fff" />
      </View>
    );
  }

  if (!session) {
    return <SignInScreen onSignIn={(s) => setSession(s)} />;
  }

  return (
    <NavigationContainer>
      <MainTabNavigator
        session={session}
        onSignOut={() => {
          supabase.auth.signOut();
          setSession(null);
        }}
      />
    </NavigationContainer>
  );
}
