/**
 * Auto-instrumentation for the Anthropic Node.js SDK (v0.20+).
 *
 * Patches Messages.prototype.create. Streaming calls (stream: true) pass through.
 */
import type { EventSender } from '../client'
import { calculateCost, type NelvraEvent, type NelvraMetadata } from '../types'

let _sender: EventSender | null = null
let _environment = 'production'
let _patched = false

export function instrumentAnthropic(sender: EventSender, environment: string): void {
  if (_patched) return

  let Messages: any
  try {
    Messages = require('@anthropic-ai/sdk/resources/messages').Messages
  } catch {
    return // anthropic not installed
  }

  _sender = sender
  _environment = environment

  const originalCreate = Messages.prototype.create

  Messages.prototype.create = async function (body: any, options?: any): Promise<any> {
    if (body?.stream) {
      return originalCreate.call(this, body, options)
    }

    const nelvraMetadata: NelvraMetadata = body?.nelvra_metadata ?? {}
    const cleanBody = { ...body }
    delete cleanBody.nelvra_metadata

    const start = Date.now()
    const response = await originalCreate.call(this, cleanBody, options)
    const latencyMs = Date.now() - start

    captureAnthropicResponse(cleanBody, response, latencyMs, nelvraMetadata)
    return response
  }

  _patched = true
}

function captureAnthropicResponse(
  body: any,
  response: any,
  latencyMs: number,
  meta: NelvraMetadata,
): void {
  if (!_sender) return

  try {
    const messages: Array<Record<string, unknown>> = body?.messages ?? []
    const systemPrompt: string | null = body?.system ?? null
    const model: string = response.model ?? body?.model ?? 'unknown'
    const usage = response.usage

    const promptTokens: number = usage?.input_tokens ?? 0
    const completionTokens: number = usage?.output_tokens ?? 0
    const totalTokens = promptTokens + completionTokens

    const textBlocks: string[] = (response.content ?? [])
      .filter((b: any) => b.type === 'text')
      .map((b: any) => b.text as string)
    const responseText = textBlocks.join('')
    const finishReason: string = response.stop_reason ?? 'unknown'

    const event: NelvraEvent = {
      timestamp: new Date().toISOString(),
      model,
      provider: 'anthropic',
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
    console.warn('Nelvra: error capturing Anthropic event')
  }
}

export function _resetForTesting(): void {
  _patched = false
  _sender = null
  try {
    const mod = require.resolve('@anthropic-ai/sdk/resources/messages')
    delete require.cache[mod]
  } catch {
    // ignore
  }
}
