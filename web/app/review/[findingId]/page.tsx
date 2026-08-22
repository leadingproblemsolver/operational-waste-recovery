import { notFound } from 'next/navigation'
import { getFinding, OwrpApiError, type FindingEvent, type MeasurementState } from '../../../lib/owrp'

export const dynamic = 'force-dynamic'

function stateClass(state: MeasurementState): string {
  return state === 'ESTIMATED' ? 'estimated' : 'not-measurable'
}

function stateLabel(state: MeasurementState): string {
  return state.replaceAll('_', ' ')
}

function EventCard({ label, event }: { label: string; event: FindingEvent }) {
  return (
    <section className="card">
      <p className="eyebrow">OBSERVED · {label}</p>
      <h2>{event.event_id}</h2>
      <div className="meta">
        <span>Source: {event.source}</span>
        <span>Model: {event.model_name}</span>
        <span>Tokens: {event.total_tokens}</span>
        <span>Cost: ${event.cost_usd.toFixed(4)}</span>
        <span>Class: {event.classification}</span>
        <span>{event.timestamp}</span>
      </div>
      <h3>Prompt</h3>
      <pre>{event.prompt}</pre>
      <h3>Response</h3>
      <pre>{event.response}</pre>
    </section>
  )
}

export default async function ReviewPage({
  params,
}: {
  params: Promise<{ findingId: string }>
}) {
  const { findingId } = await params

  let finding
  try {
    finding = await getFinding(findingId)
  } catch (error) {
    if (error instanceof OwrpApiError && error.status === 404) notFound()
    const message = error instanceof Error ? error.message : 'Unknown upstream error'
    const code = error instanceof OwrpApiError ? error.code : 'unknown_error'
    return (
      <main>
        <p className="eyebrow">OWR Trace Inspector</p>
        <h1>Finding unavailable</h1>
        <section className="card warning">
          <h2>{code}</h2>
          <p className="lede">{message}</p>
          <p className="muted">
            No evidence is rendered when the backend is unauthorized, unavailable, or malformed.
          </p>
        </section>
      </main>
    )
  }

  const inferred = finding.inferred
  return (
    <main>
      <p className="eyebrow">OWR Trace Inspector · Human Review Surface</p>
      <h1>Potential repeated-work finding</h1>
      <p className="lede">
        Exact source interactions are shown as observed evidence. Waste and avoidable usage remain
        explicitly inferred estimates; similarity is not treated as proof of duplication.
      </p>

      <div className="toolbar">
        <span className={`badge ${stateClass(finding.measurement_state)}`}>
          {stateLabel(finding.measurement_state)}
        </span>
        <span className="badge">Finding {finding.finding_id}</span>
        <span className="badge">Repository {finding.repo_id}</span>
        {finding.capsule ? (
          <a className="button" href={`/review/${encodeURIComponent(finding.finding_id)}/capsule`}>
            Download Recovery Capsule
          </a>
        ) : null}
      </div>

      <div className="grid">
        <EventCard label="Episode A" event={finding.observed.left} />
        <EventCard label="Episode B" event={finding.observed.right} />

        <section className="card full">
          <p className="eyebrow">INFERRED · requires human judgment</p>
          <h2>Potential rework</h2>
          <p className="lede">{inferred.basis}</p>
          <div className="metrics">
            <div className="metric">
              <span className="muted">Prompt similarity</span>
              <strong>{(finding.observed.similarity * 100).toFixed(1)}%</strong>
            </div>
            <div className="metric">
              <span className="muted">Avoidable tokens</span>
              <strong>
                {inferred.avoidable_tokens === null ? 'Not measurable' : inferred.avoidable_tokens}
              </strong>
              <span className={`badge ${stateClass(inferred.token_measurement_state)}`}>
                {stateLabel(inferred.token_measurement_state)}
              </span>
            </div>
            <div className="metric">
              <span className="muted">Avoidable cost</span>
              <strong>
                {inferred.avoidable_cost_usd === null
                  ? 'Not measurable'
                  : `$${inferred.avoidable_cost_usd.toFixed(4)}`}
              </strong>
              <span className={`badge ${stateClass(inferred.cost_measurement_state)}`}>
                {stateLabel(inferred.cost_measurement_state)}
              </span>
            </div>
          </div>
        </section>

        {finding.capsule ? (
          <section className="card full">
            <p className="eyebrow">RECOVERY CAPSULE · ESTIMATED</p>
            <h2>Context to review before reconstructing the same work</h2>
            <pre>{finding.capsule.text}</pre>
            <div className="meta">
              <span>Sources: {finding.capsule.source_count}</span>
              <span>Estimated tokens saved: {finding.capsule.estimated_tokens_saved}</span>
            </div>
          </section>
        ) : null}
      </div>
    </main>
  )
}
