import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AskResponse } from "@/lib/api";

interface Props {
  response: AskResponse | null;
}

export function AnswerDisplay({ response }: Props) {
  if (!response) return null;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Answer</CardTitle>
          <span className="text-xs text-muted-foreground">
            Mode: {response.mode} (confidence: {(response.confidence * 100).toFixed(0)}%)
          </span>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm max-w-none whitespace-pre-wrap">
            {response.answer}
          </div>
        </CardContent>
      </Card>

      {response.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="text-sm space-y-1">
              {response.sources.map((src, i) => (
                <li key={i} className="font-mono text-xs">
                  {src.file_path}
                  {src.score !== null && (
                    <span className="text-muted-foreground ml-2">
                      (score: {src.score.toFixed(3)})
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
