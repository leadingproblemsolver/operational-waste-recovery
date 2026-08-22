import { describe, expect, it, vi } from 'vitest'
import { getReview, OWRPError, parseReview } from './owrp'

const auditId = '0123456789abcdef01234567'

const observedReview = {
  audit_id: auditId,
  measurement_state: 'OBSERVED',
  finding: {
    state: 'OBSERVED',
    summary: 'Repeated-work pair detected by deterministic prompt similarity.',
  },
  evidence: {
    similarity: 0.8,
    avoidable_tokens: 120,
    avoidable_cost_usd: 0.42,
  },
  episode_a: {
    event_id: 'a',
    timestamp: '2026-08-22T12:00:00Z',
    repo_id: 'reworktrace',
    classification: 'debugging',
    prompt_excerpt: 'debug timeout',
    response_excerpt: 'inspected cache',
  },
  episode_b: {
    event_id: 'b',
    timestamp: '2026-08-22T13:00:00Z',
    repo_id: 'reworktrace',
    classification: 'debugging',
    prompt_excerpt: 'debug timeout again',
    response_excerpt: 'reconstructed cache context',
  },
  inference: {
    state: 'INFERRED',
    summary: 'This pair may represent avoidable context reconstruction.',
  },
  recovery_capsule: {
    capsule_id: 'capsule-1',
    text: 'Repository: reworktrace\nReview this capsule before reconstructing the same context.',
    source_count: 2,
    estimated_tokens_saved: 90,
  },
} as const

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

async function expectKind(promise: Promise<unknown>, kind: OWRPError['kind']) {
  try {
    await promise
  } catch (error) {
    expect(error).toBeInstanceOf(OWRPError)
    expect((error as OWRPError).kind).toBe(kind)
    return
  }
  throw new Error(`expected ${kind} error`)
}

describe('getReview', () => {
  it('returns a validated persisted review on the happy path', async () => {
    const fetcher = vi.fn(async () => jsonResponse(observedReview)) as unknown as typeof fetch

    const review = await getReview(auditId, {
      baseUrl: 'https://owr.example.test',
      token: 'secret',
      fetcher,
    })

    expect(review.audit_id).toBe(auditId)
    expect(review.measurement_state).toBe('OBSERVED')
    expect(review.evidence.avoidable_tokens).toBe(120)
    expect(fetcher).toHaveBeenCalledWith(
      `https://owr.example.test/api/review/${auditId}`,
      expect.objectContaining({ method: 'GET', cache: 'no-store' })
    )
    const request = fetcher.mock.calls[0][1]
    expect((request?.headers as Headers).get('Authorization')).toBe('Bearer secret')
  })

  it('classifies a missing persisted finding as not_found', async () => {
    const fetcher = vi.fn(async () => jsonResponse({ error: 'review_not_found' }, 404)) as unknown as typeof fetch
    await expectKind(getReview(auditId, { fetcher }), 'not_found')
  })

  it('rejects malformed success responses instead of trusting HTTP 200', async () => {
    const fetcher = vi.fn(async () =>
      new Response('{not valid json', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    ) as unknown as typeof fetch
    await expectKind(getReview(auditId, { fetcher }), 'malformed')
  })

  it('keeps authorization failure distinct from missing data', async () => {
    const fetcher = vi.fn(async () => jsonResponse({ error: 'unauthorized' }, 401)) as unknown as typeof fetch
    await expectKind(getReview(auditId, { fetcher }), 'unauthorized')
  })

  it('preserves NOT_MEASURABLE rather than promoting it to observed impact', () => {
    const review = parseReview({
      ...observedReview,
      measurement_state: 'NOT_MEASURABLE',
    })
    expect(review.measurement_state).toBe('NOT_MEASURABLE')
    expect(review.finding.state).toBe('OBSERVED')
    expect(review.inference.state).toBe('INFERRED')
  })
})
