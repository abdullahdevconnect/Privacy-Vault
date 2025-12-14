// F:\nodebase_final_pro\src\features\workflows\server\prefetch.ts
import "server-only";

import { createCallerFactory, createTRPCContext } from "@/trpc/init";
import { appRouter } from "@/trpc/routers/_app";
import { cache } from "react";

// Caller create karne ka setup
const createCaller = createCallerFactory(appRouter);

const getCaller = cache(async () => {
  // ✅ FIX: createTRPCContext ko arguments ki zaroorat nahi hai.
  // Ye khud hi next/headers se headers utha leta hai.
  const ctx = await createTRPCContext();
  return createCaller(ctx);
});

export const prefetchWorkflow = async (id: string) => {
  const caller = await getCaller();

  try {
    const workflow = await caller.workflows.getById({ id });
    console.log("✅ Workflow Prefetched on Server:", workflow?.name);
    return workflow;
  } catch (error) {
    console.error("❌ Error prefetching workflow:", error);
    return null;
  }
};
