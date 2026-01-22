// Use empty string for API_BASE so requests are relative to current origin
// Nginx will proxy these to the backend service
const API_BASE = '';

export type IndexInfo = {
  name: string;
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
