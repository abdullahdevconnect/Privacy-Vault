// F:\nodebase_final_pro\src\features\workflows\params.ts
import {
  createSearchParamsCache,
  parseAsInteger,
  parseAsString,
} from "nuqs/server";
import { useQueryStates } from "nuqs";

// 👇 FIX: Iska naam 'parsers' se badal kar 'workflowsParams' karein
export const workflowsParams = {
  page: parseAsInteger.withDefault(1),
  pageSize: parseAsInteger.withDefault(10),
  search: parseAsString.withDefault(""),
};

// 👇 Niche jahan jahan 'parsers' use ho raha tha, wahan bhi update karein
export const searchParamsCache = createSearchParamsCache(workflowsParams);

export const useWorkflowsParams = () => {
  return useQueryStates(workflowsParams);
};
