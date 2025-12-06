//F:\nodebase_final_pro\src\app\(dashboard)\(editor)\workflows\[workflowId]\page.tsx
import { requireAuth } from "@/lib/auth-utils";

interface PageProps {
  params: Promise<{
    workflowId: string;
  }>;
}

const Page = async ({ params }: PageProps) => {
  await requireAuth();
  const { workflowId } = await params;

  return <p>Workflow id: {workflowId}</p>;
};

export default Page;
