import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import {
  WorkflowsContainer,
  WorkflowsList,
} from "@/features/workflows/components/workflows";
import { LoadingView, ErrorView } from "@/components/entity-components";
import { requireAuth } from "@/lib/auth-utils";
import { trpc, HydrateClient } from "@/trpc/server";
import { searchParamsCache } from "@/features/workflows/params";
import { PAGINATION } from "@/config/constants"; // 👈 Import added

interface PageProps {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

const Page = async (props: PageProps) => {
  await requireAuth();

  const resolvedSearchParams = await props.searchParams;
  const params = searchParamsCache.parse(resolvedSearchParams);

  // ✅ FIX: Hardcoded '8' ko hata kar Constant use kiya
  void trpc.workflows.getMany.prefetch({
    page: params.page ?? 1,
    pageSize: PAGINATION.DEFAULT_PAGE_SIZE, // Ab ye 10 uthayega (ya jo bhi constant main ho)
    search: params.search ?? "",
  });

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
