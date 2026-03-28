import React, { useState } from 'react';
import { View, Text, SafeAreaView, ScrollView, StatusBar, TouchableOpacity } from 'react-native';
import { Feather, Ionicons } from '@expo/vector-icons';
import DateFilterSheet, { DateRange } from '../components/DateFilterSheet';

type ReportData = {
  totalEarned: string;
  totalSpent: string;
  netProfit: string;
  totalEntries: number;
  avgDaily: string;
  topItems: { rank: number; name: string; units: string; amount: string }[];
};

const REPORT_BY_FILTER: Record<string, ReportData> = {
  today: {
    totalEarned: '₹920', totalSpent: '₹350', netProfit: '₹570',
    totalEntries: 1, avgDaily: '₹920',
    topItems: [
      { rank: 1, name: 'Chai', units: '38 units sold', amount: '₹380' },
      { rank: 2, name: 'Samosa', units: '28 units sold', amount: '₹420' },
      { rank: 3, name: 'Water', units: '12 units sold', amount: '₹120' },
    ],
  },
  yesterday: {
    totalEarned: '₹1,070', totalSpent: '₹310', netProfit: '₹760',
    totalEntries: 1, avgDaily: '₹1,070',
    topItems: [
      { rank: 1, name: 'Chai', units: '120 units sold', amount: '₹1,200' },
      { rank: 2, name: 'Samosa', units: '60 units sold', amount: '₹900' },
      { rank: 3, name: 'Vada Pav', units: '50 units sold', amount: '₹600' },
    ],
  },
  last7: {
    totalEarned: '₹11,675', totalSpent: '₹2,330', netProfit: '₹9,345',
    totalEntries: 7, avgDaily: '₹1,668',
    topItems: [
      { rank: 1, name: 'Chai', units: '590 units sold', amount: '₹5,900' },
      { rank: 2, name: 'Samosa', units: '285 units sold', amount: '₹4,275' },
      { rank: 3, name: 'Vada Pav', units: '125 units sold', amount: '₹1,500' },
    ],
  },
  thisMonth: {
    totalEarned: '₹38,500', totalSpent: '₹11,200', netProfit: '₹27,300',
    totalEntries: 22, avgDaily: '₹1,750',
    topItems: [
      { rank: 1, name: 'Chai', units: '2,100 units sold', amount: '₹21,000' },
      { rank: 2, name: 'Samosa', units: '850 units sold', amount: '₹12,750' },
      { rank: 3, name: 'Vada Pav', units: '390 units sold', amount: '₹4,680' },
    ],
  },
  lastMonth: {
    totalEarned: '₹35,200', totalSpent: '₹10,500', netProfit: '₹24,700',
    totalEntries: 28, avgDaily: '₹1,257',
    topItems: [
      { rank: 1, name: 'Chai', units: '1,900 units sold', amount: '₹19,000' },
      { rank: 2, name: 'Samosa', units: '780 units sold', amount: '₹11,700' },
      { rank: 3, name: 'Vada Pav', units: '290 units sold', amount: '₹3,480' },
    ],
  },
  past6months: {
    totalEarned: '₹2,10,000', totalSpent: '₹63,000', netProfit: '₹1,47,000',
    totalEntries: 168, avgDaily: '₹1,250',
    topItems: [
      { rank: 1, name: 'Chai', units: '11,500 units sold', amount: '₹1,15,000' },
      { rank: 2, name: 'Samosa', units: '4,800 units sold', amount: '₹72,000' },
      { rank: 3, name: 'Vada Pav', units: '1,900 units sold', amount: '₹22,800' },
    ],
  },
  thisYear: {
    totalEarned: '₹75,500', totalSpent: '₹22,500', netProfit: '₹53,000',
    totalEntries: 87, avgDaily: '₹868',
    topItems: [
      { rank: 1, name: 'Chai', units: '7,550 units sold', amount: '₹75,500' },
      { rank: 2, name: 'Samosa', units: '3,200 units sold', amount: '₹48,000' },
      { rank: 3, name: 'Vada Pav', units: '1,200 units sold', amount: '₹14,400' },
    ],
  },
  lifetime: {
    totalEarned: '₹3,15,500', totalSpent: '₹94,500', netProfit: '₹2,21,000',
    totalEntries: 365, avgDaily: '₹864',
    topItems: [
      { rank: 1, name: 'Chai', units: '31,550 units sold', amount: '₹3,15,500' },
      { rank: 2, name: 'Samosa', units: '12,800 units sold', amount: '₹1,92,000' },
      { rank: 3, name: 'Vada Pav', units: '5,200 units sold', amount: '₹62,400' },
    ],
  },
  custom: {
    totalEarned: '₹3,450', totalSpent: '₹980', netProfit: '₹2,470',
    totalEntries: 3, avgDaily: '₹1,150',
    topItems: [
      { rank: 1, name: 'Chai', units: '345 units sold', amount: '₹3,450' },
      { rank: 2, name: 'Samosa', units: '120 units sold', amount: '₹1,800' },
      { rank: 3, name: 'Vada Pav', units: '55 units sold', amount: '₹660' },
    ],
  },
};

function getDefaultRange(): DateRange {
  const today = new Date();
  return { filter: 'last7', label: 'Last 7 Days', from: new Date(today.getFullYear(), today.getMonth(), today.getDate() - 6), to: today };
}

export default function ReportScreen() {
  const [dateRange, setDateRange] = useState<DateRange>(getDefaultRange());
  const report = REPORT_BY_FILTER[dateRange.filter] ?? REPORT_BY_FILTER['last7'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9F9F4', paddingTop: 32 }}>
      <StatusBar barStyle="dark-content" backgroundColor="#F9F9F4" />
      <View style={{ paddingTop: 32, paddingHorizontal: 20, paddingBottom: 16 }}>
        <Text style={{ fontSize: 11, fontWeight: '700', color: '#8C867B', letterSpacing: 2, marginBottom: 4 }}>FINANCIAL SUMMARY</Text>
        <Text style={{ fontSize: 28, fontWeight: '900', color: '#101828' }}>Report</Text>
      </View>
      <View style={{ height: 1, backgroundColor: '#E5E5E5', marginHorizontal: 20, marginBottom: 20 }} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }} showsVerticalScrollIndicator={false}>

        {/* Overall Summary */}
        <View style={{ backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: '#EBEBEB' }}>
          <Text style={{ fontSize: 10, fontWeight: '700', color: '#8C867B', letterSpacing: 2, marginBottom: 16 }}>OVERALL SUMMARY</Text>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
            <View style={{ alignItems: 'center', flex: 1 }}>
              <Feather name="trending-up" size={18} color="#10A150" />
              <Text style={{ fontSize: 20, fontWeight: '900', color: '#10A150', marginTop: 4 }}>{report.totalEarned}</Text>
              <Text style={{ fontSize: 9, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginTop: 2 }}>TOTAL EARNED</Text>
            </View>
            <View style={{ width: 1, backgroundColor: '#EBEBEB' }} />
            <View style={{ alignItems: 'center', flex: 1 }}>
              <Feather name="trending-down" size={18} color="#E73550" />
              <Text style={{ fontSize: 20, fontWeight: '900', color: '#E73550', marginTop: 4 }}>{report.totalSpent}</Text>
              <Text style={{ fontSize: 9, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginTop: 2 }}>TOTAL SPENT</Text>
            </View>
            <View style={{ width: 1, backgroundColor: '#EBEBEB' }} />
            <View style={{ alignItems: 'center', flex: 1 }}>
              <Ionicons name="wallet-outline" size={18} color="#1A2024" />
              <Text style={{ fontSize: 20, fontWeight: '900', color: '#1A2024', marginTop: 4 }}>{report.netProfit}</Text>
              <Text style={{ fontSize: 9, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginTop: 2 }}>NET PROFIT</Text>
            </View>
          </View>
        </View>

        {/* Entries & Avg */}
        <View style={{ flexDirection: 'row', marginBottom: 16, gap: 12 }}>
          <View style={{ flex: 1, backgroundColor: '#fff', borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#EBEBEB', alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ fontSize: 40, fontWeight: '900', color: '#10A150' }}>{report.totalEntries}</Text>
            <Text style={{ fontSize: 10, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginTop: 4 }}>TOTAL ENTRIES</Text>
          </View>
          <View style={{ flex: 1, backgroundColor: '#fff', borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#EBEBEB', alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ fontSize: 28, fontWeight: '900', color: '#101828' }}>{report.avgDaily}</Text>
            <Text style={{ fontSize: 10, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginTop: 4, textAlign: 'center' }}>AVG DAILY{'\n'}EARNING</Text>
          </View>
        </View>

        {/* Top Items */}
        <View style={{ backgroundColor: '#fff', borderRadius: 20, padding: 20, marginBottom: 24, borderWidth: 1, borderColor: '#EBEBEB' }}>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 16 }}>
            <Ionicons name="cube-outline" size={14} color="#8C867B" />
            <Text style={{ fontSize: 10, fontWeight: '700', color: '#8C867B', letterSpacing: 1, marginLeft: 6 }}>TOP ITEMS</Text>
          </View>
          {report.topItems.map((item, index) => (
            <View key={item.rank} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: index < report.topItems.length - 1 ? 20 : 0 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
                <View style={{ width: 28, height: 28, borderRadius: 14, backgroundColor: '#EAF9F0', alignItems: 'center', justifyContent: 'center', marginRight: 12 }}>
                  <Text style={{ fontSize: 12, fontWeight: '900', color: '#10A150' }}>{item.rank}</Text>
                </View>
                <View>
                  <Text style={{ fontSize: 15, fontWeight: '900', color: '#101828' }}>{item.name}</Text>
                  <Text style={{ fontSize: 12, color: '#8C867B', fontWeight: '500' }}>{item.units}</Text>
                </View>
              </View>
              <Text style={{ fontSize: 15, fontWeight: '900', color: '#10A150' }}>{item.amount}</Text>
            </View>
          ))}
        </View>

        {/* Date filter + Download */}
        <View style={{ marginBottom: 12, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ fontSize: 12, fontWeight: '700', color: '#8C867B', marginBottom: 10 }}>Select report period</Text>
          <DateFilterSheet value={dateRange} onChange={setDateRange} />
        </View>

        <TouchableOpacity
          style={{ backgroundColor: '#0F761B', borderRadius: 50, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 16 }}
          activeOpacity={0.8}
        >
          <Feather name="download" size={18} color="#FFF" />
          <Text style={{ color: '#fff', fontWeight: '900', fontSize: 16, marginLeft: 8 }}>Download PDF Report</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}
