import { getReview, OWRPError } from '@/lib/owrp'

type RouteProps = {
  params: Promise<{ auditId: string }>
}

export const dynamic = 'force-dynamic'

export async function GET(_request: Request, { params }: RouteProps) {
  const { auditId } = await params

  try {
    const review = await getReview(auditId)
    if (!review.recovery_capsule) {
      return Response.json({ error: 'capsule_not_found' }, { status: 404 })
    }

    const body = [
      '# Recovery Capsule',
      '',
      `Audit: ${review.audit_id}`,
      `Finding state: ${review.finding.state}`,
      `Inference state: ${review.inference.state}`,
      '',
      review.recovery_capsule.text,
      '',
      '---',
      'This capsule is derived from persisted source episodes. Estimated reuse does not establish realized labor savings or production ROI.',
      '',
    ].join('\n')

    return new Response(body, {
      status: 200,
      headers: {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Content-Disposition': `attachment; filename="recovery-${review.audit_id}.md"`,
        'Cache-Control': 'no-store',
      },
    })
  } catch (error) {
    if (error instanceof OWRPError) {
      const status = error.kind === 'not_found' ? 404 : error.kind === 'unauthorized' ? 401 : 502
      return Response.json({ error: error.kind }, { status })
    }
    return Response.json({ error: 'unavailable' }, { status: 502 })
  }
}
