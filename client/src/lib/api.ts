const API_BASE = 'http://localhost:8000';

export type IndexInfo = {
  name: string;
  path: string;
}

export type AskResponse = {
  answer: string;
  sources: { file_path: string; score: number | null }[];
  mode: string;
  confidence: number;
}

export async function fetchIndexes(): Promise<IndexInfo[]> {
  const res = await fetch(`${API_BASE}/indexes`);
  if (!res.ok) throw new Error('Failed to fetch indexes');
  return res.json();
}

export async function askQuestion(index: string, question: string): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ index, question }),
  });
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to get answer');
  }
  return res.json();
}
