import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const variant = status === 'completed' ? 'success' : status === 'failed' ? 'destructive' : 'default';
  
  return (
    <Badge variant={variant}>
      {status}
    </Badge>
  );
}
