"use client";

import { trpc } from "@/trpc/client"; 
import { useWorkflowsParams } from "../params";


export const useWorkflows = () => {
  const [params] = useWorkflowsParams();

  // ✅ Real Data from Database via tRPC
  return trpc.workflows.getMany.useQuery(
    {
      page: params.page ?? 1,
      pageSize: 8, // Ek page par 8 workflows
      search: params.search ?? "",
    },
    {
      // Optional: Data ko fresh rakhne ke liye
      staleTime: 1000 * 60 * 1, // 1 minute
    }
  );
};

// --- Create Workflow Mutation ---
export const useCreateWorkflow = () => {
  const utils = trpc.useUtils();

  return trpc.workflows.create.useMutation({
    onSuccess: () => {
      // List ko refresh karo jab naya workflow bane
      utils.workflows.getMany.invalidate();
    },
  });
};
