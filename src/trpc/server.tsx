import "server-only";

import { createHydrationHelpers } from "@trpc/react-query/rsc";

import { cache } from "react";
import { createCallerFactory, createTRPCContext } from "./init";
import { makeQueryClient } from "./query-client";
import { appRouter } from "./routers/_app";

// 1. Create a stable getter for the query client
export const getQueryClient = cache(makeQueryClient);

// 2. Create the caller factory
const caller = createCallerFactory(appRouter);

// 3. Create Hydration Helpers
export const { trpc, HydrateClient } = createHydrationHelpers<typeof appRouter>(
  caller(createTRPCContext),
  getQueryClient
);
