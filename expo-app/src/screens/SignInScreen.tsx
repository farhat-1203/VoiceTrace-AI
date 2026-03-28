import React from 'react';
import { View, Text, SafeAreaView, TouchableOpacity, Image, StatusBar } from 'react-native';

export default function SignInScreen({ onSignIn }: { onSignIn: () => void }) {
  return (
    <SafeAreaView className="flex-1 bg-white mt-40">
      <StatusBar barStyle="dark-content" />
      <View className="flex-1 px-8 justify-center">
        
        {/* Main Content Container - Centered on screen */}
        <View className="items-center mb-12">
          
          {/* Visual Icon */}
          <View className="relative items-center justify-center mb-10">
            <View className="w-60 h-60 rounded-full bg-[#E6F3E6] absolute" />
            <View className="w-44 h-44 rounded-full bg-[#CDE5CD] absolute" />
            <View className="w-28 h-28 rounded-full bg-[#0F761B] items-center justify-center shadow-xl shadow-green-200">
               {/* Minimalist Mic Graphic */}
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

          {/* Branding & Tagline Grouped */}
          <Text className="text-4xl font-black tracking-tight text-slate-900 mb-2 mt-8">
            VoiceTrace
          </Text>
          <Text className="text-xl font-bold text-green-800">
            Speak. Track. Grow.
          </Text>
          <Text className="text-[15px] leading-6 text-slate-500 mt-4 text-center px-6">
            Record your daily sales in Hindi or Hinglish without ever typing.
          </Text>
        </View>

        {/* Action Section - Moved slightly up from the bottom */}
        <View className="w-full mt-4">
          <TouchableOpacity
            onPress={onSignIn}
            activeOpacity={0.8}
            className="flex-row items-center justify-center bg-white border border-slate-200 rounded-2xl py-4 shadow-sm active:bg-slate-50"
          >
            <Image 
              source={require('../assets/googleicon.png')} 
              style={{ width: 22, height: 22 }}
              resizeMode="contain"
            />
            <Text className="text-lg font-semibold text-slate-700 ml-4">
              Continue with Google
            </Text>
          </TouchableOpacity>
          
          <Text className="text-center text-[11px] text-slate-400 mt-5 px-10 leading-4">
            By continuing, you agree to our 
            <Text className="text-slate-500 font-bold"> Terms of Service </Text> 
            and 
            <Text className="text-slate-500 font-bold"> Privacy Policy</Text>
          </Text>
        </View>

      </View>
    </SafeAreaView>
  );
}