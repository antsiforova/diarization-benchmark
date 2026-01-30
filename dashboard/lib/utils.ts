import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('ru-RU', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDuration(startedAtOrSeconds: Date | string | number, completedAt?: Date | string | null): string {
  let diffSec: number;
  
  // If first argument is a number, treat it as seconds
  if (typeof startedAtOrSeconds === 'number') {
    diffSec = Math.floor(startedAtOrSeconds);
  } else {
    // Otherwise, treat as dates
    if (!completedAt) {
      return 'N/A';
    }
    const start = typeof startedAtOrSeconds === 'string' ? new Date(startedAtOrSeconds) : startedAtOrSeconds;
    const end = typeof completedAt === 'string' ? new Date(completedAt) : completedAt;
    const diffMs = end.getTime() - start.getTime();
    diffSec = Math.floor(diffMs / 1000);
  }
  
  if (diffSec < 60) {
    return `${diffSec}s`;
  } else if (diffSec < 3600) {
    const mins = Math.floor(diffSec / 60);
    const secs = diffSec % 60;
    return `${mins}m ${secs}s`;
  } else {
    const hours = Math.floor(diffSec / 3600);
    const mins = Math.floor((diffSec % 3600) / 60);
    return `${hours}h ${mins}m`;
  }
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  return `${(value * 100).toFixed(2)}%`;
}
