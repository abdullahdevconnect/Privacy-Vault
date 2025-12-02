import {
  WorkflowsContainer,
  WorkflowsList,
} from "@/features/workflows/components/workflows";
import { prefetchWorkflows } from "@/features/workflows/server/prefetch";
import { requireAuth } from "@/lib/auth-utils";
import { HydrateClient } from "@/trpc/server";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { searchParamsCache } from "@/features/workflows/params";

interface PageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

const Page = async ({ searchParams }: PageProps) => {
  await requireAuth();

  
  const resolvedSearchParams = await searchParams;
  const params = searchParamsCache.parse(resolvedSearchParams);


  void prefetchWorkflows(params).catch((err) => {
    // Optional: Log error in development only
    if (process.env.NODE_ENV === "development") {
      console.error("Prefetch failed (likely auth issue):", err);
    }
  });

  return (
    <WorkflowsContainer>
      <HydrateClient>
        <ErrorBoundary fallback={<p>Error!</p>}>
          <Suspense fallback={<p>Loading...</p>}>
            <WorkflowsList />
          </Suspense>
        </ErrorBoundary>
      </HydrateClient>
    </WorkflowsContainer>
  );
};

export default Page;
