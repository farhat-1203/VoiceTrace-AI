/**
 * VoiceTrace AI — VAPI React Native Client
 *
 * Wraps the @vapi-ai/react-native SDK.
 * Provides:
 *  - Singleton vapiInstance
 *  - startVapiSession(context): kicks off a VAPI WebRTC call with injected context
 *  - stopVapiSession(): ends the active call
 *  - Event callbacks for UI reactivity
 *
 * The VAPI agent's serverUrl is set to our ngrok backend so that VAPI
 * sends function-call webhooks to /vapi/functions/execute.
 */
import Vapi from '@vapi-ai/react-native';
import { VAPI_PUBLIC_KEY, VAPI_ASSISTANT_ID, BACKEND_URL } from '../config/api';

// ── Singleton VAPI instance ───────────────────────────────────────────
export const vapiInstance = new Vapi(VAPI_PUBLIC_KEY);

// ── Session context type ──────────────────────────────────────────────
export interface VapiSessionContext {
  user_id: string;
  trigger_reason: string;
  /** Backend /vapi/session/start payload for injecting into assistant */
  sessionPayload?: Record<string, unknown>;
}

/**
 * Start a VAPI WebRTC agent session.
 *
 * Flow:
 * 1. Call backend /vapi/session/start to get context + system prompt
 * 2. Start VAPI call with the assistant, injecting the system prompt override
 *    and pointing serverUrl to our FastAPI backend for function calls.
 *
 * VAPI will immediately connect via WebRTC (Daily.co) — lowest latency path.
 */
export async function startVapiSession(context: VapiSessionContext): Promise<void> {
  try {
    // Step 1: Fetch context + system prompt from our backend
    const response = await fetch(`${BACKEND_URL}/vapi/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: context.user_id,
        trigger_reason: context.trigger_reason,
        context_data: context.sessionPayload ?? {},
      }),
    });

    const sessionData = response.ok ? await response.json() : null;
    const systemPrompt: string = sessionData?.system_prompt ?? defaultSystemPrompt();
    const vapiContext: Record<string, unknown> = sessionData?.context ?? {};

    // Step 2: Start the VAPI call with assistant override
    await vapiInstance.start({
      assistantId: VAPI_ASSISTANT_ID,
      assistantOverrides: {
        // Inject dynamic system prompt with real context
        model: {
          provider: 'groq',
          model: 'llama-3.3-70b-versatile',
          messages: [
            {
              role: 'system',
              content: buildSystemPrompt(systemPrompt, vapiContext),
            },
          ],
          // Point function calls to our backend
          toolIds: [],
        },
        // Backend receives transcripts, function calls, and events
        serverUrl: `${BACKEND_URL}/vapi/functions/execute`,
        serverMessages: [
          'conversation-update',
          'function-call',
          'end-of-call-report',
        ],
        // Voice settings for natural Hindi/Hinglish TTS
        voice: {
          provider: 'playht',
          voiceId: 'jennifer',
        },
      },
    });
  } catch (err) {
    console.error('[vapiClient] Failed to start session:', err);
    throw err;
  }
}

/**
 * Stop the active VAPI call.
 */
export function stopVapiSession(): void {
  vapiInstance.stop();
}

// ── System prompt builder ─────────────────────────────────────────────

function defaultSystemPrompt(): string {
  return `You are a helpful business assistant for street vendors in India.
Speak in Hindi or Hinglish. Ask one question at a time. Be warm and empathetic.`;
}

function buildSystemPrompt(
  base: string,
  ctx: Record<string, unknown>,
): string {
  const parts = [base];

  if (ctx.vendor_name) {
    parts.push(`\nVendor name: ${ctx.vendor_name}`);
  }
  if (ctx.trigger_reason) {
    parts.push(`\nReason for this call: ${ctx.trigger_reason}`);
  }
  if (ctx.total_revenue !== undefined) {
    parts.push(
      `\nToday's revenue: ₹${ctx.total_revenue}, expenses: ₹${ctx.total_expenses}, profit: ₹${ctx.net_profit}`,
    );
  }
  if ((ctx.low_confidence_items as unknown[])?.length) {
    parts.push(
      `\nItems needing clarification: ${JSON.stringify(ctx.low_confidence_items)}`,
    );
  }
  if ((ctx.stock_out_mentions as unknown[])?.length) {
    parts.push(`\nStock-outs mentioned: ${(ctx.stock_out_mentions as string[]).join(', ')}`);
  }

  return parts.join('\n');
}
