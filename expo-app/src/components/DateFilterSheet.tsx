import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Modal,
  ScrollView,
  Platform,
} from 'react-native';
import { Feather } from '@expo/vector-icons';

export type DateFilter =
  | 'today'
  | 'yesterday'
  | 'last7'
  | 'thisMonth'
  | 'lastMonth'
  | 'past6months'
  | 'thisYear'
  | 'lifetime'
  | 'custom';

export interface DateRange {
  filter: DateFilter;
  label: string;
  from: Date;
  to: Date;
}

const QUICK_OPTIONS: { key: DateFilter; label: string }[] = [
  { key: 'today', label: 'Today' },
  { key: 'yesterday', label: 'Yesterday' },
  { key: 'last7', label: 'Last 7 Days' },
  { key: 'thisMonth', label: 'This Month' },
  { key: 'lastMonth', label: 'Last Month' },
  { key: 'past6months', label: 'Past 6 Months' },
  { key: 'thisYear', label: 'This Year' },
  { key: 'lifetime', label: 'Lifetime' },
];

function getRange(filter: DateFilter): { from: Date; to: Date } {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  switch (filter) {
    case 'today':
      return { from: today, to: today };
    case 'yesterday': {
      const y = new Date(today); y.setDate(y.getDate() - 1);
      return { from: y, to: y };
    }
    case 'last7': {
      const f = new Date(today); f.setDate(f.getDate() - 6);
      return { from: f, to: today };
    }
    case 'thisMonth':
      return { from: new Date(today.getFullYear(), today.getMonth(), 1), to: today };
    case 'lastMonth': {
      const f = new Date(today.getFullYear(), today.getMonth() - 1, 1);
      const t = new Date(today.getFullYear(), today.getMonth(), 0);
      return { from: f, to: t };
    }
    case 'past6months': {
      const f = new Date(today); f.setMonth(f.getMonth() - 6);
      return { from: f, to: today };
    }
    case 'thisYear':
      return { from: new Date(today.getFullYear(), 0, 1), to: today };
    case 'lifetime':
      return { from: new Date(2020, 0, 1), to: today };
    default:
      return { from: today, to: today };
  }
}

function fmt(d: Date) {
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
}

function shortLabel(filter: DateFilter, from: Date, to: Date) {
  if (filter === 'custom') return `${fmt(from)} – ${fmt(to)}`;
  return QUICK_OPTIONS.find(o => o.key === filter)?.label ?? 'Select Period';
}

// Minimal inline calendar
function MiniCalendar({
  title,
  selected,
  onSelect,
  onClose,
}: {
  title: string;
  selected: Date;
  onSelect: (d: Date) => void;
  onClose: () => void;
}) {
  const [viewYear, setViewYear] = useState(selected.getFullYear());
  const [viewMonth, setViewMonth] = useState(selected.getMonth());

  const DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];
  const firstDay = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const monthName = new Date(viewYear, viewMonth, 1).toLocaleString('default', { month: 'long' });

  const cells: (number | null)[] = [...Array(firstDay).fill(null), ...Array.from({ length: daysInMonth }, (_, i) => i + 1)];

  return (
    <View style={{ backgroundColor: '#fff', borderRadius: 20, padding: 20, margin: 16 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
        <Text style={{ fontSize: 16, fontWeight: '800', color: '#101828' }}>{title}</Text>
        <TouchableOpacity onPress={onClose}>
          <Feather name="x" size={20} color="#8C867B" />
        </TouchableOpacity>
      </View>

      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginVertical: 16 }}>
        <TouchableOpacity onPress={() => { const d = new Date(viewYear, viewMonth - 1, 1); setViewMonth(d.getMonth()); setViewYear(d.getFullYear()); }}>
          <Feather name="arrow-left" size={20} color="#10A150" />
        </TouchableOpacity>
        <Text style={{ fontSize: 16, fontWeight: '700', color: '#10A150' }}>{monthName} {viewYear}</Text>
        <TouchableOpacity onPress={() => { const d = new Date(viewYear, viewMonth + 1, 1); setViewMonth(d.getMonth()); setViewYear(d.getFullYear()); }}>
          <Feather name="arrow-right" size={20} color="#10A150" />
        </TouchableOpacity>
      </View>

      <View style={{ flexDirection: 'row', marginBottom: 8 }}>
        {DAYS.map(d => (
          <Text key={d} style={{ flex: 1, textAlign: 'center', fontSize: 12, fontWeight: '600', color: '#8C867B' }}>{d}</Text>
        ))}
      </View>

      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {cells.map((day, i) => {
          const isSelected = day !== null && selected.getDate() === day && selected.getMonth() === viewMonth && selected.getFullYear() === viewYear;
          return (
            <TouchableOpacity
              key={i}
              style={{ width: `${100 / 7}%`, alignItems: 'center', paddingVertical: 8 }}
              disabled={day === null}
              onPress={() => { if (day) { onSelect(new Date(viewYear, viewMonth, day)); onClose(); } }}
            >
              {day !== null && (
                <View style={{ width: 32, height: 32, borderRadius: 16, backgroundColor: isSelected ? '#10A150' : 'transparent', alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={{ fontSize: 14, fontWeight: isSelected ? '800' : '400', color: isSelected ? '#fff' : '#101828' }}>{day}</Text>
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

interface Props {
  value: DateRange;
  onChange: (range: DateRange) => void;
}

export default function DateFilterSheet({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [tempFilter, setTempFilter] = useState<DateFilter>(value.filter);
  const [customFrom, setCustomFrom] = useState<Date>(value.from);
  const [customTo, setCustomTo] = useState<Date>(value.to);
  const [calendarFor, setCalendarFor] = useState<'from' | 'to' | null>(null);

  const today = new Date();

  function handleOpen() {
    setTempFilter(value.filter);
    setCustomFrom(value.from);
    setCustomTo(value.to);
    setOpen(true);
  }

  function handleQuickSelect(key: DateFilter) {
    setTempFilter(key);
    const { from, to } = getRange(key);
    setCustomFrom(from);
    setCustomTo(to);
  }

  function handleDone() {
    const label = shortLabel(tempFilter, customFrom, customTo);
    onChange({ filter: tempFilter, label, from: customFrom, to: customTo });
    setOpen(false);
  }

  return (
    <>
      {/* Trigger button */}
      <TouchableOpacity
        onPress={handleOpen}
        style={{
          flexDirection: 'row', alignItems: 'center',
          backgroundColor: '#fff', borderRadius: 50,
          paddingHorizontal: 16, paddingVertical: 10,
          borderWidth: 1, borderColor: '#EBEBEB',
          alignSelf: 'center',
        }}
      >
        <Feather name="calendar" size={14} color="#10A150" style={{ marginRight: 6 }} />
        <Text style={{ fontSize: 14, fontWeight: '700', color: '#101828' }}>{value.label}</Text>
        <Feather name="chevron-down" size={14} color="#8C867B" style={{ marginLeft: 6 }} />
      </TouchableOpacity>

      <Modal visible={open} transparent animationType="slide" onRequestClose={() => setOpen(false)}>
        <TouchableOpacity style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.35)' }} activeOpacity={1} onPress={() => setOpen(false)} />

        <View style={{ backgroundColor: '#F9F9F4', borderTopLeftRadius: 28, borderTopRightRadius: 28, paddingBottom: 32 }}>
          {calendarFor ? (
            <MiniCalendar
              title={calendarFor === 'from' ? 'Select From Date' : 'Select To Date'}
              selected={calendarFor === 'from' ? customFrom : customTo}
              onSelect={(d) => {
                if (calendarFor === 'from') { setCustomFrom(d); setTempFilter('custom'); }
                else { setCustomTo(d); setTempFilter('custom'); }
              }}
              onClose={() => setCalendarFor(null)}
            />
          ) : (
            <View style={{ padding: 20 }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <Text style={{ fontSize: 18, fontWeight: '800', color: '#101828' }}>Select date</Text>
                <Text style={{ fontSize: 13, color: '#8C867B', fontWeight: '600' }}>
                  Today, {today.getDate()} {today.toLocaleString('default', { month: 'short' })}
                </Text>
              </View>

              <View style={{ height: 1, backgroundColor: '#E5E5E5', marginVertical: 16 }} />

              {/* Quick options grid */}
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                {QUICK_OPTIONS.map(opt => {
                  const active = tempFilter === opt.key;
                  return (
                    <TouchableOpacity
                      key={opt.key}
                      onPress={() => handleQuickSelect(opt.key)}
                      style={{
                        paddingHorizontal: 16, paddingVertical: 10,
                        borderRadius: 50,
                        backgroundColor: active ? '#10A150' : '#fff',
                        borderWidth: 1, borderColor: active ? '#10A150' : '#DEDEDE',
                      }}
                    >
                      <Text style={{ fontSize: 13, fontWeight: '700', color: active ? '#fff' : '#101828' }}>{opt.label}</Text>
                    </TouchableOpacity>
                  );
                })}
              </View>

              {/* Divider */}
              <View style={{ flexDirection: 'row', alignItems: 'center', marginVertical: 20 }}>
                <View style={{ flex: 1, height: 1, backgroundColor: '#E5E5E5' }} />
                <Text style={{ marginHorizontal: 12, color: '#8C867B', fontSize: 13 }}>Or</Text>
                <View style={{ flex: 1, height: 1, backgroundColor: '#E5E5E5' }} />
              </View>

              {/* Custom date range */}
              <View style={{ flexDirection: 'row', gap: 12 }}>
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 12, fontWeight: '600', color: '#8C867B', marginBottom: 6 }}>From</Text>
                  <TouchableOpacity
                    onPress={() => setCalendarFor('from')}
                    style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#DEDEDE', paddingHorizontal: 14, paddingVertical: 12 }}
                  >
                    <Text style={{ fontSize: 14, color: '#101828', fontWeight: '600' }}>{fmt(customFrom)}</Text>
                    <Feather name="calendar" size={16} color="#8C867B" />
                  </TouchableOpacity>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={{ fontSize: 12, fontWeight: '600', color: '#8C867B', marginBottom: 6 }}>To</Text>
                  <TouchableOpacity
                    onPress={() => setCalendarFor('to')}
                    style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#fff', borderRadius: 12, borderWidth: 1, borderColor: '#DEDEDE', paddingHorizontal: 14, paddingVertical: 12 }}
                  >
                    <Text style={{ fontSize: 14, color: '#101828', fontWeight: '600' }}>{fmt(customTo)}</Text>
                    <Feather name="calendar" size={16} color="#8C867B" />
                  </TouchableOpacity>
                </View>
              </View>

              {/* Done */}
              <TouchableOpacity
                onPress={handleDone}
                style={{ backgroundColor: '#0F761B', borderRadius: 50, paddingVertical: 16, alignItems: 'center', marginTop: 24 }}
              >
                <Text style={{ color: '#fff', fontWeight: '800', fontSize: 16 }}>Done</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </Modal>
    </>
  );
}
