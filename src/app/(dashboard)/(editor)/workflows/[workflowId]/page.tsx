import { prefetchWorkflow } from "@/features/workflows/server/prefetch";
import { HydrateClient } from "@/trpc/server";
import { Suspense } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Editor } from "@/features/editor/components/editor";
import { EditorHeader } from "@/features/editor/components/editor-header";
import { EditorLoading } from "@/features/editor/components/editor-loading";
import { EditorError } from "@/features/editor/components/editor-error";

interface PageProps {
  params: Promise<{
    workflowId: string;
  }>;
}

const Page = async ({ params }: PageProps) => {
  const resolvedParams = await params;
  const { workflowId } = resolvedParams;

  // Server side prefetching
  await prefetchWorkflow(workflowId);

  return (
    <HydrateClient>
      <ErrorBoundary fallback={<EditorError />}>
        <div className="flex h-full w-full flex-col">
          <Suspense fallback={<EditorLoading />}>
            <EditorHeader workflowId={workflowId} />
          </Suspense>

          <main className="flex-1 overflow-hidden">
            <Suspense fallback={<EditorLoading />}>
              <Editor workflowId={workflowId} />
            </Suspense>
          </main>
        </div>
      </ErrorBoundary>
    </HydrateClient>
  );
};

export default Page;
