/**
 * VoiceTrace AI — Recording Screen
 *
 * Three-phase flow:
 *
 *  1. IDLE     → User taps mic to start recording (expo-av)
 *  2. RECORDING → Timer runs, audio captured (max 3 min)
 *  3. PROCESSING → File uploaded to POST /process with JWT
 *  4. RESULT   → Transcription + extracted data shown
 *  5. VAPI     → If pipeline says should_trigger_vapi OR user taps "Talk to Agent"
 *                → Start VAPI WebRTC agent session
 *
 * VAPI Event Handling:
 *  - vapiInstance.on('call-start')  → switch UI to agent-speaking mode
 *  - vapiInstance.on('call-end')    → return to RESULT state
 *  - vapiInstance.on('speech-start') → agent speaking animation
 *  - vapiInstance.on('speech-end')  → agent idle
 *  - vapiInstance.on('message')     → append transcript lines
 *  - vapiInstance.on('error')       → show error alert
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, SafeAreaView, TouchableOpacity, StatusBar,
  Animated, Modal, ScrollView, Alert, ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import type { Session } from '@supabase/supabase-js';

import { BACKEND_URL } from '../config/api';
import { vapiInstance, startVapiSession, stopVapiSession } from '../services/vapiClient';

// ── Types ─────────────────────────────────────────────────────────────

type ScreenPhase =
  | 'idle'
  | 'recording'
  | 'processing'
  | 'result'
  | 'vapi_connecting'
  | 'vapi_active';

interface ProcessResult {
  session_id: string;
  transcript: string;
  extracted_data: Record<string, any>;
  final_response: string;
  safety_flag: string;
  should_trigger_vapi: boolean;
  mood_trigger_reason?: string;
  error?: string;
}

interface ConversationLine {
  role: 'agent' | 'user';
  text: string;
}

interface Props {
  visible: boolean;
  onClose: () => void;
  session: Session;
}

// ── Waveform Animated Bar ─────────────────────────────────────────────

function WaveBar({ delay, color = '#FFF' }: { delay: number; color?: string }) {
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
    <Animated.View style={{
      width: 6, height: 40, borderRadius: 4,
      backgroundColor: color, marginHorizontal: 3,
      transform: [{ scaleY: anim }],
    }} />
  );
}

// ── Main Component ────────────────────────────────────────────────────

export default function RecordingScreen({ visible, onClose, session }: Props) {
  const [phase, setPhase] = useState<ScreenPhase>('idle');
  const [seconds, setSeconds] = useState(0);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [conversation, setConversation] = useState<ConversationLine[]>([]);
  const [agentSpeaking, setAgentSpeaking] = useState(false);

  const recordingRef = useRef<Audio.Recording | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const conversationRef = useRef<ScrollView>(null);

  const delays = [100, 250, 50, 180, 300, 80, 220];

  // ── VAPI Event Wiring ─────────────────────────────────────────────
  useEffect(() => {
    const onCallStart = () => {
      setPhase('vapi_active');
      setConversation([]);
    };

    const onCallEnd = () => {
      setAgentSpeaking(false);
      setPhase('result');
    };

    const onSpeechStart = () => setAgentSpeaking(true);
    const onSpeechEnd   = () => setAgentSpeaking(false);

    const onMessage = (msg: any) => {
      // VAPI sends transcript objects and function-call results as messages
      if (msg?.type === 'transcript') {
        const role: 'agent' | 'user' = msg.role === 'assistant' ? 'agent' : 'user';
        const text: string = msg.transcript ?? '';
        if (text.trim()) {
          setConversation((prev) => [...prev, { role, text }]);
          setTimeout(() => conversationRef.current?.scrollToEnd({ animated: true }), 100);
        }
      }
    };

    const onError = (err: any) => {
      Alert.alert('VAPI Error', err?.message ?? 'Voice agent encountered an error.');
      setPhase('result');
    };

    vapiInstance.on('call-start', onCallStart);
    vapiInstance.on('call-end', onCallEnd);
    vapiInstance.on('speech-start', onSpeechStart);
    vapiInstance.on('speech-end', onSpeechEnd);
    vapiInstance.on('message', onMessage);
    vapiInstance.on('error', onError);

    return () => {
      vapiInstance.off('call-start', onCallStart);
      vapiInstance.off('call-end', onCallEnd);
      vapiInstance.off('speech-start', onSpeechStart);
      vapiInstance.off('speech-end', onSpeechEnd);
      vapiInstance.off('message', onMessage);
      vapiInstance.off('error', onError);
    };
  }, []);

  // ── Audio Recording ───────────────────────────────────────────────

  const startRecording = async () => {
    try {
      const { granted } = await Audio.requestPermissionsAsync();
      if (!granted) {
        Alert.alert('Microphone Permission', 'Please allow microphone access to record audio.');
        return;
      }

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync({
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 44100,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      });
      await recording.startAsync();
      recordingRef.current = recording;

      setPhase('recording');
      setSeconds(0);
      timerRef.current = setInterval(() => {
        setSeconds((s) => {
          // Auto-stop at 3 minutes
          if (s >= 179) {
            stopRecording();
            return 180;
          }
          return s + 1;
        });
      }, 1000);
    } catch (err: any) {
      Alert.alert('Recording Error', err.message ?? 'Could not start recording.');
    }
  };

  const stopRecording = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    setPhase('processing');

    const recording = recordingRef.current;
    if (!recording) return;

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      recordingRef.current = null;

      await Audio.setAudioModeAsync({ allowsRecordingIOS: false });

      if (!uri) throw new Error('No audio URI returned');
      await uploadAndProcess(uri);
    } catch (err: any) {
      Alert.alert('Processing Error', err.message ?? 'Could not process audio.');
      setPhase('idle');
    }
  };

  // ── Upload to Backend Pipeline ────────────────────────────────────

  const uploadAndProcess = async (uri: string) => {
    const accessToken = session.access_token;

    const formData = new FormData();
    formData.append('file', {
      uri,
      name: 'recording.m4a',
      type: 'audio/mp4',
    } as any);

    try {
      const response = await fetch(`${BACKEND_URL}/process`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${accessToken}`,
          'ngrok-skip-browser-warning': 'true', // ngrok tunnel header
        },
        body: formData,
      });

      if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Server error ${response.status}: ${errText}`);
      }

      const data: ProcessResult = await response.json();
      setResult(data);
      setPhase('result');

      // ── Auto-trigger VAPI if pipeline says so ──────────────────
      if (data.should_trigger_vapi) {
        setTimeout(() => triggerVapiSession(data), 1200);
      }
    } catch (err: any) {
      Alert.alert('Upload Failed', err.message ?? 'Could not connect to backend.');
      setPhase('idle');
    }
  };

  // ── VAPI Session Trigger ──────────────────────────────────────────

  const triggerVapiSession = async (pipelineResult: ProcessResult) => {
    setPhase('vapi_connecting');
    try {
      await startVapiSession({
        user_id: session.user.id,
        trigger_reason: pipelineResult.mood_trigger_reason ?? 'Voice entry completed',
        sessionPayload: {
          session_id: pipelineResult.session_id,
          extracted_data: pipelineResult.extracted_data,
          transcript: pipelineResult.transcript,
        },
      });
      // VAPI 'call-start' event will fire and set phase to 'vapi_active'
    } catch (err: any) {
      Alert.alert('Agent Error', 'Could not connect to voice agent. Please try again.');
      setPhase('result');
    }
  };

  // ── Close / Cleanup ───────────────────────────────────────────────

  const handleClose = () => {
    if (phase === 'vapi_active' || phase === 'vapi_connecting') {
      stopVapiSession();
    }
    if (timerRef.current) clearInterval(timerRef.current);
    recordingRef.current?.stopAndUnloadAsync().catch(() => {});
    recordingRef.current = null;
    setPhase('idle');
    setSeconds(0);
    setResult(null);
    setConversation([]);
    onClose();
  };

  const formatTime = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  const timeWarning = seconds >= 150; // last 30 sec

  // ── Render ────────────────────────────────────────────────────────

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
            {phase === 'vapi_active' ? 'Voice Agent' : 'Voice Entry'}
          </Text>
          <View style={{ width: 44 }} />
        </View>

        {/* ═══════════════════════════════════════════════ */}
        {/* Phase: IDLE / RECORDING                        */}
        {/* ═══════════════════════════════════════════════ */}
        {(phase === 'idle' || phase === 'recording') && (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 32 }}>

            {/* Waveform orb */}
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
                {phase === 'recording' ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {delays.map((d, i) => <WaveBar key={i} delay={d} />)}
                  </View>
                ) : (
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
              {phase === 'recording' ? 'Listening...' : 'Start Talking'}
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.75)', fontSize: 15, fontWeight: '500', textAlign: 'center', marginBottom: 16 }}>
              {phase === 'recording'
                ? 'Speak in Hindi / Hinglish'
                : 'Tap the button below to start recording'}
            </Text>

            {phase === 'recording' && (
              <Text style={{
                color: timeWarning ? '#FFD700' : 'rgba(255,255,255,0.9)',
                fontSize: 22, fontWeight: '800', letterSpacing: 2,
              }}>
                {formatTime(seconds)}
                {timeWarning && ' ⚠️'}
              </Text>
            )}
          </View>
        )}

        {/* ═══════════════════════════════════════════════ */}
        {/* Phase: PROCESSING                              */}
        {/* ═══════════════════════════════════════════════ */}
        {phase === 'processing' && (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator size="large" color="#fff" />
            <Text style={{ color: '#FFF', fontSize: 18, fontWeight: '700', marginTop: 20 }}>
              Transcribing...
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 14, marginTop: 8 }}>
              Groq Whisper is processing your audio
            </Text>
          </View>
        )}

        {/* ═══════════════════════════════════════════════ */}
        {/* Phase: RESULT                                  */}
        {/* ═══════════════════════════════════════════════ */}
        {phase === 'result' && result && (
          <ScrollView
            style={{ flex: 1 }}
            contentContainerStyle={{ padding: 24 }}
            showsVerticalScrollIndicator={false}
          >
            {/* Transcript card */}
            <View style={{
              backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 16,
              padding: 16, marginBottom: 16,
            }}>
              <Text style={{ color: 'rgba(255,255,255,0.65)', fontSize: 11, fontWeight: '700', marginBottom: 8, letterSpacing: 1 }}>
                TRANSCRIPT
              </Text>
              <Text style={{ color: '#FFF', fontSize: 15, lineHeight: 22 }}>
                {result.transcript || '(no transcript)'}
              </Text>
            </View>

            {/* AI Response card */}
            {result.final_response ? (
              <View style={{
                backgroundColor: 'rgba(255,255,255,0.12)', borderRadius: 16,
                padding: 16, marginBottom: 16,
              }}>
                <Text style={{ color: 'rgba(255,255,255,0.65)', fontSize: 11, fontWeight: '700', marginBottom: 8, letterSpacing: 1 }}>
                  AI INSIGHTS
                </Text>
                <Text style={{ color: '#FFF', fontSize: 14, lineHeight: 21 }}>
                  {result.final_response}
                </Text>
              </View>
            ) : null}

            {/* Earnings / Expenses summary */}
            {result.extracted_data && (
              <View style={{
                flexDirection: 'row', gap: 10, marginBottom: 20,
              }}>
                {[
                  {
                    label: 'EARNED',
                    value: `₹${(result.extracted_data.items_sold ?? [])
                      .reduce((s: number, i: any) => s + (i.total_amount ?? 0), 0)}`,
                    color: '#4ADE80',
                  },
                  {
                    label: 'SPENT',
                    value: `₹${(result.extracted_data.expenses ?? [])
                      .reduce((s: number, e: any) => s + (e.amount ?? 0), 0)}`,
                    color: '#F87171',
                  },
                ].map((card) => (
                  <View key={card.label} style={{
                    flex: 1, backgroundColor: 'rgba(255,255,255,0.1)',
                    borderRadius: 14, padding: 14, alignItems: 'center',
                  }}>
                    <Text style={{ color: card.color, fontSize: 22, fontWeight: '900' }}>
                      {card.value}
                    </Text>
                    <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 11, fontWeight: '700', marginTop: 4 }}>
                      {card.label}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* Talk to Agent button */}
            <TouchableOpacity
              onPress={() => triggerVapiSession(result)}
              style={{
                backgroundColor: '#FFF', borderRadius: 16,
                paddingVertical: 16, alignItems: 'center',
                flexDirection: 'row', justifyContent: 'center', gap: 10,
              }}
            >
              <Ionicons name="mic" size={22} color="#0F761B" />
              <Text style={{ color: '#0F761B', fontSize: 16, fontWeight: '800' }}>
                Talk to Agent
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleClose}
              style={{
                marginTop: 12, paddingVertical: 14, alignItems: 'center',
              }}
            >
              <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 15, fontWeight: '600' }}>
                Close
              </Text>
            </TouchableOpacity>
          </ScrollView>
        )}

        {/* ═══════════════════════════════════════════════ */}
        {/* Phase: VAPI CONNECTING                         */}
        {/* ═══════════════════════════════════════════════ */}
        {phase === 'vapi_connecting' && (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator size="large" color="#fff" />
            <Text style={{ color: '#FFF', fontSize: 18, fontWeight: '700', marginTop: 20 }}>
              Connecting Agent...
            </Text>
            <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 14, marginTop: 8 }}>
              Setting up voice session
            </Text>
          </View>
        )}

        {/* ═══════════════════════════════════════════════ */}
        {/* Phase: VAPI ACTIVE — Real-time conversation    */}
        {/* ═══════════════════════════════════════════════ */}
        {phase === 'vapi_active' && (
          <View style={{ flex: 1 }}>
            {/* Agent speaking orb */}
            <View style={{ alignItems: 'center', paddingVertical: 28 }}>
              <View style={{
                width: 130, height: 130, borderRadius: 65,
                backgroundColor: agentSpeaking
                  ? 'rgba(255,255,255,0.25)'
                  : 'rgba(255,255,255,0.1)',
                alignItems: 'center', justifyContent: 'center',
              }}>
                {agentSpeaking ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {delays.slice(0, 5).map((d, i) => (
                      <WaveBar key={i} delay={d} color={agentSpeaking ? '#FFF' : 'rgba(255,255,255,0.5)'} />
                    ))}
                  </View>
                ) : (
                  <Ionicons name="mic-outline" size={52} color="rgba(255,255,255,0.7)" />
                )}
              </View>
              <Text style={{ color: '#FFF', fontSize: 16, fontWeight: '700', marginTop: 12 }}>
                {agentSpeaking ? 'Agent Speaking...' : 'Listening to you...'}
              </Text>
            </View>

            {/* Conversation transcript */}
            <ScrollView
              ref={conversationRef}
              style={{
                flex: 1, marginHorizontal: 16,
                backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 16,
              }}
              contentContainerStyle={{ padding: 16 }}
              showsVerticalScrollIndicator={false}
            >
              {conversation.length === 0 && (
                <Text style={{ color: 'rgba(255,255,255,0.5)', textAlign: 'center', fontSize: 14, marginTop: 20 }}>
                  Conversation will appear here...
                </Text>
              )}
              {conversation.map((line, idx) => (
                <View key={idx} style={{
                  marginBottom: 12,
                  alignItems: line.role === 'agent' ? 'flex-start' : 'flex-end',
                }}>
                  <View style={{
                    maxWidth: '80%',
                    backgroundColor: line.role === 'agent'
                      ? 'rgba(255,255,255,0.2)'
                      : 'rgba(255,255,255,0.1)',
                    borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10,
                  }}>
                    <Text style={{ color: 'rgba(255,255,255,0.55)', fontSize: 11, fontWeight: '700', marginBottom: 4 }}>
                      {line.role === 'agent' ? 'AGENT' : 'YOU'}
                    </Text>
                    <Text style={{ color: '#FFF', fontSize: 14, lineHeight: 20 }}>
                      {line.text}
                    </Text>
                  </View>
                </View>
              ))}
            </ScrollView>

            {/* End call button */}
            <View style={{ alignItems: 'center', paddingVertical: 24, paddingBottom: 40 }}>
              <TouchableOpacity
                onPress={() => {
                  stopVapiSession();
                  setPhase('result');
                }}
                style={{
                  width: 70, height: 70, borderRadius: 35,
                  backgroundColor: '#E73550',
                  alignItems: 'center', justifyContent: 'center',
                  shadowColor: '#E73550', shadowOpacity: 0.5, shadowRadius: 12, elevation: 8,
                }}
              >
                <Ionicons name="call" size={30} color="#FFF" />
              </TouchableOpacity>
              <Text style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, fontWeight: '600', marginTop: 10 }}>
                End Session
              </Text>
            </View>
          </View>
        )}

        {/* ═══ Bottom Controls (only for idle/recording) ═══════════════ */}
        {(phase === 'idle' || phase === 'recording') && (
          <View style={{ alignItems: 'center', paddingBottom: 48, gap: 16 }}>
            {phase === 'recording' ? (
              <TouchableOpacity
                onPress={stopRecording}
                style={{
                  width: 80, height: 80, borderRadius: 40,
                  backgroundColor: '#FFF', alignItems: 'center', justifyContent: 'center',
                  shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 8, elevation: 6,
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
                  shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 8, elevation: 6,
                }}
              >
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
              {phase === 'recording' ? 'Tap to stop' : 'Tap to record'}
            </Text>
          </View>
        )}
      </SafeAreaView>
    </Modal>
  );
}
