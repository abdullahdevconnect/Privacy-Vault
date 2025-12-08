import { trpc } from "@/trpc/client";
import { toast } from "sonner";
// 👇 FIX: Import path update kiya hai (kyunke params.ts ab aik folder peeche hai)
import { useWorkflowsParams } from "../params";

// --- Hooks ---

export const useWorkflows = () => {
  const [params] = useWorkflowsParams();
  return trpc.workflows.getMany.useQuery(params);
};

export const useCreateWorkflow = () => {
  const utils = trpc.useUtils();

  return trpc.workflows.create.useMutation({
    onSuccess: () => {
      toast.success("Workflow created");
      utils.workflows.getMany.invalidate();
    },
    onError: () => {
      toast.error("Failed to create workflow");
    },
  });
};

export const useRemoveWorkflow = () => {
  const utils = trpc.useUtils();

  return trpc.workflows.remove.useMutation({
    onSuccess: () => {
      toast.success("Workflow removed");
      utils.workflows.getMany.invalidate();
    },
    onError: () => {
      toast.error("Failed to remove workflow");
    },
  });
};

export const useSuspenseWorkflow = (id: string) => {
  const [data] = trpc.workflows.getById.useSuspenseQuery({ id });
  return data;
};

export const useUpdateWorkflowName = () => {
  const utils = trpc.useUtils();

  return trpc.workflows.updateName.useMutation({
    onSuccess: (data, variables) => {
      toast.success("Workflow updated");

      // Update the specific workflow in cache
      utils.workflows.getById.invalidate({ id: variables.id });

      // Also update the list so the new name shows up on the dashboard
      utils.workflows.getMany.invalidate();
    },
    onError: (error) => {
      toast.error(`Failed to update workflow: ${error.message}`);
    },
  });
};
