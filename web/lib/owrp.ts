export type MeasurementState = 'OBSERVED' | 'NOT_MEASURABLE'

export type Episode = {
  event_id: string
  timestamp: string
  repo_id: string
  classification: string
  prompt_excerpt: string
  response_excerpt: string
}

export type RecoveryCapsule = {
  capsule_id: string
  text: string
  source_count: number
  estimated_tokens_saved: number
}

export type OWRReview = {
  audit_id: string
  measurement_state: MeasurementState
  finding: {
    state: 'OBSERVED'
    summary: string
  }
  evidence: {
    similarity: number
    avoidable_tokens: number
    avoidable_cost_usd: number
  }
  episode_a: Episode
  episode_b: Episode
  inference: {
    state: 'INFERRED'
    summary: string
  }
  recovery_capsule: RecoveryCapsule | null
}

export type OWRPErrorKind = 'not_found' | 'unauthorized' | 'malformed' | 'unavailable'

export class OWRPError extends Error {
  constructor(
    public readonly kind: OWRPErrorKind,
    message: string,
    public readonly status?: number
  ) {
    super(message)
    this.name = 'OWRPError'
  }
}

type FetchLike = typeof fetch

type ClientOptions = {
  baseUrl?: string
  token?: string
  fetcher?: FetchLike
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isString(value: unknown): value is string {
  return typeof value === 'string'
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

function isEpisode(value: unknown): value is Episode {
  return (
    isRecord(value) &&
    isString(value.event_id) &&
    isString(value.timestamp) &&
    isString(value.repo_id) &&
    isString(value.classification) &&
    isString(value.prompt_excerpt) &&
    isString(value.response_excerpt)
  )
}

function isRecoveryCapsule(value: unknown): value is RecoveryCapsule {
  return (
    isRecord(value) &&
    isString(value.capsule_id) &&
    isString(value.text) &&
    isFiniteNumber(value.source_count) &&
    Number.isInteger(value.source_count) &&
    value.source_count >= 0 &&
    isFiniteNumber(value.estimated_tokens_saved) &&
    Number.isInteger(value.estimated_tokens_saved) &&
    value.estimated_tokens_saved >= 0
  )
}

export function parseReview(value: unknown): OWRReview {
  if (!isRecord(value)) {
    throw new OWRPError('malformed', 'OWR returned a non-object review payload.')
  }

  const measurementState = value.measurement_state
  const finding = value.finding
  const evidence = value.evidence
  const inference = value.inference
  const capsule = value.recovery_capsule

  const valid =
    isString(value.audit_id) &&
    (measurementState === 'OBSERVED' || measurementState === 'NOT_MEASURABLE') &&
    isRecord(finding) &&
    finding.state === 'OBSERVED' &&
    isString(finding.summary) &&
    isRecord(evidence) &&
    isFiniteNumber(evidence.similarity) &&
    isFiniteNumber(evidence.avoidable_tokens) &&
    isFiniteNumber(evidence.avoidable_cost_usd) &&
    isEpisode(value.episode_a) &&
    isEpisode(value.episode_b) &&
    isRecord(inference) &&
    inference.state === 'INFERRED' &&
    isString(inference.summary) &&
    (capsule === null || isRecoveryCapsule(capsule))

  if (!valid) {
    throw new OWRPError('malformed', 'OWR review payload failed the TypeScript contract.')
  }

  return value as OWRReview
}

export async function getReview(auditId: string, options: ClientOptions = {}): Promise<OWRReview> {
  const baseUrl = (options.baseUrl ?? process.env.OWRP_API_URL ?? 'http://127.0.0.1:8787').replace(
    /\/$/,
    ''
  )
  const token = options.token ?? process.env.OWRP_API_TOKEN
  const fetcher = options.fetcher ?? fetch
  const headers = new Headers()
  headers.set('Accept', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetcher(`${baseUrl}/api/review/${encodeURIComponent(auditId)}`, {
      method: 'GET',
      headers,
      cache: 'no-store',
    })
  } catch (error) {
    throw new OWRPError(
      'unavailable',
      `OWR request failed before a response was received: ${error instanceof Error ? error.message : 'unknown error'}`
    )
  }

  if (response.status === 404) {
    throw new OWRPError('not_found', 'No persisted review exists for this audit ID.', 404)
  }
  if (response.status === 401 || response.status === 403) {
    throw new OWRPError('unauthorized', 'OWR rejected the review request.', response.status)
  }
  if (!response.ok) {
    throw new OWRPError('unavailable', `OWR returned HTTP ${response.status}.`, response.status)
  }

  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new OWRPError('malformed', 'OWR returned a non-JSON success response.', response.status)
  }

  return parseReview(payload)
}
