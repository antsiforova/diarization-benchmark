import { NextRequest, NextResponse } from 'next/server';
import { getRuns } from '@/lib/db';
import { spawn } from 'child_process';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const model = searchParams.get('model') || undefined;
    const status = searchParams.get('status') || undefined;
    const limit = parseInt(searchParams.get('limit') || '50');
    
    const runs = await getRuns({
      model,
      status,
      limit
    });
    
    // Transform data to match frontend expectations
    const transformedRuns = runs.map(run => ({
      id: run.id,
      model_name: run.model_name,
      dataset_name: run.dataset_name || 'Unknown',
      status: run.status,
      started_at: run.started_at,
      completed_at: run.completed_at,
      duration_sec: run.started_at && run.completed_at 
        ? (new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000
        : null,
      der_mean: run.avg_der,
      jer_mean: run.avg_jer,
      result_count: run.result_count
    }));
    
    return NextResponse.json({ runs: transformedRuns });
  } catch (error) {
    console.error('Error fetching runs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch runs' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const { dataset, model } = await request.json();
    
    // Validate inputs
    if (!dataset || !['ami', 'sequestered'].includes(dataset)) {
      return NextResponse.json(
        { error: 'Invalid dataset. Must be "ami" or "sequestered"' },
        { status: 400 }
      );
    }

    const scriptPath = '/app/run_and_save.py';

    console.log(`Starting benchmark: ${dataset} dataset with ${model || 'mock'} model`);

    // Start benchmark in background (Docker environment)
    const pythonProcess = spawn('python3', [
      scriptPath,
      '--dataset', dataset,
      '--model', model || 'mock'
    ], {
      cwd: '/app',
      detached: true,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    // Log output for debugging
    pythonProcess.stdout?.on('data', (data) => {
      console.log(`Benchmark stdout: ${data}`);
    });

    pythonProcess.stderr?.on('data', (data) => {
      console.error(`Benchmark stderr: ${data}`);
    });

    pythonProcess.on('error', (error) => {
      console.error(`Failed to start benchmark:`, error);
    });

    pythonProcess.on('exit', (code) => {
      console.log(`Benchmark process exited with code ${code}`);
    });

    // Detach process so it runs independently
    pythonProcess.unref();

    return NextResponse.json({
      status: 'started',
      message: `Benchmark started for ${dataset} dataset`,
      dataset,
      model: model || 'mock'
    });
  } catch (error) {
    console.error('Error starting benchmark:', error);
    return NextResponse.json(
      { error: 'Failed to start benchmark' },
      { status: 500 }
    );
  }
}