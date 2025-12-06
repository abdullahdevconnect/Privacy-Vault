// src/features/workflows/hooks/use-workflows-params.ts
import { parseAsInteger, parseAsString } from "nuqs";

export const workflowsParams = {
  page: parseAsInteger.withDefault(1),
  search: parseAsString.withDefault(""),
};
