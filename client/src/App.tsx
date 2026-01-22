import { useEffect, useState } from 'react';
import { IndexSelector } from './components/IndexSelector';
import { QuestionInput } from './components/QuestionInput';
import { AnswerDisplay } from './components/AnswerDisplay';
import { fetchIndexes, askQuestion } from './lib/api';
import type { IndexInfo, AskResponse } from './lib/api';

function App() {
  const [indexes, setIndexes] = useState<IndexInfo[]>([]);
  const [selectedIndex, setSelectedIndex] = useState('');
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchIndexes()
      .then(setIndexes)
      .catch((e) => setError(e.message));
  }, []);

  const handleAsk = async () => {
    if (!selectedIndex || !question.trim()) return;

    setLoading(true);
    setError('');
    setResponse(null);

    try {
      const res = await askQuestion(selectedIndex, question);
      setResponse(res);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <h1 className="text-2xl font-bold">Repo Q&A</h1>

        <IndexSelector
          indexes={indexes}
          value={selectedIndex}
          onChange={setSelectedIndex}
        />

        <QuestionInput
          value={question}
          onChange={setQuestion}
          onSubmit={handleAsk}
          loading={loading}
        />

        {error && (
          <div className="text-red-500 text-sm">{error}</div>
        )}

        <AnswerDisplay response={response} />
      </div>
    </div>
  );
}

export default App;
