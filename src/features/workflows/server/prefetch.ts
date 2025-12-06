// F:\nodebase_final_pro\src\features\workflows\server\prefetch.ts
import "server-only";
import { trpc } from "@/trpc/server";
import { type AppRouter } from "@/trpc/routers/_app";
import { type inferRouterInputs } from "@trpc/server";

type GetWorkflowsInput = inferRouterInputs<AppRouter>["workflows"]["getMany"];

/**
 * @param params - The search/pagination parameters (page, pageSize, query)
 */
export const prefetchWorkflows = async (params: GetWorkflowsInput) => {
  return trpc.workflows.getMany.prefetch(params);
};
