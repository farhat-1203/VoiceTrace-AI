import React, { useState } from 'react';
import { View, Text, SafeAreaView, ScrollView, StatusBar, TouchableOpacity } from 'react-native';
import { Feather, Ionicons, MaterialCommunityIcons } from '@expo/vector-icons';
import DateFilterSheet, { DateRange, DateFilter } from '../components/DateFilterSheet';

// ── Demo data keyed by filter ──────────────────────────────────────────────
type LedgerRecord = {
  id: number;
  date: string;
  earned: string;
  spent: string;
  net: string;
  itemsSold: { name: string; qty: number; amount: string }[];
  expenses: { name: string; amount: string }[];
  voiceNote: string;
};

const DATA_BY_FILTER: Record<string, LedgerRecord[]> = {
  today: [
    {
      id: 1,
      date: 'Saturday, Mar 28, 2026',
      earned: '₹920',
      spent: '₹350',
      net: '₹570',
      itemsSold: [
        { name: 'Chai', qty: 38, amount: '₹380' },
        { name: 'Samosa', qty: 28, amount: '₹420' },
        { name: 'Water', qty: 12, amount: '₹120' },
      ],
      expenses: [
        { name: 'Milk', amount: '₹200' },
        { name: 'Gas', amount: '₹150' },
      ],
      voiceNote: 'Aaj tak 38 chai, 28 samosa, 12 water. Milk 200, gas cylinder 150.',
    },
  ],
  yesterday: [
    {
      id: 2,
      date: 'Friday, Mar 27, 2026',
      earned: '₹1,070',
      spent: '₹310',
      net: '₹760',
      itemsSold: [
        { name: 'Chai', qty: 120, amount: '₹1,200' },
        { name: 'Samosa', qty: 60, amount: '₹900' },
        { name: 'Vada Pav', qty: 50, amount: '₹600' },
      ],
      expenses: [
        { name: 'Milk', amount: '₹200' },
        { name: 'Oil', amount: '₹110' },
      ],
      voiceNote: '120 chai, 60 samosa, 50 vada pav. Milk 200, oil 110.',
    },
  ],
  last7: [
    {
      id: 1,
      date: 'Saturday, Mar 28, 2026',
      earned: '₹920',
      spent: '₹350',
      net: '₹570',
      itemsSold: [{ name: 'Chai', qty: 38, amount: '₹380' }, { name: 'Samosa', qty: 28, amount: '₹420' }],
      expenses: [{ name: 'Milk', amount: '₹200' }, { name: 'Gas', amount: '₹150' }],
      voiceNote: '38 chai, 28 samosa. Milk 200, gas 150.',
    },
    {
      id: 2,
      date: 'Friday, Mar 27, 2026',
      earned: '₹1,070',
      spent: '₹310',
      net: '₹760',
      itemsSold: [{ name: 'Chai', qty: 120, amount: '₹1,200' }, { name: 'Vada Pav', qty: 50, amount: '₹600' }],
      expenses: [{ name: 'Milk', amount: '₹200' }, { name: 'Oil', amount: '₹110' }],
      voiceNote: '120 chai, 50 vada pav. Milk 200, oil 110.',
    },
    {
      id: 3,
      date: 'Thursday, Mar 26, 2026',
      earned: '₹1,275',
      spent: '₹300',
      net: '₹975',
      itemsSold: [{ name: 'Chai', qty: 75, amount: '₹750' }, { name: 'Samosa', qty: 35, amount: '₹525' }],
      expenses: [{ name: 'Milk', amount: '₹300' }],
      voiceNote: '75 chai, 35 samosa. Milk 300.',
    },
    {
      id: 4,
      date: 'Wednesday, Mar 25, 2026',
      earned: '₹980',
      spent: '₹280',
      net: '₹700',
      itemsSold: [{ name: 'Chai', qty: 65, amount: '₹650' }, { name: 'Biscuit', qty: 33, amount: '₹330' }],
      expenses: [{ name: 'Milk', amount: '₹180' }, { name: 'Sugar', amount: '₹100' }],
      voiceNote: '65 chai, 33 biscuit. Milk 180, sugar 100.',
    },
  ],
  thisMonth: [
    {
      id: 1, date: 'Mar 28, 2026', earned: '₹920', spent: '₹350', net: '₹570',
      itemsSold: [{ name: 'Chai', qty: 38, amount: '₹380' }],
      expenses: [{ name: 'Milk', amount: '₹350' }],
      voiceNote: '38 chai. Milk 350.',
    },
    {
      id: 2, date: 'Mar 27, 2026', earned: '₹1,070', spent: '₹310', net: '₹760',
      itemsSold: [{ name: 'Chai', qty: 120, amount: '₹1,200' }],
      expenses: [{ name: 'Oil', amount: '₹310' }],
      voiceNote: '120 chai. Oil 310.',
    },
    {
      id: 3, date: 'Mar 20, 2026', earned: '₹1,500', spent: '₹400', net: '₹1,100',
      itemsSold: [{ name: 'Chai', qty: 150, amount: '₹1,500' }],
      expenses: [{ name: 'Milk', amount: '₹400' }],
      voiceNote: '150 chai. Milk 400.',
    },
    {
      id: 4, date: 'Mar 15, 2026', earned: '₹1,200', spent: '₹350', net: '₹850',
      itemsSold: [{ name: 'Samosa', qty: 80, amount: '₹1,200' }],
      expenses: [{ name: 'Oil', amount: '₹350' }],
      voiceNote: '80 samosa. Oil 350.',
    },
    {
      id: 5, date: 'Mar 10, 2026', earned: '₹850', spent: '₹200', net: '₹650',
      itemsSold: [{ name: 'Vada Pav', qty: 70, amount: '₹850' }],
      expenses: [{ name: 'Bread', amount: '₹200' }],
      voiceNote: '70 vada pav. Bread 200.',
    },
  ],
  lastMonth: [
    {
      id: 1, date: 'Feb 28, 2026', earned: '₹2,100', spent: '₹600', net: '₹1,500',
      itemsSold: [{ name: 'Chai', qty: 210, amount: '₹2,100' }],
      expenses: [{ name: 'Milk', amount: '₹600' }],
      voiceNote: '210 chai. Milk 600.',
    },
    {
      id: 2, date: 'Feb 15, 2026', earned: '₹1,800', spent: '₹500', net: '₹1,300',
      itemsSold: [{ name: 'Samosa', qty: 120, amount: '₹1,800' }],
      expenses: [{ name: 'Oil', amount: '₹500' }],
      voiceNote: '120 samosa. Oil 500.',
    },
  ],
  past6months: [
    {
      id: 1, date: 'Mar 2026', earned: '₹28,500', spent: '₹8,200', net: '₹20,300',
      itemsSold: [{ name: 'Chai', qty: 2850, amount: '₹28,500' }],
      expenses: [{ name: 'Supplies', amount: '₹8,200' }],
      voiceNote: 'March total: 2850 chai. Supplies 8200.',
    },
    {
      id: 2, date: 'Feb 2026', earned: '₹25,000', spent: '₹7,500', net: '₹17,500',
      itemsSold: [{ name: 'Chai', qty: 2500, amount: '₹25,000' }],
      expenses: [{ name: 'Supplies', amount: '₹7,500' }],
      voiceNote: 'February total: 2500 chai. Supplies 7500.',
    },
    {
      id: 3, date: 'Jan 2026', earned: '₹22,000', spent: '₹6,800', net: '₹15,200',
      itemsSold: [{ name: 'Chai', qty: 2200, amount: '₹22,000' }],
      expenses: [{ name: 'Supplies', amount: '₹6,800' }],
      voiceNote: 'January total: 2200 chai. Supplies 6800.',
    },
  ],
  thisYear: [
    {
      id: 1, date: 'Q1 2026 (Jan–Mar)', earned: '₹75,500', spent: '₹22,500', net: '₹53,000',
      itemsSold: [{ name: 'Chai', qty: 7550, amount: '₹75,500' }],
      expenses: [{ name: 'Total Supplies', amount: '₹22,500' }],
      voiceNote: 'Q1 2026 summary. 7550 chai total. Supplies 22500.',
    },
  ],
  lifetime: [
    {
      id: 1, date: '2026 (YTD)', earned: '₹75,500', spent: '₹22,500', net: '₹53,000',
      itemsSold: [{ name: 'Chai', qty: 7550, amount: '₹75,500' }],
      expenses: [{ name: 'Supplies', amount: '₹22,500' }],
      voiceNote: '2026 YTD: 7550 chai. Supplies 22500.',
    },
    {
      id: 2, date: '2025', earned: '₹2,40,000', spent: '₹72,000', net: '₹1,68,000',
      itemsSold: [{ name: 'All Items', qty: 24000, amount: '₹2,40,000' }],
      expenses: [{ name: 'Total Expenses', amount: '₹72,000' }],
      voiceNote: '2025 full year summary.',
    },
  ],
  custom: [
    {
      id: 1, date: 'Custom Range', earned: '₹3,450', spent: '₹980', net: '₹2,470',
      itemsSold: [{ name: 'Chai', qty: 345, amount: '₹3,450' }],
      expenses: [{ name: 'Supplies', amount: '₹980' }],
      voiceNote: 'Custom date range data.',
    },
  ],
};

function getDefaultRange(): DateRange {
  const today = new Date();
  return { filter: 'last7', label: 'Last 7 Days', from: new Date(today.getFullYear(), today.getMonth(), today.getDate() - 6), to: today };
}

function LedgerCard({ record, defaultOpen = false }: { record: LedgerRecord; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <View style={{ backgroundColor: '#fff', borderRadius: 20, marginBottom: 16, borderWidth: 1, borderColor: '#EBEBEB', overflow: 'hidden' }}>
      <TouchableOpacity onPress={() => setOpen(o => !o)} activeOpacity={0.7} style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 20, paddingBottom: 16 }}>
        <MaterialCommunityIcons name="calendar-month-outline" size={20} color="#10A150" />
        <Text style={{ flex: 1, fontSize: 15, fontWeight: '800', color: '#101828', marginLeft: 12 }}>{record.date}</Text>
        <Feather name={open ? 'chevron-up' : 'chevron-down'} size={20} color="#8C867B" />
      </TouchableOpacity>

      <View style={{ flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 20, paddingBottom: 20 }}>
        <View style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 11, fontWeight: '600', color: '#8C867B', marginBottom: 4 }}>Earnings</Text>
          <Text style={{ fontSize: 18, fontWeight: '900', color: '#10A150' }}>{record.earned}</Text>
        </View>
        <View style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 11, fontWeight: '600', color: '#8C867B', marginBottom: 4 }}>Expenses</Text>
          <Text style={{ fontSize: 18, fontWeight: '900', color: '#E73550' }}>{record.spent}</Text>
        </View>
        <View style={{ alignItems: 'center' }}>
          <Text style={{ fontSize: 11, fontWeight: '600', color: '#8C867B', marginBottom: 4 }}>Net</Text>
          <Text style={{ fontSize: 18, fontWeight: '900', color: '#101828' }}>{record.net}</Text>
        </View>
      </View>

      {open && (
        <>
          <View style={{ height: 1, backgroundColor: '#F0F0F0', marginHorizontal: 20 }} />
          <View style={{ paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
            <Text style={{ fontSize: 13, fontWeight: '900', color: '#10A150', marginBottom: 12 }}>Items Sold</Text>
            {record.itemsSold.map((item, i) => (
              <View key={i} style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text style={{ fontSize: 14, color: '#101828', fontWeight: '500' }}>{item.name} ({item.qty})</Text>
                <Text style={{ fontSize: 14, fontWeight: '700', color: '#101828' }}>{item.amount}</Text>
              </View>
            ))}
            <Text style={{ fontSize: 13, fontWeight: '900', color: '#10A150', marginTop: 16, marginBottom: 12 }}>Expenses</Text>
            {record.expenses.map((exp, i) => (
              <View key={i} style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                <Text style={{ fontSize: 14, color: '#101828', fontWeight: '500' }}>{exp.name}</Text>
                <Text style={{ fontSize: 14, fontWeight: '700', color: '#101828' }}>{exp.amount}</Text>
              </View>
            ))}
            <View style={{ backgroundColor: '#F3F1E9', borderRadius: 16, padding: 16, marginTop: 16, marginBottom: 16, flexDirection: 'row', alignItems: 'flex-start' }}>
              <Ionicons name="mic" size={16} color="#10A150" style={{ marginTop: 2, marginRight: 8 }} />
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 12, fontWeight: '900', color: '#10A150', marginBottom: 4 }}>Original Voice Note</Text>
                <Text style={{ fontSize: 13, color: '#3D3D3D', fontWeight: '500', lineHeight: 20 }}>{record.voiceNote}</Text>
              </View>
            </View>
          </View>
        </>
      )}
    </View>
  );
}

export default function LedgerScreen() {
  const [dateRange, setDateRange] = useState<DateRange>(getDefaultRange());

  const ledgerData = DATA_BY_FILTER[dateRange.filter] ?? DATA_BY_FILTER['last7'];

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: '#F9F9F4', paddingTop: 32 }}>
      <StatusBar barStyle="dark-content" backgroundColor="#F9F9F4" />
      <View style={{ paddingTop: 32, paddingHorizontal: 20, paddingBottom: 8 }}>
        <Text style={{ fontSize: 11, fontWeight: '700', color: '#8C867B', letterSpacing: 2, marginBottom: 4 }}>BUSINESS RECORDS</Text>
        <Text style={{ fontSize: 28, fontWeight: '900', color: '#101828' }}>My Ledger</Text>
        <Text style={{ fontSize: 13, color: '#8C867B', fontWeight: '500', marginTop: 4 }}>Tap to view details</Text>
      </View>

      <View style={{ paddingHorizontal: 20, paddingVertical: 12, alignItems: 'center', justifyContent: 'center' }}>
        <DateFilterSheet value={dateRange} onChange={setDateRange} />
      </View>

      <View style={{ height: 1, backgroundColor: '#E5E5E5', marginHorizontal: 20, marginBottom: 16 }} />

      <ScrollView contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
        {ledgerData.map((record, i) => (
          <LedgerCard key={record.id} record={record} defaultOpen={i === 0} />
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}
