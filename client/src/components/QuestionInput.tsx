import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export function QuestionInput({ value, onChange, onSubmit, loading }: Props) {
  return (
    <div className="space-y-2">
      <Textarea
        placeholder="Ask a question about the repository..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && e.metaKey) onSubmit();
        }}
        rows={3}
      />
      <Button onClick={onSubmit} disabled={loading || !value.trim()}>
        {loading ? 'Thinking...' : 'Ask'}
      </Button>
    </div>
  );
}
