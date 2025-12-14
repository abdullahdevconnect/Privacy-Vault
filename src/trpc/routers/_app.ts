// F:\nodebase_final_pro\src\trpc\routers\_app.ts
import { createTRPCRouter } from "../init";


import { workflowsRouter } from "@/features/workflows/server/routers";

// Debugging ke liye: Check karein ke router undefined to nahi hai?
if (!workflowsRouter) {
  console.error(
    "❌ ERROR: workflowsRouter properly import nahi hua! Path check karein."
  );
} else {
  console.log("✅ SUCCESS: workflowsRouter load ho gaya hai.");
}

export const appRouter = createTRPCRouter({
  // Ye 'workflows' key page.tsx main 'trpc.workflows' banati hai
  workflows: workflowsRouter,
});

export type AppRouter = typeof appRouter;
