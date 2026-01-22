import { useState, useEffect } from "react";
import "./index.css";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function App() {
  const [indexes, setIndexes] = useState([]);
  const [indexDir, setIndexDir] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [mode, setMode] = useState("");
  const [confidence, setConfidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/indexes")
      .then((res) => res.json())
      .then((data) => {
        setIndexes(data.indexes || []);
        if (data.indexes?.length > 0) {
          setIndexDir(data.indexes[0].path);
        }
      })
      .catch(() => {});
  }, []);

  async function handleAsk() {
    if (!question.trim() || !indexDir) return;

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);
    setMode("");
    setConfidence(null);

    try {
      const res = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index_dir: indexDir, question }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Request failed");
      }

      const data = await res.json();
      setAnswer(data.answer ?? "");
      setSources(data.sources ?? []);
      setMode(data.mode ?? "");
      setConfidence(data.confidence ?? null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      handleAsk();
    }
  }

  return (
    <div className="dark min-h-screen bg-background text-foreground">
      <div className="max-w-3xl mx-auto px-5 py-10">
        <h1 className="text-3xl font-semibold mb-6">Repo Q&A</h1>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="index">Repository Index</Label>
            {indexes.length > 0 ? (
              <Select value={indexDir} onValueChange={setIndexDir}>
                <SelectTrigger>
                  <SelectValue placeholder="Select an index" />
                </SelectTrigger>
                <SelectContent>
                  {indexes.map((idx) => (
                    <SelectItem key={idx.path} value={idx.path}>
                      {idx.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <Input
                id="index"
                value={indexDir}
                onChange={(e) => setIndexDir(e.target.value)}
                placeholder="./indexes/your-repo"
              />
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="question">Question</Label>
            <Textarea
              id="question"
              className="min-h-28 resize-y"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about the codebase... (Cmd+Enter to submit)"
            />
          </div>

          <Button
            onClick={handleAsk}
            disabled={loading || !question.trim()}
          >
            {loading ? "Thinking..." : "Ask"}
          </Button>
        </div>

        {error && (
          <Card className="mt-4 border-destructive bg-destructive/10">
            <CardContent className="pt-4 text-destructive">
              {error}
            </CardContent>
          </Card>
        )}

        {answer && (
          <Card className="mt-6">
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <Badge variant="secondary">{mode}</Badge>
                {confidence !== null && (
                  <span className="text-xs text-muted-foreground">
                    Confidence: {(confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <CardTitle className="text-base mb-3">Answer</CardTitle>
                <pre className="whitespace-pre-wrap text-sm leading-relaxed bg-muted p-4 rounded-lg border">
                  {answer}
                </pre>
              </div>

              {sources.length > 0 && (
                <div>
                  <CardTitle className="text-base mb-3">Sources</CardTitle>
                  <ul className="space-y-1">
                    {sources.map((src, i) => (
                      <li
                        key={i}
                        className="flex justify-between items-center px-3 py-2 bg-muted rounded border"
                      >
                        <span className="font-mono text-sm">
                          {src.file_path}
                        </span>
                        {src.score !== null && (
                          <span className="font-mono text-xs text-muted-foreground">
                            {src.score.toFixed(4)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
