import "server-only";

import { createHydrationHelpers } from "@trpc/react-query/rsc";
import { cache } from "react";
import { createCallerFactory, createTRPCContext } from "./init";
import { makeQueryClient } from "./query-client";
import { appRouter } from "./routers/_app";




// 1. Cache the Query Client
export const getQueryClient = cache(makeQueryClient);

// 2. Create the caller factory
const createCaller = createCallerFactory(appRouter);

// 3. Helper function to create the caller with context
const getCaller = cache(async () => {
  const ctx = await createTRPCContext();
  return createCaller(ctx);
});

// 4. Create Hydration Helpers
export const { trpc, HydrateClient } = createHydrationHelpers<typeof appRouter>(
  // @ts-expect-error - tRPC v11 types issue with async callers in RSC, but works at runtime
  getCaller,
  getQueryClient
);
