/**
 * Auto-instrumentation for the OpenAI Node.js SDK (v4+).
 *
 * Patches Completions.prototype.create and AsyncCompletions is handled via the same
 * prototype since the SDK uses a unified async API. Streaming calls (stream: true)
 * are passed through without instrumentation.
 */
import type { EventSender } from '../client'
import { calculateCost, type NelvraEvent, type NelvraMetadata } from '../types'

let _sender: EventSender | null = null
let _environment = 'production'
let _patched = false

export function instrumentOpenAI(sender: EventSender, environment: string): void {
  if (_patched) return

  let Completions: any
  try {
    Completions = require('openai/resources/chat/completions').Completions
  } catch {
    return // openai not installed
  }

  _sender = sender
  _environment = environment

  const originalCreate = Completions.prototype.create

  Completions.prototype.create = async function (body: any, options?: any): Promise<any> {
    if (body?.stream) {
      return originalCreate.call(this, body, options)
    }

    const nelvraMetadata: NelvraMetadata = body?.nelvra_metadata ?? {}
    const cleanBody = { ...body }
    delete cleanBody.nelvra_metadata

    const start = Date.now()
    const response = await originalCreate.call(this, cleanBody, options)
    const latencyMs = Date.now() - start

    captureOpenAIResponse(cleanBody, response, latencyMs, nelvraMetadata)
    return response
  }

  _patched = true
}

function captureOpenAIResponse(
  body: any,
  response: any,
  latencyMs: number,
  meta: NelvraMetadata,
): void {
  if (!_sender) return

  try {
    const messages: Array<Record<string, unknown>> = body?.messages ?? []
    const model: string = response.model ?? body?.model ?? 'unknown'
    const usage = response.usage

    const promptTokens: number = usage?.prompt_tokens ?? 0
    const completionTokens: number = usage?.completion_tokens ?? 0
    const totalTokens: number = usage?.total_tokens ?? 0

    const choice = response.choices?.[0]
    const responseText: string = choice?.message?.content ?? ''
    const finishReason: string = choice?.finish_reason ?? 'unknown'

    // OpenAI embeds the system message inside `messages`
    let systemPrompt: string | null = null
    for (const msg of messages) {
      if (msg.role === 'system' && typeof msg.content === 'string') {
        systemPrompt = msg.content
        break
      }
    }

    const event: NelvraEvent = {
      timestamp: new Date().toISOString(),
      model,
      provider: 'openai',
      messages,
      system_prompt: systemPrompt,
      response_text: responseText,
      finish_reason: finishReason,
      prompt_tokens: promptTokens,
      completion_tokens: completionTokens,
      total_tokens: totalTokens,
      cost_usd: calculateCost(model, promptTokens, completionTokens),
      latency_ms: latencyMs,
      environment: _environment,
      prompt_id: meta.prompt_id ?? null,
      user_id: meta.user_id ?? null,
      session_id: meta.session_id ?? null,
      feature: meta.feature ?? null,
      tags: meta.tags ?? [],
      custom_metadata: meta.metadata ?? {},
    }

    _sender.enqueue(event)
  } catch {
    // Instrumentation errors must never surface
    console.warn('Nelvra: error capturing OpenAI event')
  }
}

export function _resetForTesting(): void {
  _patched = false
  _sender = null
  try {
    // Reload the module to restore the original prototype method
    const mod = require.resolve('openai/resources/chat/completions')
    delete require.cache[mod]
  } catch {
    // ignore
  }
}
