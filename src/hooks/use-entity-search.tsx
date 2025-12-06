//F:\nodebase_final_pro\src\hooks\use-entity-search.tsx
import { useEffect, useState } from "react";
import { PAGINATION } from "@/config/constants";

interface UseEntitySearchProps<
  T extends {
    search?: string | null; // Nuqs search can be null/undefined
    page: number;
  }
> {
  params: T;
  setParams: (params: Partial<T> | null) => void;
  debounceMs?: number;
}

export function useEntitySearch<
  T extends {
    search?: string | null;
    page: number;
  }
>({ params, setParams, debounceMs = 500 }: UseEntitySearchProps<T>) {
  // 1. Local state manages the immediate input value (for smooth typing)
  const [localSearch, setLocalSearch] = useState(params.search ?? "");

  // 2. Sync local state if the URL changes externally (e.g., Back button navigation)
  useEffect(() => {
    setLocalSearch(params.search ?? "");
  }, [params.search]);

  
  useEffect(() => {
    const handler = setTimeout(() => {
      
      if (localSearch !== (params.search ?? "")) {
        setParams({
          search: localSearch || null, 
          page: PAGINATION.DEFAULT_PAGE, 
        } as unknown as Partial<T>); 
      }
    }, debounceMs);

    
    return () => {
      clearTimeout(handler);
    };
  }, [localSearch, debounceMs, params.search, setParams]);

  return {
    search: localSearch,
    setSearch: setLocalSearch,
  };
}
