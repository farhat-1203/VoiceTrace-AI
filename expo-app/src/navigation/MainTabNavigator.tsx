import React from 'react';
import { View, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons, Ionicons } from '@expo/vector-icons';
import type { Session } from '@supabase/supabase-js';

import HomeScreen from '../screens/HomeScreen';
import LedgerScreen from '../screens/LedgerScreen';
import InsightsScreen from '../screens/InsightsScreen';
import ReportScreen from '../screens/ReportScreen';

const Tab = createBottomTabNavigator();

interface Props {
  session: Session;
  onSignOut: () => void;
}

export default function MainTabNavigator({ session, onSignOut }: Props) {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#FFF',
          borderTopWidth: 1,
          borderTopColor: '#EFEFEF',
          height: 100,
          paddingBottom: 25,
          paddingTop: 10,
        },
        tabBarActiveTintColor: '#10A150',
        tabBarInactiveTintColor: '#7E8A9A',
      }}
    >
      <Tab.Screen
        name="Home"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <View className={`items-center justify-center ${focused ? 'w-[44px] h-[44px] rounded-full bg-[#EAF9F0]' : ''}`}>
              <MaterialCommunityIcons name="microphone-outline" size={24} color={color} />
            </View>
          ),
          tabBarLabel: ({ focused }) => (
            <Text className={`text-[12px] mt-1 ${focused ? 'font-bold text-[#10A150]' : 'font-semibold text-[#7E8A9A]'}`}>Home</Text>
          ),
        }}
      >
        {() => <HomeScreen session={session} onSignOut={onSignOut} />}
      </Tab.Screen>
      <Tab.Screen
        name="Ledger"
        options={{
          tabBarIcon: ({ color, focused }) => (
            <View className={`items-center justify-center ${focused ? 'w-[44px] h-[44px] rounded-full bg-[#EAF9F0]' : ''}`}>
              <Ionicons name="book-outline" size={24} color={color} />
            </View>
          ),
          tabBarLabel: ({ focused }) => (
            <Text className={`text-[12px] mt-1 ${focused ? 'font-bold text-[#10A150]' : 'font-semibold text-[#7E8A9A]'}`}>Ledger</Text>
          ),
        }}
      >
        {() => <LedgerScreen />}
      </Tab.Screen>
      <Tab.Screen
        name="Insights"
        component={InsightsScreen}
        options={{
          tabBarIcon: ({ color, focused }) => (
            <View className={`items-center justify-center ${focused ? 'w-[44px] h-[44px] rounded-full bg-[#EAF9F0]' : ''}`}>
              <MaterialCommunityIcons name="chart-line" size={24} color={color} />
            </View>
          ),
          tabBarLabel: ({ focused }) => (
            <Text className={`text-[12px] mt-1 ${focused ? 'font-bold text-[#10A150]' : 'font-semibold text-[#7E8A9A]'}`}>Insights</Text>
          ),
        }}
      />
      <Tab.Screen
        name="Report"
        component={ReportScreen}
        options={{
          tabBarIcon: ({ color, focused }) => (
            <View className={`items-center justify-center ${focused ? 'w-[44px] h-[44px] rounded-full bg-[#EAF9F0]' : ''}`}>
              <Ionicons name="document-text-outline" size={24} color={color} />
            </View>
          ),
          tabBarLabel: ({ focused }) => (
            <Text className={`text-[12px] mt-1 ${focused ? 'font-bold text-[#10A150]' : 'font-semibold text-[#7E8A9A]'}`}>Report</Text>
          ),
        }}
      />
    </Tab.Navigator>
  );
}
