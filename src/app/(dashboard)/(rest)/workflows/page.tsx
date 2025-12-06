//F:\nodebase_final_pro\src\app\(dashboard)\(rest)\workflows\page.tsx
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import {
  WorkflowsContainer,
  WorkflowsList,
} from "@/features/workflows/components/workflows";
import { LoadingView, ErrorView } from "@/components/entity-components";
import { prefetchWorkflows } from "@/features/workflows/server/prefetch";
import { requireAuth } from "@/lib/auth-utils";
import { HydrateClient } from "@/trpc/server";
import { searchParamsCache } from "@/features/workflows/params"; // ✅ Added missing import

interface PageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

const Page = async (props: PageProps) => {
  await requireAuth();

  const resolvedSearchParams = await props.searchParams;
  const params = searchParamsCache.parse(resolvedSearchParams);

  // ✅ Await the prefetch to prevent empty state flash
  try {
    await prefetchWorkflows(params);
  } catch (err) {
    console.error("Prefetch failed:", err);
  }

  return (
    <WorkflowsContainer>
      <HydrateClient>
        <ErrorBoundary
          fallback={
            <ErrorView message="Failed to load workflows. Please try again." />
          }>
          <Suspense
            key={JSON.stringify(params)}
            fallback={<LoadingView entity="workflows" />}>
            <WorkflowsList />
          </Suspense>
        </ErrorBoundary>
      </HydrateClient>
    </WorkflowsContainer>
  );
};

export default Page;
