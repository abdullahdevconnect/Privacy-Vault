"use client";
import { requireAuth } from "@/lib/auth-utils";
import { caller } from "@/trpc/server";
import { LogoutButton } from "./logout";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTRPC } from "@/trpc/client";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const Page = () => {
  const trpc = useTRPC();
  const queryClient = useQueryClient();

  const { data } = useQuery(trpc.getWorkflows.queryOptions());

  const testAi = useMutation(
    trpc.testAi.mutationOptions({
      onSuccess: () => {
        toast.success("AI Test successful");
      },
      onError: (err) => {
        toast.error(err?.message || "AI Test failed");
      },
    })
  );

  const create = useMutation(
    trpc.createWorkflow.mutationOptions({
      onSuccess: () => {
        queryClient.invalidateQueries(trpc.getWorkflows.queryOptions());
        toast.success("Workflow created and job sent to Inngest!");
      },
      onError: (err) => {
        toast.error(err?.message || "Failed to create workflow");
      },
    })
  );

  return (
    <div className="min-h-screen min-w-screen flex items-center justify-center flex-col gap-y-6">
      protected server component
      <div>{JSON.stringify(data, null, 2)}</div>
      <Button disabled={testAi.isPending} onClick={() => testAi.mutate()}>
        Test AI
      </Button>
      <Button disabled={create.isPending} onClick={() => create.mutate()}>
        {create.isPending ? "Creating..." : "Create workflow"}
      </Button>
      <LogoutButton />
    </div>
  );
};

export default Page;
