import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

export interface Run {
  id: number;
  dataset_id: number;
  model_name: string;
  config: any;
  status: string;
  started_at: Date;
  completed_at: Date | null;
  created_at: Date;
}

export interface Result {
  id: number;
  run_id: number;
  audio_file_id: number;
  metric_name: string;
  value: number | null;
  details: any;
  created_at: Date;
}

export interface RunWithMetrics extends Run {
  avg_der?: number | null;
  avg_jer?: number | null;
  result_count?: number;
  dataset_name?: string;
}

export interface GetRunsOptions {
  model?: string;
  status?: string;
  limit?: number;
}

export async function getRuns(options: GetRunsOptions = {}): Promise<RunWithMetrics[]> {
  const { model, status, limit = 50 } = options;
  
  let query = `
    SELECT 
      r.*,
      d.name as dataset_name,
      (SELECT AVG(value) FROM results WHERE run_id = r.id AND metric_name = 'der') as avg_der,
      (SELECT AVG(value) FROM results WHERE run_id = r.id AND metric_name = 'jer') as avg_jer,
      (SELECT COUNT(DISTINCT audio_file_id) FROM results WHERE run_id = r.id) as result_count
    FROM runs r
    LEFT JOIN datasets d ON r.dataset_id = d.id
  `;
  
  const conditions: string[] = [];
  const params: any[] = [];
  
  if (model) {
    conditions.push(`r.model_name = $${params.length + 1}`);
    params.push(model);
  }
  
  if (status) {
    conditions.push(`r.status = $${params.length + 1}`);
    params.push(status);
  }
  
  if (conditions.length > 0) {
    query += ' WHERE ' + conditions.join(' AND ');
  }
  
  query += `
    ORDER BY r.id DESC
    LIMIT $${params.length + 1}
  `;
  params.push(limit);
  
  const result = await pool.query(query, params);
  return result.rows;
}

export interface RunDetails extends Run {
  dataset_name?: string;
  results: Result[];
  stats?: {
    der: {
      mean: number | null;
      min: number | null;
      max: number | null;
      std: number | null;
    };
    jer: {
      mean: number | null;
      min: number | null;
      max: number | null;
      std: number | null;
    };
  };
}

export async function getRunDetails(runId: number): Promise<RunDetails | null> {
  // Get run with dataset name
  const runResult = await pool.query(
    `SELECT r.*, d.name as dataset_name 
     FROM runs r 
     LEFT JOIN datasets d ON r.dataset_id = d.id 
     WHERE r.id = $1`,
    [runId]
  );
  
  if (runResult.rows.length === 0) {
    return null;
  }
  
  const run = runResult.rows[0];
  
  // Get results
  const resultsQuery = await pool.query(
    'SELECT * FROM results WHERE run_id = $1 ORDER BY audio_file_id, metric_name',
    [runId]
  );
  
  const results = resultsQuery.rows;
  
  // Calculate stats
  let stats = undefined;
  if (results.length > 0) {
    const derValues = results
      .filter(r => r.metric_name === 'der' && r.value !== null)
      .map(r => r.value as number);
    const jerValues = results
      .filter(r => r.metric_name === 'jer' && r.value !== null)
      .map(r => r.value as number);
    
    const calcStats = (values: number[]) => {
      if (values.length === 0) {
        return { mean: null, min: null, max: null, std: null };
      }
      
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const min = Math.min(...values);
      const max = Math.max(...values);
      
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      const std = Math.sqrt(variance);
      
      return { mean, min, max, std };
    };
    
    stats = {
      der: calcStats(derValues),
      jer: calcStats(jerValues),
    };
  }
  
  return {
    ...run,
    results,
    stats,
  };
}
