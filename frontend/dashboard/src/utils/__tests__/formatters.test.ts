import { describe, it, expect } from 'vitest';

// Utility formatters
export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatTime = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${(ms / 60000).toFixed(1)}m`;
  return `${(ms / 3600000).toFixed(1)}h`;
};

export const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

export const formatPercent = (value: number, decimals = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

export const truncate = (str: string, length: number): string => {
  if (str.length <= length) return str;
  return str.substring(0, length) + '...';
};

describe('Date Formatters', () => {
  it('formats date correctly', () => {
    const date = new Date('2026-04-30T10:30:00Z');
    const formatted = formatDate(date);
    expect(formatted).toMatch(/Apr 30, 2026/);
  });

  it('formats time correctly', () => {
    const date = new Date('2026-04-30T10:30:00Z');
    const formatted = formatTime(date);
    expect(formatted).toMatch(/\d{1,2}:\d{2}/);
  });
});

describe('Duration Formatter', () => {
  it('formats milliseconds', () => {
    expect(formatDuration(500)).toBe('500ms');
  });

  it('formats seconds', () => {
    expect(formatDuration(2500)).toBe('2.5s');
  });

  it('formats minutes', () => {
    expect(formatDuration(90000)).toBe('1.5m');
  });

  it('formats hours', () => {
    expect(formatDuration(5400000)).toBe('1.5h');
  });
});

describe('Bytes Formatter', () => {
  it('formats zero bytes', () => {
    expect(formatBytes(0)).toBe('0 B');
  });

  it('formats bytes', () => {
    expect(formatBytes(500)).toBe('500.00 B');
  });

  it('formats kilobytes', () => {
    expect(formatBytes(1536)).toBe('1.50 KB');
  });

  it('formats megabytes', () => {
    expect(formatBytes(1572864)).toBe('1.50 MB');
  });

  it('formats gigabytes', () => {
    expect(formatBytes(1610612736)).toBe('1.50 GB');
  });
});

describe('Percent Formatter', () => {
  it('formats percentage with default decimals', () => {
    expect(formatPercent(85.123)).toBe('85.1%');
  });

  it('formats percentage with custom decimals', () => {
    expect(formatPercent(85.123, 2)).toBe('85.12%');
  });

  it('formats zero percent', () => {
    expect(formatPercent(0)).toBe('0.0%');
  });

  it('formats 100 percent', () => {
    expect(formatPercent(100)).toBe('100.0%');
  });
});

describe('String Truncate', () => {
  it('does not truncate short strings', () => {
    expect(truncate('Hello', 10)).toBe('Hello');
  });

  it('truncates long strings', () => {
    expect(truncate('This is a very long string', 10)).toBe('This is a ...');
  });

  it('handles exact length', () => {
    expect(truncate('12345', 5)).toBe('12345');
  });

  it('handles empty string', () => {
    expect(truncate('', 5)).toBe('');
  });
});
