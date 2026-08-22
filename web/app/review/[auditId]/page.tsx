import { getReview, OWRPError, type OWRReview } from '@/lib/owrp'

export const dynamic = 'force-dynamic'

type PageProps = {
  params: Promise<{ auditId: string }>
}

function failureCopy(error: OWRPError): { title: string; detail: string } {
  switch (error.kind) {
    case 'not_found':
      return {
        title: 'Review not found',
        detail: 'No persisted duplicate-work finding exists for this audit ID.',
      }
    case 'unauthorized':
      return {
        title: 'Review access denied',
        detail: 'The OWR backend rejected this server-side request. Check the configured API token.',
      }
    case 'malformed':
      return {
        title: 'Backend contract mismatch',
        detail: 'OWR returned HTTP success, but the payload did not satisfy the review contract.',
      }
    case 'unavailable':
      return {
        title: 'Review temporarily unavailable',
        detail: 'The OWR backend could not supply a trustworthy review response.',
      }
  }
}

function EpisodeCard({ label, episode }: { label: string; episode: OWRReview['episode_a'] }) {
  return (
    <article className="episode">
      <div className="eyebrow">{label}</div>
      <dl className="meta">
        <div><dt>Event</dt><dd>{episode.event_id}</dd></div>
        <div><dt>Repository</dt><dd>{episode.repo_id}</dd></div>
        <div><dt>Class</dt><dd>{episode.classification}</dd></div>
        <div><dt>Timestamp</dt><dd>{episode.timestamp}</dd></div>
      </dl>
      <h3>Prompt evidence</h3>
      <pre>{episode.prompt_excerpt}</pre>
      <h3>Response evidence</h3>
      <pre>{episode.response_excerpt}</pre>
    </article>
  )
}

function Review({ review }: { review: OWRReview }) {
  const isMeasured = review.measurement_state === 'OBSERVED'

  return (
    <main>
      <header className="hero">
        <div>
          <div className="eyebrow">ReworkTrace / persisted review</div>
          <h1>Repeated-work finding</h1>
          <p className="audit">Audit {review.audit_id}</p>
        </div>
        <span className={`state ${isMeasured ? '' : 'state-muted'}`}>{review.measurement_state}</span>
      </header>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Finding · {review.finding.state}</div>
            <h2>{review.finding.summary}</h2>
          </div>
        </div>
        {isMeasured ? (
          <div className="metrics">
            <div><span>Similarity</span><strong>{(review.evidence.similarity * 100).toFixed(1)}%</strong></div>
            <div><span>Avoidable tokens</span><strong>{review.evidence.avoidable_tokens.toLocaleString()}</strong></div>
            <div><span>Measured duplicate cost</span><strong>${review.evidence.avoidable_cost_usd.toFixed(4)}</strong></div>
          </div>
        ) : (
          <p className="notice">Impact measurement is not available for this review. No cost or savings claim is promoted.</p>
        )}
      </section>

      <section className="episodes">
        <EpisodeCard label="Episode A · exact source evidence" episode={review.episode_a} />
        <EpisodeCard label="Episode B · exact source evidence" episode={review.episode_b} />
      </section>

      <section className="panel inference">
        <div className="eyebrow">Interpretation · {review.inference.state}</div>
        <p>{review.inference.summary}</p>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <div className="eyebrow">Recovery Capsule</div>
            <h2>{review.recovery_capsule ? 'Reusable context is available' : 'No capsule persisted'}</h2>
          </div>
          {review.recovery_capsule ? (
            <a className="button" href={`/review/${encodeURIComponent(review.audit_id)}/capsule`}>Download capsule</a>
          ) : null}
        </div>
        {review.recovery_capsule ? (
          <>
            <pre className="capsule">{review.recovery_capsule.text}</pre>
            <p className="footnote">
              Built from {review.recovery_capsule.source_count} persisted sources. Estimated capsule-token reuse is a deterministic model output, not realized labor savings.
            </p>
          </>
        ) : (
          <p className="notice">The finding remains inspectable even without a generated recovery capsule.</p>
        )}
      </section>
    </main>
  )
}

export default async function ReviewPage({ params }: PageProps) {
  const { auditId } = await params

  try {
    return <Review review={await getReview(auditId)} />
  } catch (error) {
    const typed = error instanceof OWRPError
      ? error
      : new OWRPError('unavailable', 'Unexpected review rendering failure.')
    const copy = failureCopy(typed)
    return (
      <main className="failure">
        <div className="eyebrow">ReworkTrace / {typed.kind}</div>
        <h1>{copy.title}</h1>
        <p>{copy.detail}</p>
        <code>{auditId}</code>
      </main>
    )
  }
}
