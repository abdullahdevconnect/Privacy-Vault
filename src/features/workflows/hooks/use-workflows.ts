"use client";

import { trpc } from "@/trpc/client";
import { toast } from "sonner";

export const useSuspenseWorkflows = () => {
  return trpc.workflows.getMany.useSuspenseQuery({});
};

export const useCreateWorkflow = () => {
  const utils = trpc.useUtils();

  return trpc.workflows.create.useMutation({
    
    onSuccess: async (data: any) => {
      toast.success(`Workflow "${data.name}" created`, {
        id: "create-workflow",
      });

      await utils.workflows.getMany.invalidate();
    },
        onError: (error: any) => {
      toast.error(`Failed to create workflow: ${error.message}`, {
        id: "create-workflow",
      });
    },
  });
};
