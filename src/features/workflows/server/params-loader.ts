// src/features/workflows/server/params-loader.ts
import { createSearchParamsCache } from "nuqs/server";
import { workflowsParams } from "../hooks/use-workflows-params";





export const workflowsParamsLoader = createSearchParamsCache(workflowsParams);
