import { createTRPCRouter } from "../init";
// Make sure ye path direct file par jaye, folder par nahi
import { workflowsRouter } from "@/features/workflows/server/routers";

export const appRouter = createTRPCRouter({
  workflows: workflowsRouter,
});

export type AppRouter = typeof appRouter;
