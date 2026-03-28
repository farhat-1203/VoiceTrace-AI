import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, SafeAreaView, TouchableOpacity, StatusBar, Animated, Modal
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Props {
  visible: boolean;
  onClose: () => void;
}

// Waveform bar component
function WaveBar({ delay }: { delay: number }) {
  const anim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1, duration: 400 + delay, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 0.3, duration: 400 + delay, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, []);

  return (
    <Animated.View
      style={{
        width: 6,
        height: 40,
        borderRadius: 4,
        backgroundColor: '#FFF',
        marginHorizontal: 3,
        transform: [{ scaleY: anim }],
      }}
    />
  );
}

export default function RecordingScreen({ visible, onClose }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startRecording = () => {
    setIsRecording(true);
    setSeconds(0);
    timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000);
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const handleClose = () => {
    stopRecording();
    setSeconds(0);
    onClose();
  };

  const formatTime = (s: number) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const delays = [100, 250, 50, 180, 300, 80, 220];

  return (
    <Modal visible={visible} animationType="slide" statusBarTranslucent>
      <SafeAreaView style={{ flex: 1, backgroundColor: '#0F761B' }}>
        <StatusBar barStyle="light-content" backgroundColor="#0F761B" />

        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 }}>
          <TouchableOpacity onPress={handleClose} style={{ padding: 8 }}>
            <Ionicons name="chevron-down" size={28} color="#FFF" />
          </TouchableOpacity>
          <Text style={{ flex: 1, textAlign: 'center', color: '#FFF', fontSize: 16, fontWeight: '700' }}>
            Voice Entry
          </Text>
          <View style={{ width: 44 }} />
        </View>

        {/* Main content */}
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 }}>

          {/* Waveform / idle icon */}
          <View style={{
            width: 200, height: 200, borderRadius: 100,
            backgroundColor: 'rgba(255,255,255,0.15)',
            alignItems: 'center', justifyContent: 'center', marginBottom: 32,
          }}>
            <View style={{
              width: 150, height: 150, borderRadius: 75,
              backgroundColor: 'rgba(255,255,255,0.2)',
              alignItems: 'center', justifyContent: 'center',
            }}>
              {isRecording ? (
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  {delays.map((d, i) => <WaveBar key={i} delay={d} />)}
                </View>
              ) : (
                /* Custom waveform icon (static bars) */
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  {[14, 28, 40, 28, 40, 28, 14].map((h, i) => (
                    <View key={i} style={{
                      width: 6, height: h, borderRadius: 4,
                      backgroundColor: '#FFF', marginHorizontal: 3,
                    }} />
                  ))}
                </View>
              )}
            </View>
          </View>

          <Text style={{ color: '#FFF', fontSize: 26, fontWeight: '900', marginBottom: 8 }}>
            {isRecording ? 'Listening...' : 'Start Talking'}
          </Text>
          <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 15, fontWeight: '500', textAlign: 'center', marginBottom: 16 }}>
            {isRecording ? 'Speak in Hindi / Hinglish' : 'Tap the button below to start recording'}
          </Text>

          {isRecording && (
            <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 22, fontWeight: '800', letterSpacing: 2 }}>
              {formatTime(seconds)}
            </Text>
          )}
        </View>

        {/* Bottom controls */}
        <View style={{ alignItems: 'center', paddingBottom: 48, gap: 16 }}>
          {isRecording ? (
            <TouchableOpacity
              onPress={stopRecording}
              style={{
                width: 80, height: 80, borderRadius: 40,
                backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <View style={{ width: 28, height: 28, borderRadius: 6, backgroundColor: '#E73550' }} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              onPress={startRecording}
              style={{
                width: 80, height: 80, borderRadius: 40,
                backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center',
              }}
            >
              {/* Waveform icon matching the image */}
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                {[10, 20, 30, 20, 30, 20, 10].map((h, i) => (
                  <View key={i} style={{
                    width: 4, height: h, borderRadius: 3,
                    backgroundColor: '#0F761B', marginHorizontal: 2,
                  }} />
                ))}
              </View>
            </TouchableOpacity>
          )}
          <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 13, fontWeight: '600' }}>
            {isRecording ? 'Tap to stop' : 'Tap to record'}
          </Text>
        </View>
      </SafeAreaView>
    </Modal>
  );
}
