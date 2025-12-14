"use client";

import {
  useSuspenseWorkflow,
  useUpdateWorkflowName,
} from "@/features/workflows/hooks/use-workflows";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Loader2, Save } from "lucide-react"; // Loader icon add kiya
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useReactFlow } from "@xyflow/react"; // 👈 Graph data lenay k liye
import { trpc } from "@/trpc/client";
import { toast } from "sonner"; // 👈 Success message k liye

export const EditorHeader = ({ workflowId }: { workflowId: string }) => {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b bg-background px-4">
      <div className="flex w-full flex-row items-center gap-x-4">
        <EditorBreadcrumbs workflowId={workflowId} />
        {/* ✅ Workflow ID pass ki taake save ho sakay */}
        <EditorSaveButton workflowId={workflowId} />
      </div>
    </header>
  );
};

const EditorBreadcrumbs = ({ workflowId }: { workflowId: string }) => {
  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link href="/workflows">Workflows</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          <EditorNameInput workflowId={workflowId} />
        </BreadcrumbItem>
      </BreadcrumbList>
    </Breadcrumb>
  );
};

const EditorNameInput = ({ workflowId }: { workflowId: string }) => {
  const workflow = useSuspenseWorkflow(workflowId);
  const updateWorkflow = useUpdateWorkflowName();

  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(workflow.name);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleSave = async () => {
    if (name === workflow.name) {
      setIsEditing(false);
      return;
    }

    if (name.trim() === "") {
      setName(workflow.name);
      setIsEditing(false);
      return;
    }

    try {
      await updateWorkflow.mutateAsync({
        id: workflowId,
        name: name,
      });
      toast.success("Workflow renamed"); // Toast add kiya
    } catch (error) {
      setName(workflow.name);
      toast.error("Failed to rename workflow");
    } finally {
      setIsEditing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
    } else if (e.key === "Escape") {
      setName(workflow.name);
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <Input
        ref={inputRef}
        value={name}
        onChange={(e) => setName(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className="h-7 w-auto min-w-[100px] px-2"
        disabled={updateWorkflow.isPending}
      />
    );
  }

  return (
    <div
      onClick={() => setIsEditing(true)}
      className="flex cursor-pointer items-center gap-1 font-medium transition-colors hover:text-foreground">
      {workflow.name}
    </div>
  );
};

// 👇 MAIN UPDATE: Save Button Logic
const EditorSaveButton = ({ workflowId }: { workflowId: string }) => {
  // 1. React Flow se instance lene ka hook
  // (NOTE: Iske liye Header ka ReactFlowProvider ke andar hona zaroori hai)
  const { toObject } = useReactFlow();

  // 2. Database mutation hook
  const updateWorkflow = trpc.workflows.update.useMutation({
    onSuccess: () => {
      toast.success("Workflow saved successfully");
    },
    onError: () => {
      toast.error("Something went wrong while saving");
    },
  });

  const handleSave = () => {
    // 3. Graph ka snapshot lena (Nodes, Edges, Viewport sab copy hoga)
    const snapshot = toObject();

    // 4. Mutation call karna
    updateWorkflow.mutate({
      id: workflowId,
      definition: JSON.stringify(snapshot), // Object ko string bana kar bhejna
    });
  };

  return (
    <div className="ml-auto">
      <Button
        size="sm"
        onClick={handleSave}
        disabled={updateWorkflow.isPending}
        variant="outline">
        {updateWorkflow.isPending ? (
          <Loader2 className="mr-2 size-4 animate-spin" />
        ) : (
          <Save className="mr-2 size-4" />
        )}
        Save
      </Button>
    </div>
  );
};
