'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { StatusBadge } from '@/components/StatusBadge';
import { formatDuration, formatPercent, formatDate } from '@/lib/utils';
import { NewRunForm } from '@/components/NewRunForm';
import { MetricsChart } from '@/components/MetricsChart';

interface Run {
  id: number;
  model_name: string;
  dataset_name: string;
  status: string;
  started_at: string;
  duration_sec: number;
  der_mean: number;
  jer_mean: number;
}

export default function HomePage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewRunForm, setShowNewRunForm] = useState(false);
  const [showChart, setShowChart] = useState<'DER' | 'JER' | null>(null);

  const loadRuns = () => {
    fetch('/api/runs')
      .then(res => res.json())
      .then(data => {
        setRuns(data.runs || []);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to load runs');
        setLoading(false);
        console.error(err);
      });
  };

  useEffect(() => {
    loadRuns();
  }, []);

  if (loading) {
    return <div className="text-center py-12">Loading runs...</div>;
  }

  if (error) {
    return <div className="text-center py-12 text-red-500">{error}</div>;
  }

  if (runs.length === 0) {
    return (
      <div>
        {showNewRunForm && (
          <NewRunForm
            onClose={() => setShowNewRunForm(false)}
            onSuccess={() => {
              setLoading(true);
              loadRuns();
            }}
          />
        )}
        
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold">Benchmark Runs</h2>
          <button
            onClick={() => setShowNewRunForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + New Run
          </button>
        </div>
        
        <div className="text-center py-12">
          <p className="text-muted-foreground">No benchmark runs found.</p>
          <p className="text-sm text-muted-foreground mt-2">Click "+ New Run" to start a benchmark.</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {showNewRunForm && (
        <NewRunForm
          onClose={() => setShowNewRunForm(false)}
          onSuccess={() => {
            setLoading(true);
            loadRuns();
          }}
        />
      )}

      {showChart && (
        <MetricsChart
          metricType={showChart}
          onClose={() => setShowChart(null)}
        />
      )}

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">Benchmark Runs</h2>
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">
            Total: {runs.length} runs
          </div>
          <button
            onClick={() => setShowChart('DER')}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            DER Chart
          </button>
          <button
            onClick={() => setShowChart('JER')}
            className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            JER Chart
          </button>
          <button
            onClick={() => setShowNewRunForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            + New Run
          </button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>#</TableHead>
              <TableHead>DB ID</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Dataset</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead className="text-right">DER</TableHead>
              <TableHead className="text-right">JER</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run, index) => (
              <TableRow key={run.id} className="cursor-pointer hover:bg-muted/50">
                <TableCell>#{index + 1}</TableCell>
                <TableCell>
                  <Link href={`/runs/${run.id}`} className="text-blue-600 hover:underline">
                    #{run.id}
                  </Link>
                </TableCell>
                <TableCell className="font-medium">{run.model_name}</TableCell>
                <TableCell>{run.dataset_name}</TableCell>
                <TableCell>
                  <StatusBadge status={run.status} />
                </TableCell>
                <TableCell>
                  {run.duration_sec ? formatDuration(run.duration_sec) : '-'}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {run.der_mean !== null && run.der_mean !== undefined ? formatPercent(run.der_mean) : '-'}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {run.jer_mean !== null && run.jer_mean !== undefined ? formatPercent(run.jer_mean) : '-'}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {formatDate(run.started_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
