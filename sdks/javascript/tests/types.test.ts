import { describe, it, expect } from 'vitest'
import { calculateCost } from '../src/types'

describe('calculateCost', () => {
  it('returns null for unknown models', () => {
    expect(calculateCost('some-future-model', 100, 50)).toBeNull()
  })

  it('calculates gpt-4o cost correctly', () => {
    // 1000 input * $5/1M + 500 output * $15/1M = $0.005 + $0.0075 = $0.0125
    const cost = calculateCost('gpt-4o', 1000, 500)
    expect(cost).toBeCloseTo(0.0125, 5)
  })

  it('calculates anthropic cost correctly', () => {
    // 500 input * $3/1M + 200 output * $15/1M = $0.0015 + $0.003 = $0.0045
    const cost = calculateCost('claude-3-5-sonnet-20241022', 500, 200)
    expect(cost).toBeCloseTo(0.0045, 5)
  })

  it('handles zero tokens', () => {
    const cost = calculateCost('gpt-4o', 0, 0)
    expect(cost).toBe(0)
  })

  it('returns a number with max 8 decimal places', () => {
    const cost = calculateCost('gpt-4o-mini', 1, 1)
    expect(cost).not.toBeNull()
    const str = cost!.toString()
    const decimals = str.includes('.') ? str.split('.')[1].length : 0
    expect(decimals).toBeLessThanOrEqual(8)
  })
})
