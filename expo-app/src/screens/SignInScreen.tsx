import React, { useState } from 'react';
import { View, Text, SafeAreaView, TouchableOpacity, StatusBar, TextInput, Alert, ActivityIndicator, KeyboardAvoidingView, ScrollView, Platform } from 'react-native';
import { supabase } from '../lib/supabase';

export default function SignInScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSignUp, setIsSignUp] = useState(false);

  async function signInWithEmail() {
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) Alert.alert('Error', error.message);
    setLoading(false);
  }

  async function signUpWithEmail() {
    setLoading(true);
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
    });

    if (error) Alert.alert('Error', error.message);
    else if (!data?.session) Alert.alert('Success', 'Please check your inbox for email verification!');
    setLoading(false);
  }

  return (
    <SafeAreaView className="flex-1 bg-white">
      <StatusBar barStyle="dark-content" />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', paddingHorizontal: 32, paddingBottom: 40 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Main Content Container */}
          <View className="items-center mb-10">
            
            {/* Visual Icon */}
            <View className="relative items-center justify-center mb-6 mt-4">
              <View className="w-40 h-40 rounded-full bg-[#E6F3E6] absolute" />
              <View className="w-28 h-28 rounded-full bg-[#CDE5CD] absolute" />
              <View className="w-16 h-16 rounded-full bg-[#0F761B] items-center justify-center shadow-xl shadow-green-200">
                 {/* Minimalist Mic Graphic */}
                 <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                     {[6, 12, 20, 12, 20, 12, 6].map((h, i) => (
                       <View key={i} style={{
                         width: 3, height: h, borderRadius: 2,
                         backgroundColor: '#FFF', marginHorizontal: 1.5,
                       }} />
                     ))}
                   </View>
              </View>
            </View>

            {/* Branding & Tagline */}
            <Text className="text-3xl font-black tracking-tight text-slate-900 mb-1 mt-6">
              VoiceTrace
            </Text>
            <Text className="text-lg font-bold text-green-800">
              Speak. Track. Grow.
            </Text>
          </View>

          {/* Action Section */}
          <View className="w-full">
            
            <View className="mb-4">
              <Text className="text-slate-600 font-semibold mb-2 ml-1">Email</Text>
              <TextInput
                onChangeText={(text) => setEmail(text)}
                value={email}
                placeholder="email@address.com"
                autoCapitalize={'none'}
                autoCorrect={false}
                keyboardType="email-address"
                returnKeyType="next"
                className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-800"
              />
            </View>

            <View className="mb-6">
              <Text className="text-slate-600 font-semibold mb-2 ml-1">Password</Text>
              <TextInput
                onChangeText={(text) => setPassword(text)}
                value={password}
                secureTextEntry={true}
                placeholder="Password"
                autoCapitalize={'none'}
                returnKeyType="done"
                onSubmitEditing={isSignUp ? signUpWithEmail : signInWithEmail}
                className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-slate-800"
              />
            </View>

            <TouchableOpacity
              onPress={isSignUp ? signUpWithEmail : signInWithEmail}
              disabled={loading}
              activeOpacity={0.8}
              className={`w-full items-center justify-center rounded-2xl py-4 shadow-sm ${loading ? 'bg-[#0F761B]/70' : 'bg-[#0F761B]'}`}
            >
              {loading ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <Text className="text-lg font-bold text-white">
                  {isSignUp ? 'Create Account' : 'Sign In'}
                </Text>
              )}
            </TouchableOpacity>
            
            <View className="flex-row justify-center mt-6">
              <Text className="text-slate-500">
                {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
              </Text>
              <TouchableOpacity onPress={() => setIsSignUp(!isSignUp)}>
                <Text className="text-[#0F761B] font-bold">
                  {isSignUp ? 'Sign In' : 'Sign Up'}
                </Text>
              </TouchableOpacity>
            </View>

          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}