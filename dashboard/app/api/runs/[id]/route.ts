import { NextRequest, NextResponse } from 'next/server';
import { getRunDetails } from '@/lib/db';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const runId = parseInt(id);
    
    if (isNaN(runId)) {
      return NextResponse.json(
        { error: 'Invalid run ID' },
        { status: 400 }
      );
    }
    
    const runDetails = await getRunDetails(runId);
    
    if (!runDetails) {
      return NextResponse.json(
        { error: 'Run not found' },
        { status: 404 }
      );
    }
    
    // Extract miss, false_alarm, confusion from DER details (normalize by total)
    const derResults = runDetails.results.filter((r: any) => r.metric_name === 'der');
    const missValues = derResults
      .map((r: any) => r.details?.total ? r.details.miss / r.details.total : null)
      .filter((v: any) => v !== null && v !== undefined);
    const falseAlarmValues = derResults
      .map((r: any) => r.details?.total ? r.details.false_alarm / r.details.total : null)
      .filter((v: any) => v !== null && v !== undefined);
    const confusionValues = derResults
      .map((r: any) => r.details?.total ? r.details.confusion / r.details.total : null)
      .filter((v: any) => v !== null && v !== undefined);
    
    const calcMean = (values: number[]) => values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : null;
    
    // Group results by audio_file_id
    const fileMap = new Map<number, any>();
    runDetails.results.forEach((result: any) => {
      if (!fileMap.has(result.audio_file_id)) {
        fileMap.set(result.audio_file_id, {
          audio_file_id: result.audio_file_id,
          file_path: `file_${result.audio_file_id}`, // TODO: get actual file path
          metrics: {}
        });
      }
      const fileMetrics = fileMap.get(result.audio_file_id);
      if (result.metric_name === 'der') {
        fileMetrics.metrics.DER = result.value;
        const total = result.details?.total || 1;
        fileMetrics.metrics.miss = result.details?.miss !== undefined ? result.details.miss / total : null;
        fileMetrics.metrics.false_alarm = result.details?.false_alarm !== undefined ? result.details.false_alarm / total : null;
        fileMetrics.metrics.confusion = result.details?.confusion !== undefined ? result.details.confusion / total : null;
      } else if (result.metric_name === 'jer') {
        fileMetrics.metrics.JER = result.value;
      }
    });
    
    // Transform data to match frontend expectations
    const response = {
      id: runDetails.id,
      model_name: runDetails.model_name,
      dataset_name: runDetails.dataset_name || 'Unknown Dataset',
      dataset_id: runDetails.dataset_id,
      status: runDetails.status,
      started_at: runDetails.started_at,
      completed_at: runDetails.completed_at,
      duration_sec: runDetails.completed_at && runDetails.started_at
        ? (new Date(runDetails.completed_at).getTime() - new Date(runDetails.started_at).getTime()) / 1000
        : 0,
      metrics: {
        aggregate: {
          DER_mean: runDetails.stats?.der?.mean ?? null,
          DER_min: runDetails.stats?.der?.min ?? null,
          DER_max: runDetails.stats?.der?.max ?? null,
          DER_std: runDetails.stats?.der?.std ?? null,
          JER_mean: runDetails.stats?.jer?.mean ?? null,
          JER_min: runDetails.stats?.jer?.min ?? null,
          JER_max: runDetails.stats?.jer?.max ?? null,
          JER_std: runDetails.stats?.jer?.std ?? null,
          miss_mean: calcMean(missValues),
          false_alarm_mean: calcMean(falseAlarmValues),
          confusion_mean: calcMean(confusionValues),
          num_files: derResults.length,
        },
        per_file: Array.from(fileMap.values()),
      },
    };
    
    return NextResponse.json(response);
  } catch (error) {
    console.error('Error fetching run details:', error);
    return NextResponse.json(
      { error: 'Failed to fetch run details' },
      { status: 500 }
    );
  }
}
