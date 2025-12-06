// F:\nodebase_final_pro\src\trpc\server.tsx
import "server-only";

import { createHydrationHelpers } from "@trpc/react-query/rsc";
import { cache } from "react";
import { createCallerFactory, createTRPCContext } from "./init";
import { makeQueryClient } from "./query-client";
import { appRouter } from "./routers/_app";


export const getQueryClient = cache(makeQueryClient);

// 2. Create the caller factory
const caller = createCallerFactory(appRouter);


export const { trpc, HydrateClient } = createHydrationHelpers<typeof appRouter>(
  caller as any,
  getQueryClient
);


export const api = async () => {
  return caller(await createTRPCContext());
};
