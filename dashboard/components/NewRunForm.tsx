'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface NewRunFormProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function NewRunForm({ onClose, onSuccess }: NewRunFormProps) {
  const [dataset, setDataset] = useState('ami');
  const [model, setModel] = useState('mock');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/runs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset, model }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to start benchmark');
      }

      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start benchmark');
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md bg-white shadow-xl">
        <CardHeader>
          <CardTitle className="flex justify-between items-center">
            <span>New Benchmark Run</span>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
              disabled={loading}
            >
              ✕
            </button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="dataset" className="block text-sm font-medium mb-2">
                Dataset
              </label>
              <select
                id="dataset"
                value={dataset}
                onChange={(e) => setDataset(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ami">AMI Corpus</option>
                <option value="sequestered">Sequestered Data</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                {dataset === 'ami' ? 'AMI Meeting Corpus test set' : 'Conversation recordings'}
              </p>
            </div>

            <div>
              <label htmlFor="model" className="block text-sm font-medium mb-2">
                Model
              </label>
              <select
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="mock">Mock Mode</option>
              </select>
              <p className="text-xs text-muted-foreground mt-1">
                Simulated diarization for demonstration
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Starting...' : 'Start Benchmark'}
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
