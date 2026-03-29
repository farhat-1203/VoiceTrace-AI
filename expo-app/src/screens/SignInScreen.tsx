/**
 * VoiceTrace AI — Sign In / Sign Up Screen
 *
 * Real Supabase email + password authentication.
 * Toggles between "Sign In" and "Create Account" modes.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  SafeAreaView,
  TouchableOpacity,
  TextInput,
  StatusBar,
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import type { Session } from '@supabase/supabase-js';
import { signIn, signUp } from '../services/supabaseClient';

interface Props {
  onSignIn: (session: Session) => void;
}

export default function SignInScreen({ onSignIn }: Props) {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Missing fields', 'Please enter your email and password.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signin') {
        const { data, error } = await signIn(email.trim(), password);
        if (error) throw error;
        if (data.session) onSignIn(data.session);
      } else {
        const { data, error } = await signUp(email.trim(), password);
        if (error) throw error;
        if (data.session) {
          onSignIn(data.session);
        } else {
          Alert.alert(
            'Account Created',
            'Please check your email to confirm your account, then sign in.',
          );
          setMode('signin');
        }
      }
    } catch (err: any) {
      Alert.alert(
        mode === 'signin' ? 'Sign In Failed' : 'Sign Up Failed',
        err.message || 'Something went wrong. Please try again.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#fff' }}>
      <StatusBar barStyle="dark-content" />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1 }}
          keyboardShouldPersistTaps="handled"
        >
          <View style={{ flex: 1, paddingHorizontal: 32, justifyContent: 'center', paddingTop: 60 }}>

            {/* ── Logo / Brand ──────────────────────────────────── */}
            <View style={{ alignItems: 'center', marginBottom: 48 }}>
              {/* Concentric circles with waveform icon */}
              <View style={{ position: 'relative', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
                <View style={{ width: 200, height: 200, borderRadius: 100, backgroundColor: '#E6F3E6', position: 'absolute' }} />
                <View style={{ width: 155, height: 155, borderRadius: 78, backgroundColor: '#CDE5CD', position: 'absolute' }} />
                <View style={{
                  width: 110, height: 110, borderRadius: 55,
                  backgroundColor: '#0F761B',
                  alignItems: 'center', justifyContent: 'center',
                  shadowColor: '#0F761B', shadowOpacity: 0.4, shadowRadius: 16, elevation: 8,
                }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {[10, 20, 32, 20, 32, 20, 10].map((h, i) => (
                      <View key={i} style={{
                        width: 5, height: h, borderRadius: 3,
                        backgroundColor: '#FFF', marginHorizontal: 2.5,
                      }} />
                    ))}
                  </View>
                </View>
              </View>

              <Text style={{ fontSize: 36, fontWeight: '900', color: '#101828', letterSpacing: -0.5 }}>
                VoiceTrace
              </Text>
              <Text style={{ fontSize: 18, fontWeight: '700', color: '#0F761B', marginTop: 4 }}>
                Speak. Track. Grow.
              </Text>
              <Text style={{ fontSize: 14, color: '#667085', marginTop: 8, textAlign: 'center', lineHeight: 20 }}>
                Record your daily sales in Hindi or Hinglish{'\n'}without ever typing.
              </Text>
            </View>

            {/* ── Mode Toggle ───────────────────────────────────── */}
            <View style={{
              flexDirection: 'row', backgroundColor: '#F3F4F6',
              borderRadius: 12, padding: 4, marginBottom: 28,
            }}>
              {(['signin', 'signup'] as const).map((m) => (
                <TouchableOpacity
                  key={m}
                  onPress={() => setMode(m)}
                  style={{
                    flex: 1, paddingVertical: 10, borderRadius: 10,
                    backgroundColor: mode === m ? '#fff' : 'transparent',
                    alignItems: 'center',
                    shadowColor: mode === m ? '#000' : 'transparent',
                    shadowOpacity: mode === m ? 0.06 : 0,
                    shadowRadius: 4, elevation: mode === m ? 2 : 0,
                  }}
                >
                  <Text style={{
                    fontWeight: '700', fontSize: 14,
                    color: mode === m ? '#101828' : '#6B7280',
                  }}>
                    {m === 'signin' ? 'Sign In' : 'Create Account'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* ── Email Input ───────────────────────────────────── */}
            <View style={{ marginBottom: 14 }}>
              <Text style={{ fontSize: 13, fontWeight: '600', color: '#374151', marginBottom: 6 }}>
                Email
              </Text>
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                placeholderTextColor="#9CA3AF"
                keyboardType="email-address"
                autoCapitalize="none"
                autoComplete="email"
                style={{
                  borderWidth: 1.5, borderColor: '#E5E7EB',
                  borderRadius: 14, paddingHorizontal: 16, paddingVertical: 14,
                  fontSize: 15, color: '#101828', backgroundColor: '#FAFAFA',
                }}
              />
            </View>

            {/* ── Password Input ────────────────────────────────── */}
            <View style={{ marginBottom: 28 }}>
              <Text style={{ fontSize: 13, fontWeight: '600', color: '#374151', marginBottom: 6 }}>
                Password
              </Text>
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder={mode === 'signup' ? 'Min. 6 characters' : '••••••••'}
                placeholderTextColor="#9CA3AF"
                secureTextEntry
                autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
                style={{
                  borderWidth: 1.5, borderColor: '#E5E7EB',
                  borderRadius: 14, paddingHorizontal: 16, paddingVertical: 14,
                  fontSize: 15, color: '#101828', backgroundColor: '#FAFAFA',
                }}
              />
            </View>

            {/* ── Submit Button ─────────────────────────────────── */}
            <TouchableOpacity
              onPress={handleAuth}
              disabled={loading}
              activeOpacity={0.85}
              style={{
                backgroundColor: '#0F761B',
                borderRadius: 16, paddingVertical: 16,
                alignItems: 'center', justifyContent: 'center',
                shadowColor: '#0F761B', shadowOpacity: 0.35,
                shadowRadius: 12, elevation: 6,
              }}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={{ color: '#fff', fontSize: 16, fontWeight: '800' }}>
                  {mode === 'signin' ? 'Sign In' : 'Create Account'}
                </Text>
              )}
            </TouchableOpacity>

            {/* ── Legal ─────────────────────────────────────────── */}
            <Text style={{ textAlign: 'center', fontSize: 11, color: '#9CA3AF', marginTop: 20, lineHeight: 16 }}>
              By continuing, you agree to our{' '}
              <Text style={{ color: '#6B7280', fontWeight: '700' }}>Terms of Service</Text>
              {' '}and{' '}
              <Text style={{ color: '#6B7280', fontWeight: '700' }}>Privacy Policy</Text>
            </Text>

          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}