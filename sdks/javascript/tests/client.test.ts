import { describe, it, expect, vi, beforeEach } from 'vitest'
import { Nelvra, EventSender } from '../src/client'
import type { NelvraEvent } from '../src/types'

const sampleEvent: NelvraEvent = {
  timestamp: new Date().toISOString(),
  model: 'gpt-4o',
  provider: 'openai',
  messages: [{ role: 'user', content: 'hello' }],
  response_text: 'hi',
  finish_reason: 'stop',
  prompt_tokens: 10,
  completion_tokens: 5,
  total_tokens: 15,
  latency_ms: 200,
  environment: 'production',
}

describe('Nelvra', () => {
  it('throws if apiKey is empty', () => {
    expect(() => new Nelvra({ apiKey: '' })).toThrow('apiKey is required')
  })

  it('sets the global instance', () => {
    const client = new Nelvra({ apiKey: 'nvl_live_test', apiUrl: 'http://localhost:1' })
    expect(Nelvra.getInstance()).toBe(client)
  })

  it('strips trailing slash from apiUrl', () => {
    const client = new Nelvra({ apiKey: 'nvl_live_test', apiUrl: 'http://localhost:8000/' })
    expect(client.apiUrl).toBe('http://localhost:8000')
  })

  it('defaults environment to production', () => {
    const client = new Nelvra({ apiKey: 'nvl_live_test' })
    expect(client.environment).toBe('production')
  })

  it('instrument is idempotent', () => {
    vi.mock('../src/instruments/openai', () => ({ instrumentOpenAI: vi.fn() }))
    vi.mock('../src/instruments/anthropic', () => ({ instrumentAnthropic: vi.fn() }))

    const client = new Nelvra({ apiKey: 'nvl_live_test', apiUrl: 'http://localhost:1' })
    client.instrument()
    client.instrument() // second call should not throw
  })
})

describe('EventSender', () => {
  it('enqueues without blocking', () => {
    const sender = new EventSender('key', 'http://localhost:1')
    expect(() => sender.enqueue(sampleEvent)).not.toThrow()
  })

  it('drops events silently when queue is full', () => {
    const sender = new EventSender('key', 'http://localhost:1')
    // Fill well beyond the mock limit
    for (let i = 0; i < 20_000; i++) {
      sender.enqueue(sampleEvent)
    }
    // Should not throw
  })

  it('warns on failed send', async () => {
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    global.fetch = vi.fn().mockRejectedValue(new Error('connection refused'))

    const sender = new EventSender('key', 'http://localhost:1')
    await (sender as any).send([sampleEvent])

    expect(warnSpy).toHaveBeenCalledWith(expect.stringContaining('Nelvra'))
    warnSpy.mockRestore()
  })
})
