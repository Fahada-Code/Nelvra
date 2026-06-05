export interface NelvraEvent {
  timestamp: string
  model: string
  provider: 'openai' | 'anthropic'
  messages: Array<Record<string, unknown>>
  response_text: string
  finish_reason: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  latency_ms: number
  environment: string
  system_prompt?: string | null
  prompt_id?: string | null
  cost_usd?: number | null
  user_id?: string | null
  session_id?: string | null
  feature?: string | null
  tags?: string[]
  custom_metadata?: Record<string, unknown>
}

export interface NelvraMetadata {
  prompt_id?: string
  user_id?: string
  session_id?: string
  feature?: string
  tags?: string[]
  metadata?: Record<string, unknown>
}

/** Pricing in USD per 1M tokens */
const COST_PER_1M: Record<string, { input: number; output: number }> = {
  // OpenAI
  'gpt-4o': { input: 5.0, output: 15.0 },
  'gpt-4o-2024-08-06': { input: 2.5, output: 10.0 },
  'gpt-4o-mini': { input: 0.15, output: 0.6 },
  'gpt-4-turbo': { input: 10.0, output: 30.0 },
  'gpt-4': { input: 30.0, output: 60.0 },
  'gpt-3.5-turbo': { input: 0.5, output: 1.5 },
  // Anthropic
  'claude-opus-4-8': { input: 15.0, output: 75.0 },
  'claude-sonnet-4-6': { input: 3.0, output: 15.0 },
  'claude-haiku-4-5-20251001': { input: 0.8, output: 4.0 },
  'claude-3-5-sonnet-20241022': { input: 3.0, output: 15.0 },
  'claude-3-5-haiku-20241022': { input: 0.8, output: 4.0 },
  'claude-3-opus-20240229': { input: 15.0, output: 75.0 },
  'claude-3-haiku-20240307': { input: 0.25, output: 1.25 },
}

export function calculateCost(
  model: string,
  promptTokens: number,
  completionTokens: number,
): number | null {
  const pricing = COST_PER_1M[model]
  if (!pricing) return null
  const cost = (promptTokens * pricing.input + completionTokens * pricing.output) / 1_000_000
  return Math.round(cost * 1e8) / 1e8
}
