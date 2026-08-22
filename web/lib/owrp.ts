export type MeasurementState = 'ESTIMATED' | 'NOT_MEASURABLE'

export interface FindingEvent {
  event_id: string
  timestamp: string
  source: string
  model_name: string
  prompt: string
  response: string
  total_tokens: number
  cost_usd: number
  classification: string
}

export interface Finding {
  finding_id: string
  repo_id: string
  measurement_state: MeasurementState
  observed: {
    similarity: number
    left: FindingEvent
    right: FindingEvent
  }
  inferred: {
    label: 'potential_rework'
    avoidable_tokens: number | null
    avoidable_cost_usd: number | null
    token_measurement_state: MeasurementState
    cost_measurement_state: MeasurementState
    basis: string
  }
  capsule: {
    capsule_id: string
    text: string
    source_count: number
    estimated_tokens_saved: number
    measurement_state: 'ESTIMATED'
  } | null
}

export class OwrpApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string
  ) {
    super(message)
    this.name = 'OwrpApiError'
  }
}

type FetchLike = typeof fetch

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isMeasurementState(value: unknown): value is MeasurementState {
  return value === 'ESTIMATED' || value === 'NOT_MEASURABLE'
}

function isFindingEvent(value: unknown): value is FindingEvent {
  if (!isRecord(value)) return false
  return (
    typeof value.event_id === 'string' &&
    typeof value.timestamp === 'string' &&
    typeof value.source === 'string' &&
    typeof value.model_name === 'string' &&
    typeof value.prompt === 'string' &&
    typeof value.response === 'string' &&
    typeof value.total_tokens === 'number' &&
    typeof value.cost_usd === 'number' &&
    typeof value.classification === 'string'
  )
}

export function parseFinding(value: unknown): Finding {
  if (!isRecord(value)) {
    throw new OwrpApiError('OWRP returned a non-object finding payload', 502, 'malformed_response')
  }
  if (!isRecord(value.observed) || !isFindingEvent(value.observed.left) || !isFindingEvent(value.observed.right)) {
    throw new OwrpApiError('OWRP finding is missing observed evidence', 502, 'malformed_response')
  }
  if (!isRecord(value.inferred)) {
    throw new OwrpApiError('OWRP finding is missing inferred evidence', 502, 'malformed_response')
  }
  if (
    typeof value.finding_id !== 'string' ||
    typeof value.repo_id !== 'string' ||
    !isMeasurementState(value.measurement_state) ||
    typeof value.observed.similarity !== 'number' ||
    value.inferred.label !== 'potential_rework' ||
    !isMeasurementState(value.inferred.token_measurement_state) ||
    !isMeasurementState(value.inferred.cost_measurement_state) ||
    typeof value.inferred.basis !== 'string'
  ) {
    throw new OwrpApiError('OWRP finding fields are malformed', 502, 'malformed_response')
  }

  const avoidableTokens = value.inferred.avoidable_tokens
  const avoidableCost = value.inferred.avoidable_cost_usd
  if (avoidableTokens !== null && typeof avoidableTokens !== 'number') {
    throw new OwrpApiError('OWRP avoidable_tokens is malformed', 502, 'malformed_response')
  }
  if (avoidableCost !== null && typeof avoidableCost !== 'number') {
    throw new OwrpApiError('OWRP avoidable_cost_usd is malformed', 502, 'malformed_response')
  }

  const capsule = value.capsule
  if (capsule !== null) {
    if (
      !isRecord(capsule) ||
      typeof capsule.capsule_id !== 'string' ||
      typeof capsule.text !== 'string' ||
      typeof capsule.source_count !== 'number' ||
      typeof capsule.estimated_tokens_saved !== 'number' ||
      capsule.measurement_state !== 'ESTIMATED'
    ) {
      throw new OwrpApiError('OWRP capsule is malformed', 502, 'malformed_response')
    }
  }

  return value as unknown as Finding
}

export async function getFinding(
  findingId: string,
  options: {
    baseUrl?: string
    token?: string
    fetcher?: FetchLike
  } = {}
): Promise<Finding> {
  const baseUrl = (options.baseUrl ?? process.env.OWRP_API_BASE_URL ?? 'http://127.0.0.1:8787').replace(/\/$/, '')
  const token = options.token ?? process.env.OWRP_API_TOKEN
  const fetcher = options.fetcher ?? fetch
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined

  let response: Response
  try {
    response = await fetcher(`${baseUrl}/api/findings/${encodeURIComponent(findingId)}`, {
      headers,
      cache: 'no-store',
    })
  } catch (error) {
    throw new OwrpApiError(
      `OWRP request failed: ${error instanceof Error ? error.message : 'unknown error'}`,
      502,
      'upstream_unavailable'
    )
  }

  if (response.status === 404) {
    throw new OwrpApiError('Finding not found', 404, 'finding_not_found')
  }
  if (response.status === 401 || response.status === 403) {
    throw new OwrpApiError('OWRP authorization failed', response.status, 'unauthorized')
  }
  if (!response.ok) {
    throw new OwrpApiError(`OWRP returned HTTP ${response.status}`, response.status, 'upstream_error')
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new OwrpApiError('OWRP returned invalid JSON', 502, 'malformed_response')
  }
  return parseFinding(payload)
}
