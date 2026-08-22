import { getFinding, OwrpApiError } from '../../../../lib/owrp'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ findingId: string }> }
) {
  const { findingId } = await params

  try {
    const finding = await getFinding(findingId)
    if (!finding.capsule) {
      return Response.json({ error: 'capsule_not_found' }, { status: 404 })
    }

    const safeId = finding.finding_id.replace(/[^a-zA-Z0-9_-]/g, '_')
    return new Response(finding.capsule.text, {
      status: 200,
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Disposition': `attachment; filename="recovery-capsule-${safeId}.txt"`,
        'Cache-Control': 'no-store',
      },
    })
  } catch (error) {
    if (error instanceof OwrpApiError) {
      return Response.json({ error: error.code }, { status: error.status })
    }
    return Response.json({ error: 'unknown_error' }, { status: 500 })
  }
}
