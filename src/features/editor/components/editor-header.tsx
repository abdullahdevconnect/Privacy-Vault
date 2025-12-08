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
import { Save } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

export const EditorHeader = ({ workflowId }: { workflowId: string }) => {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b bg-background px-4">
      <div className="flex w-full flex-row items-center gap-x-4">
        <EditorBreadcrumbs workflowId={workflowId} />
        <EditorSaveButton />
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
    } catch (error) {
      // Revert name on error
      setName(workflow.name);
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

const EditorSaveButton = () => {
  // Logic for saving graph state will be added later
  return (
    <div className="ml-auto">
      <Button size="sm" onClick={() => {}} disabled={false} variant="outline">
        <Save className="mr-2 size-4" />
        Save
      </Button>
    </div>
  );
};
