import React from 'react';
import { View, Text, SafeAreaView, ScrollView, StatusBar } from 'react-native';
import { Feather, MaterialCommunityIcons } from '@expo/vector-icons';

const insights = [
  {
    id: 1,
    icon: <Feather name="trending-up" size={22} color="#10A150" />,
    bg: 'bg-[#EAF9F0]',
    titleColor: 'text-[#10A150]',
    title: 'Best Seller',
    body: 'Chai is your top product with 590 units sold.',
  },
  {
    id: 2,
    icon: <MaterialCommunityIcons name="cart-outline" size={22} color="#7C3AED" />,
    bg: 'bg-[#F3EEFF]',
    titleColor: 'text-[#7C3AED]',
    title: 'Stock Suggestion',
    body: "Stock up on chai — it's consistently your fastest-moving product.",
  },
];

export default function InsightsScreen() {
  return (
    <SafeAreaView className="flex-1 bg-[#F9F9F4] pt-8">
      <StatusBar barStyle="dark-content" backgroundColor="#F9F9F4" />
      <View className="pt-8 px-5 pb-4">
        <Text className="text-[11px] font-bold text-[#8C867B] tracking-widest mb-1">BUSINESS INTELLIGENCE</Text>
        <Text className="text-[28px] font-black text-[#101828]">Insights</Text>
      </View>
      <View className="h-[1px] bg-[#E5E5E5] mx-5 mb-5" />

      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
        {insights.map((item) => (
          <View key={item.id} className={`${item.bg} rounded-[20px] p-5 mb-4 flex-row items-start`}>
            <View className="mr-4 mt-0.5">{item.icon}</View>
            <View className="flex-1">
              <Text className={`text-[15px] font-black mb-1 ${item.titleColor}`}>{item.title}</Text>
              <Text className="text-[14px] text-[#3D3D3D] font-medium leading-5">{item.body}</Text>
            </View>
          </View>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}
