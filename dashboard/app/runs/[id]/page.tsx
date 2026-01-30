'use client';

import { useEffect, useState } from 'react';
import { use } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { StatusBadge } from '@/components/StatusBadge';
import { formatDuration, formatPercent, formatDate } from '@/lib/utils';

interface RunDetails {
  id: number;
  model_name: string;
  dataset_name: string;
  dataset_id: number;
  status: string;
  started_at: string;
  completed_at: string;
  duration_sec: number;
  metrics: {
    aggregate: Record<string, number>;
    per_file: Array<{
      audio_file_id: number;
      file_path: string;
      metrics: Record<string, number>;
    }>;
  };
}

export default function RunDetailsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const [run, setRun] = useState<RunDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/runs/${resolvedParams.id}`)
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          setError(data.error);
        } else {
          setRun(data);
        }
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load run details');
        setLoading(false);
        console.error(err);
      });
  }, [resolvedParams.id]);

  if (loading) {
    return <div className="text-center py-12">Loading run details...</div>;
  }

  if (error || !run) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error || 'Run not found'}</p>
        <Link href="/" className="text-blue-600 hover:underline mt-4 inline-block">
          ← Back to runs list
        </Link>
      </div>
    );
  }

  const getFileName = (path: string) => {
    return path.split('/').pop() || path;
  };

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link href="/" className="text-blue-600 hover:underline">
        ← Back to runs list
      </Link>

      {/* Run Info */}
      <div>
        <h2 className="text-3xl font-bold mb-2">Run #{run.id}</h2>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span>Model: <span className="font-semibold text-foreground">{run.model_name}</span></span>
          <span>Dataset: <span className="font-semibold text-foreground">{run.dataset_name}</span></span>
          <span><StatusBadge status={run.status} /></span>
        </div>
        <div className="flex gap-4 text-sm text-muted-foreground mt-2">
          <span>Started: {formatDate(run.started_at)}</span>
          <span>Duration: {formatDuration(run.duration_sec)}</span>
        </div>
      </div>

      {/* Aggregate Metrics Cards */}
      <div>
        <h3 className="text-xl font-semibold mb-4">Aggregate Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">DER</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.DER_mean !== undefined 
                  ? formatPercent(run.metrics.aggregate.DER_mean)
                  : 'N/A'}
              </div>
              {run.metrics.aggregate.DER_std !== undefined && (
                <p className="text-xs text-muted-foreground mt-1">
                  σ = {formatPercent(run.metrics.aggregate.DER_std)}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">JER</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.JER_mean !== undefined
                  ? formatPercent(run.metrics.aggregate.JER_mean)
                  : 'N/A'}
              </div>
              {run.metrics.aggregate.JER_std !== undefined && (
                <p className="text-xs text-muted-foreground mt-1">
                  σ = {formatPercent(run.metrics.aggregate.JER_std)}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Miss Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.miss_mean !== undefined
                  ? formatPercent(run.metrics.aggregate.miss_mean)
                  : 'N/A'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">False Alarm</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.false_alarm_mean !== undefined
                  ? formatPercent(run.metrics.aggregate.false_alarm_mean)
                  : 'N/A'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Confusion</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.confusion_mean !== undefined
                  ? formatPercent(run.metrics.aggregate.confusion_mean)
                  : 'N/A'}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Files Evaluated</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {run.metrics.aggregate.num_files !== undefined
                  ? Math.round(run.metrics.aggregate.num_files)
                  : run.metrics.per_file.length}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Per-file Results */}
      {run.metrics.per_file.length > 0 && (
        <div>
          <h3 className="text-xl font-semibold mb-4">Per-file Results</h3>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead className="text-right">DER</TableHead>
                  <TableHead className="text-right">JER</TableHead>
                  <TableHead className="text-right">Miss</TableHead>
                  <TableHead className="text-right">False Alarm</TableHead>
                  <TableHead className="text-right">Confusion</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {run.metrics.per_file.map((file) => (
                  <TableRow key={file.audio_file_id}>
                    <TableCell className="font-medium">
                      {getFileName(file.file_path)}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {file.metrics.DER !== undefined ? formatPercent(file.metrics.DER) : '-'}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {file.metrics.JER !== undefined ? formatPercent(file.metrics.JER) : '-'}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {file.metrics.miss !== undefined ? formatPercent(file.metrics.miss) : '-'}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {file.metrics.false_alarm !== undefined ? formatPercent(file.metrics.false_alarm) : '-'}
                    </TableCell>
                    <TableCell className="text-right font-mono">
                      {file.metrics.confusion !== undefined ? formatPercent(file.metrics.confusion) : '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Metrics Distribution */}
      {run.metrics.aggregate.DER_min !== undefined && (
        <div>
          <h3 className="text-xl font-semibold mb-4">Metrics Distribution</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">DER Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Mean:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.DER_mean)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Min:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.DER_min)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Max:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.DER_max)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Std Dev:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.DER_std || 0)}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">JER Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Mean:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.JER_mean)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Min:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.JER_min)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Max:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.JER_max)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Std Dev:</span>
                  <span className="font-mono">{formatPercent(run.metrics.aggregate.JER_std || 0)}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
