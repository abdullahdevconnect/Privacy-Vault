//F:\nodebase_final_pro\src\features\subscriptions\hooks\use-subscription.ts
import { useQuery } from "@tanstack/react-query";
import { authClient } from "@/lib/auth-client";

export const useSubscription = () => {
  return useQuery({
    queryKey: ["subscription"],
    queryFn: async () => {
      const { data, error } = await authClient.customer.state();

      // ✅ Update 1: Error handling add ki taake React Query ko error state ka pata chale
      if (error) {
        throw error;
      }

      return data;
    },
    // ✅ Update 2: Data ko 5 minute tak fresh rakhein (Performance ke liye)
    staleTime: 1000 * 60 * 5,
    retry: 1,
  });
};

export const useHasActiveSubscription = () => {
  const { data: customerState, isLoading, ...rest } = useSubscription();

  // Logic bilkul theek thi, bas thora clean kiya
  const hasActiveSubscription =
    !!customerState?.activeSubscriptions &&
    customerState.activeSubscriptions.length > 0;

  return {
    hasActiveSubscription,
    // Safe navigation ke sath null fallback
    subscription: customerState?.activeSubscriptions?.[0] ?? null,
    isLoading,
    ...rest,
  };
};
