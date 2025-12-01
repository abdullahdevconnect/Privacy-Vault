import { trpc } from "@/trpc/server";
import type { AppRouter } from "@/trpc/routers/_app";
import type { inferRouterInputs } from "@trpc/server";

// 1. Correctly infer input type from the AppRouter definition
type Input = inferRouterInputs<AppRouter>["workflows"]["getMany"];

/**
 * Prefetch all workflows
 */
export const prefetchWorkflows = async (params: Input) => {
  // 2. Use the modern v11 prefetch method.
  // This automatically fetches data into the server-side QueryClient.
  return trpc.workflows.getMany.prefetch(params);
};
