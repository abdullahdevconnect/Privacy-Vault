"use client";

import { useSuspenseWorkflow } from "@/features/workflows/hooks/use-workflows";

export const Editor = ({ workflowId }: { workflowId: string }) => {
  const workflow = useSuspenseWorkflow(workflowId);

  return (
    <div className="h-full w-full overflow-hidden bg-background">
      <pre className="p-4 text-sm">{JSON.stringify(workflow, null, 2)}</pre>
    </div>
  );
};
