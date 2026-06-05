import type { NelvraEvent } from './types'

const BATCH_SIZE = 10
const FLUSH_INTERVAL_MS = 5_000
const QUEUE_MAX_SIZE = 10_000
const SEND_TIMEOUT_MS = 10_000

export class EventSender {
  private readonly apiKey: string
  private readonly apiUrl: string
  private readonly queue: NelvraEvent[] = []
  private flushTimer: ReturnType<typeof setInterval> | null = null

  constructor(apiKey: string, apiUrl: string) {
    this.apiKey = apiKey
    this.apiUrl = apiUrl
    this.flushTimer = setInterval(() => this.flush(), FLUSH_INTERVAL_MS)
    // Allow the process to exit even if timer is running
    if (this.flushTimer.unref) {
      this.flushTimer.unref()
    }
  }

  enqueue(event: NelvraEvent): void {
    if (this.queue.length >= QUEUE_MAX_SIZE) return // drop silently
    this.queue.push(event)
    if (this.queue.length >= BATCH_SIZE) {
      this.flush()
    }
  }

  flush(): void {
    if (this.queue.length === 0) return
    const batch = this.queue.splice(0, BATCH_SIZE)
    this.send(batch).catch(() => {
      // Warn without exposing sensitive event data
      console.warn(`Nelvra: failed to send ${batch.length} event(s). They have been dropped.`)
    })
  }

  private async send(events: NelvraEvent[]): Promise<void> {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), SEND_TIMEOUT_MS)

    try {
      const resp = await fetch(`${this.apiUrl}/v1/events/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify({ events }),
        signal: controller.signal,
      })
      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`)
      }
    } finally {
      clearTimeout(timeout)
    }
  }

  destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer)
      this.flushTimer = null
    }
    // Best-effort flush on destroy
    this.flush()
  }
}

export interface NelvraOptions {
  apiKey: string
  apiUrl?: string
  environment?: string
}

export class Nelvra {
  private static _instance: Nelvra | null = null

  private readonly apiKey: string
  readonly apiUrl: string
  readonly environment: string
  readonly sender: EventSender
  private _instrumented = false

  constructor(options: NelvraOptions) {
    if (!options.apiKey) throw new Error('apiKey is required')
    this.apiKey = options.apiKey
    this.apiUrl = (options.apiUrl ?? 'https://api.nelvra.io').replace(/\/$/, '')
    this.environment = options.environment ?? 'production'
    this.sender = new EventSender(this.apiKey, this.apiUrl)
    Nelvra._instance = this
  }

  instrument(): void {
    if (this._instrumented) return

    const { instrumentOpenAI } = require('./instruments/openai')
    const { instrumentAnthropic } = require('./instruments/anthropic')

    instrumentOpenAI(this.sender, this.environment)
    instrumentAnthropic(this.sender, this.environment)

    this._instrumented = true
  }

  static getInstance(): Nelvra | null {
    return Nelvra._instance
  }
}
