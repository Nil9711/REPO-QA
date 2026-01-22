import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { IndexInfo } from "@/lib/api";

interface Props {
  indexes: IndexInfo[];
  value: string;
  onChange: (value: string) => void;
}

export function IndexSelector({ indexes, value, onChange }: Props) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a repository" />
      </SelectTrigger>
      <SelectContent>
        {indexes.map((idx) => (
          <SelectItem key={idx.name} value={idx.name}>
            {idx.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
