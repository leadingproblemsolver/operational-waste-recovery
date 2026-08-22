import { describe, expect, it } from 'vitest'
import { getFinding, OwrpApiError, type Finding } from './owrp'

function finding(overrides: Partial<Finding> = {}): Finding {
  const base: Finding = {
    finding_id: 'pair-1',
    repo_id: 'repo-1',
    measurement_state: 'ESTIMATED',
    observed: {
      similarity: 0.91,
      left: {
        event_id: 'left',
        timestamp: '2026-08-22T18:00:00+00:00',
        source: 'codex',
        model_name: 'model-a',
        prompt: 'debug retry loop',
        response: 'first response',
        total_tokens: 12,
        cost_usd: 0.04,
        classification: 'unclassified',
      },
      right: {
        event_id: 'right',
        timestamp: '2026-08-22T18:02:00+00:00',
        source: 'codex',
        model_name: 'model-a',
        prompt: 'debug retry loop again',
        response: 'second response',
        total_tokens: 12,
        cost_usd: 0.04,
        classification: 'unclassified',
      },
    },
    inferred: {
      label: 'potential_rework',
      avoidable_tokens: 12,
      avoidable_cost_usd: 0.04,
      token_measurement_state: 'ESTIMATED',
      cost_measurement_state: 'ESTIMATED',
      basis: 'Derived estimate, not realized savings.',
    },
    capsule: {
      capsule_id: 'capsule-1',
      text: 'Review retry context before debugging again.',
      source_count: 2,
      estimated_tokens_saved: 8,
      measurement_state: 'ESTIMATED',
    },
  }
  return { ...base, ...overrides }
}

function jsonFetch(payload: unknown, status = 200): typeof fetch {
  return (async () =>
    new Response(JSON.stringify(payload), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })) as typeof fetch
}

describe('getFinding', () => {
  it('loads a valid finding and sends the server-side bearer token', async () => {
    let authorization: string | null = null
    const fetcher = (async (_input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers)
      authorization = headers.get('Authorization')
      return new Response(JSON.stringify(finding()), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const result = await getFinding('pair-1', {
      baseUrl: 'http://owrp.test',
      token: 'secret-token',
      fetcher,
    })

    expect(result.finding_id).toBe('pair-1')
    expect(result.observed.left.prompt).toBe('debug retry loop')
    expect(authorization).toBe('Bearer secret-token')
  })

  it('preserves a missing finding as a typed 404', async () => {
    await expect(
      getFinding('missing', {
        baseUrl: 'http://owrp.test',
        fetcher: jsonFetch({ error: 'finding_not_found' }, 404),
      })
    ).rejects.toMatchObject<OwrpApiError>({
      status: 404,
      code: 'finding_not_found',
    })
  })

  it('rejects a malformed success payload instead of rendering invented evidence', async () => {
    await expect(
      getFinding('pair-1', {
        baseUrl: 'http://owrp.test',
        fetcher: jsonFetch({ finding_id: 'pair-1', observed: {} }),
      })
    ).rejects.toMatchObject<OwrpApiError>({
      status: 502,
      code: 'malformed_response',
    })
  })

  it('surfaces upstream authorization failure distinctly', async () => {
    await expect(
      getFinding('pair-1', {
        baseUrl: 'http://owrp.test',
        fetcher: jsonFetch({ error: 'unauthorized' }, 401),
      })
    ).rejects.toMatchObject<OwrpApiError>({
      status: 401,
      code: 'unauthorized',
    })
  })

  it('preserves NOT_MEASURABLE instead of coercing absent telemetry to zero savings', async () => {
    const unmeasurable = finding({
      measurement_state: 'NOT_MEASURABLE',
      inferred: {
        label: 'potential_rework',
        avoidable_tokens: null,
        avoidable_cost_usd: null,
        token_measurement_state: 'NOT_MEASURABLE',
        cost_measurement_state: 'NOT_MEASURABLE',
        basis: 'Telemetry unavailable.',
      },
    })

    const result = await getFinding('pair-1', {
      baseUrl: 'http://owrp.test',
      fetcher: jsonFetch(unmeasurable),
    })

    expect(result.measurement_state).toBe('NOT_MEASURABLE')
    expect(result.inferred.avoidable_tokens).toBeNull()
    expect(result.inferred.avoidable_cost_usd).toBeNull()
  })
})
