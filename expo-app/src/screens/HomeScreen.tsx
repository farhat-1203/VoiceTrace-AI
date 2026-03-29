import React, { useState } from 'react';
import { Text, View, SafeAreaView, TouchableOpacity, ScrollView, StatusBar, Alert } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import type { Session } from '@supabase/supabase-js';
import RecordingScreen from './RecordingScreen';

interface Props {
  session: Session;
  onSignOut: () => void;
}

export default function HomeScreen({ session, onSignOut }: Props) {
  const [recordingVisible, setRecordingVisible] = useState(false);

  // Resolve display name from session metadata (set during sign-up / Google OAuth)
  const fullName: string =
    session.user?.user_metadata?.full_name ||
    session.user?.user_metadata?.name ||
    session.user?.email?.split('@')[0] ||
    'User';
  const firstName = fullName.split(' ')[0];

  const greeting = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Good Morning';
    if (h < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const todayLabel = new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  });

  const handleNamePress = () => {
    Alert.alert(
      firstName,
      `Signed in as ${session.user.email}`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Log Out', style: 'destructive', onPress: onSignOut },
      ]
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-[#F9F9F4] pt-8">
      <StatusBar barStyle="dark-content" backgroundColor="#F9F9F4" />
      <RecordingScreen
        visible={recordingVisible}
        onClose={() => setRecordingVisible(false)}
        session={session}
      />
      <View className="flex-1">
        <ScrollView
          contentContainerStyle={{ paddingHorizontal: 20, paddingTop: 30, paddingBottom: 40 }}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View className="mb-10 px-1">
            <Text className="text-[12px] font-bold text-[#8C867B] tracking-[2px] mb-3 uppercase">
              {todayLabel}
            </Text>
            <View className="flex-row items-baseline">
              <Text className="text-[28px] font-black text-slate-900">
                {greeting()},{' '}
              </Text>
              <TouchableOpacity onPress={handleNamePress} activeOpacity={0.7}>
                <Text className="text-[28px] font-black text-emerald-700">
                  {firstName}
                </Text>
              </TouchableOpacity>
            </View>
            <Text className="text-base text-slate-500 font-medium mt-1">
              What did you sell today?
            </Text>
          </View>

          {/* Mic Section */}
          <View className="items-center mb-5">
            <View className="w-[220px] h-[220px] rounded-full bg-[#E6F3E6] justify-center items-center">
              <View className="w-[170px] h-[170px] rounded-full bg-[#CDE5CD] justify-center items-center">
                <TouchableOpacity
                  onPress={() => setRecordingVisible(true)}
                  className="w-[120px] h-[120px] rounded-full bg-[#0F761B] justify-center items-center shadow-lg active:opacity-80"
                >
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {[10, 20, 32, 20, 32, 20, 10].map((h, i) => (
                      <View key={i} style={{
                        width: 5, height: h, borderRadius: 3,
                        backgroundColor: '#FFF', marginHorizontal: 2.5,
                      }} />
                    ))}
                  </View>
                </TouchableOpacity>
              </View>
            </View>
            <Text className="text-xl font-extrabold text-[#101828] mt-4 mb-1.5">Tap to Record</Text>
            <Text className="text-[15px] text-[#667085] font-medium">Speak in Hindi / Hinglish</Text>
          </View>

          {/* Transcript Sample */}
          <View className="bg-[#E3F0E5] rounded-2xl py-4 px-5 mt-5 mb-4 border border-[#CDE5CD]">
            <Text className="text-sm text-[#207233] font-bold text-center leading-6">
              "Aaj maine 50 chai becha 10 rupees each.{'\n'}Milk kharida 200 rupees ka."
            </Text>
          </View>

          <View className="h-[1px] bg-[#E5E5E5] mb-8" />

          {/* Summary */}
          <View className="flex-row justify-between items-center mb-4">
            <Text className="text-lg font-extrabold text-[#101828]">Today's Summary</Text>
            <Text className="text-sm text-[#667085] font-medium">1 entry</Text>
          </View>

          <View className="flex-row justify-between">
            <View className="flex-1 rounded-2xl bg-[#EAF9F0] py-4 px-3 items-center mx-1">
              <Feather name="trending-up" size={18} color="#10A150" />
              <Text className="text-[22px] font-black mt-1.5 mb-1 text-[#10A150]">₹800</Text>
              <Text className="text-[11px] font-bold tracking-wider text-[#8B9B90]">EARNED</Text>
            </View>
            <View className="flex-1 rounded-2xl bg-[#FFF2F4] py-4 px-3 items-center mx-1">
              <Feather name="trending-down" size={18} color="#E73550" />
              <Text className="text-[22px] font-black mt-1.5 mb-1 text-[#E73550]">₹200</Text>
              <Text className="text-[11px] font-bold tracking-wider text-[#B09C9F]">SPENT</Text>
            </View>
            <View className="flex-1 rounded-2xl bg-[#F3F1E9] py-4 px-3 items-center mx-1">
              <Ionicons name="wallet-outline" size={18} color="#1A2024" />
              <Text className="text-[22px] font-black mt-1.5 mb-1 text-[#1A2024]">₹600</Text>
              <Text className="text-[11px] font-bold tracking-wider text-[#8C867B]">BALANCE</Text>
            </View>
          </View>

        </ScrollView>
      </View>
    </SafeAreaView>
  );
}
