'use client';

import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface MetricsChartProps {
  metricType: 'DER' | 'JER';
  onClose: () => void;
}

interface ChartDataPoint {
  date: string;
  value: number;
  runId: number;
}

export function MetricsChart({ metricType, onClose }: MetricsChartProps) {
  const [allRuns, setAllRuns] = useState<any[]>([]);
  const [data, setData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDataset, setSelectedDataset] = useState<string>('all');
  const [availableDatasets, setAvailableDatasets] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/runs')
      .then(res => res.json())
      .then(result => {
        const completedRuns = result.runs.filter(
          (run: any) => run.status === 'completed' && run[metricType === 'DER' ? 'der_mean' : 'jer_mean'] !== null
        );
        
        setAllRuns(completedRuns);
        
        // Extract unique datasets
        const datasets = [...new Set(completedRuns.map((run: any) => run.dataset_name))];
        setAvailableDatasets(datasets);
        
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load chart data:', err);
        setLoading(false);
      });
  }, [metricType]);

  useEffect(() => {
    // Filter and map data based on selected dataset
    const filteredRuns = selectedDataset === 'all' 
      ? allRuns 
      : allRuns.filter((run: any) => run.dataset_name === selectedDataset);

    const chartData = filteredRuns
      .map((run: any) => ({
        date: new Date(run.started_at).toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }),
        value: metricType === 'DER' ? run.der_mean : run.jer_mean,
        runId: run.id
      }))
      .reverse(); // Oldest first for timeline

    setData(chartData);
  }, [allRuns, selectedDataset, metricType]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <Card className="w-full max-w-4xl bg-white">
          <CardContent className="p-8">
            <p>Loading chart...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-6xl max-h-[90vh] overflow-auto bg-white shadow-xl">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>{metricType} Over Time</CardTitle>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground text-2xl"
            >
              ×
            </button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <label htmlFor="dataset-filter" className="block text-sm font-medium mb-2">
              Dataset
            </label>
            <select
              id="dataset-filter"
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-64 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Datasets</option>
              {availableDatasets.map((dataset) => (
                <option key={dataset} value={dataset}>
                  {dataset}
                </option>
              ))}
            </select>
          </div>
          {data.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No completed runs with {metricType} data available.
            </p>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis 
                  label={{ value: metricType, angle: -90, position: 'insideLeft' }}
                  domain={[0, 1]}
                />
                <Tooltip 
                  formatter={(value: number) => value.toFixed(4)}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#2563eb" 
                  strokeWidth={2}
                  dot={{ fill: '#2563eb', r: 5 }}
                  name={metricType}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
          
          {data.length > 0 && (
            <div className="mt-4 text-sm text-muted-foreground">
              <p>Showing {data.length} completed runs</p>
              <p>Latest: {metricType} = {data[data.length - 1]?.value.toFixed(4)}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
