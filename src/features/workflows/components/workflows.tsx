//F:\nodebase_final_pro\src\features\workflows\components\workflows.tsx
"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  MoreHorizontal,
  Play,
  Calendar,
  LayoutGrid,
  List,
  Webhook,
  Clock,
  Zap,
  MousePointerClick,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

// --- Imports from Shared Components ---
import {
  EntityContainer,
  EntityHeader,
  EntityPagination,
  EntitySearch,
  EntityItem,
  EmptyView,
  NoResultsView,
} from "@/components/entity-components";

// --- Hooks ---
import { useWorkflows, useCreateWorkflow } from "../hooks/use-workflows";

import { useEntitySearch } from "@/hooks/use-entity-search";
import { useUpgradeModal } from "@/hooks/use-upgrade-modal";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { useWorkflowsParams } from "../params";

// --- HELPER: Get Dynamic Icon ---
const getWorkflowIcon = (type: string) => {
  switch (type) {
    case "WEBHOOK":
      return <Webhook className="h-5 w-5 text-orange-500" />;
    case "SCHEDULE":
      return <Clock className="h-5 w-5 text-blue-500" />;
    case "MANUAL":
      return <MousePointerClick className="h-5 w-5 text-purple-500" />;
    default:
      return <Zap className="h-5 w-5 text-yellow-500" />;
  }
};

// ------------------------------------------------------------------
// MAIN COMPONENT: WorkflowsList
// ------------------------------------------------------------------
export const WorkflowsList = () => {
  const [params, setParams] = useWorkflowsParams();
  const router = useRouter();
  const createWorkflow = useCreateWorkflow();
  const { handleError } = useUpgradeModal();
  const [view, setView] = useState<"grid" | "list">("grid");

  // ✅ 1. FETCH REAL DATA
  const { data, isLoading, isError } = useWorkflows();

  // Data structure from tRPC router: { items: [], totalPages: ... }
  const workflows = data?.items || [];
  const totalPages = data?.totalPages || 1;

  // --- Handlers ---
  const handleCreate = () => {
    createWorkflow.mutate(undefined, {
      onSuccess: (newWorkflow) => {
        toast.success("Workflow created");
        router.push(`/workflows/${newWorkflow.id}`);
      },
      onError: (err) => {
        if (!handleError(err)) {
          toast.error("Failed to create workflow");
        }
      },
    });
  };

  // --- Loading State ---
  if (isLoading) {
    return (
      <div className="flex h-60 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // --- Error State ---
  if (isError) {
    return (
      <div className="flex h-60 flex-col items-center justify-center gap-2 text-destructive">
        <p>Something went wrong fetching workflows.</p>
        <Button variant="outline" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  // --- Empty Search Results ---
  if (workflows.length === 0 && params.search) {
    return (
      <NoResultsView
        title="No workflows found"
        message={`No results found for "${params.search}".`}
        action={
          <div className="flex items-center gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setParams({ search: null })}>
              Clear Search
            </Button>
            <Button onClick={handleCreate} disabled={createWorkflow.isPending}>
              New Workflow
            </Button>
          </div>
        }
      />
    );
  }

  // --- No Workflows Created Yet ---
  if (workflows.length === 0 && !params.search) {
    return (
      <EmptyView
        title="No workflows created"
        message="You haven't created any workflows yet. Click below to get started."
        entity="workflows"
        action={
          <Button
            size="lg"
            className="mt-4"
            onClick={handleCreate}
            disabled={createWorkflow.isPending}>
            Create your first workflow
          </Button>
        }
      />
    );
  }

  // --- Render List ---
  return (
    <div className="flex flex-col gap-4">
      {/* View Switcher */}
      <div className="flex justify-end items-center">
        <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-lg border">
          <Button
            variant={view === "grid" ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8"
            onClick={() => setView("grid")}>
            <LayoutGrid className="h-4 w-4" />
          </Button>
          <Button
            variant={view === "list" ? "secondary" : "ghost"}
            size="icon"
            className="h-8 w-8"
            onClick={() => setView("list")}>
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Workflows Grid/List */}
      <div
        className={cn(
          "grid gap-4",
          view === "grid"
            ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
            : "grid-cols-1"
        )}>
        {workflows.map((workflow: any) => (
          <EntityItem
            key={workflow.id}
            variant={view}
            href={`/workflows/${workflow.id}`}
            title={workflow.name}
            // ✅ Dynamic Icon based on Trigger Type (defaults if missing)
            image={
              <div
                className={cn(
                  "flex items-center justify-center rounded-lg border bg-muted/30 transition-colors group-hover:bg-muted/50",
                  view === "list" ? "h-9 w-9" : "h-12 w-12"
                )}>
                {/* Agar DB main triggerType field nahi hai to DEFAULT icon aayega */}
                {getWorkflowIcon(workflow.triggerType || "DEFAULT")}
              </div>
            }
            subtitle={
              <div
                className={
                  view === "list" ? "flex items-center gap-4" : "space-y-2"
                }>
                {/* Description (Grid only) */}
                {view === "grid" && (
                  <p className="line-clamp-2 text-muted-foreground">
                    {workflow.description || "No description"}
                  </p>
                )}

                {/* Meta Info (Badges & Dates) */}
                <div className="flex items-start justify-between gap-2 flex-wrap mt-2">
                  {/* Status Badge */}
                  <Badge
                    variant={
                      workflow.status === "ACTIVE" ? "default" : "secondary"
                    }
                    className={
                      workflow.status === "ACTIVE"
                        ? "bg-green-600 hover:bg-green-700"
                        : ""
                    }>
                    {workflow.status === "ACTIVE" ? "Active" : "Draft"}
                  </Badge>

                  {/* Dates */}
                  <div className="flex flex-col items-end gap-1 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>
                        Created{" "}
                        {formatDistanceToNow(new Date(workflow.createdAt), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      <span>
                        Updated{" "}
                        {formatDistanceToNow(new Date(workflow.updatedAt), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            }
            actions={
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 hover:bg-muted"
                    onClick={(e) => e.stopPropagation()}>
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/workflows/${workflow.id}`);
                    }}>
                    <Play className="mr-2 h-4 w-4" /> Open Editor
                  </DropdownMenuItem>
                  {/* Add Delete/Rename options here in future */}
                </DropdownMenuContent>
              </DropdownMenu>
            }
          />
        ))}
      </div>
    </div>
  );
};

// --- Workflows Pagination Component ---
export const WorkflowsPagination = () => {
  const [params, setParams] = useWorkflowsParams();
  const { data } = useWorkflows();

  const currentPage = params.page || 1;
  const totalPages = data?.totalPages || 1;

  // Agar sirf 1 page hai to pagination mat dikhao
  if (totalPages <= 1) return null;

  return (
    <EntityPagination
      page={currentPage}
      totalPages={totalPages}
      onPageChange={(newPage) => setParams({ page: newPage })}
    />
  );
};

// --- Baaki Components (Header, Search etc.) Same Rahenge ---
export const WorkflowsSearch = ({ disabled }: { disabled?: boolean }) => {
  const [params, setParams] = useWorkflowsParams();
  const { search, setSearch } = useEntitySearch({
    params,
    setParams,
    debounceMs: 500,
  });
  return (
    <EntitySearch
      value={search}
      onChange={setSearch}
      placeholder="Search workflows..."
    />
  );
};

export const WorkflowsHeader = ({ disabled }: { disabled?: boolean }) => {
  const createWorkflow = useCreateWorkflow();
  const router = useRouter();
  const { handleError, modal } = useUpgradeModal();
  return (
    <>
      {modal}
      <EntityHeader
        title="Workflows"
        description="Create and manage your workflows"
        onNew={() =>
          createWorkflow.mutate(undefined, {
            onSuccess: (d: any) => router.push(`/workflows/${d.id}`),
            onError: handleError,
          })
        }
        newButtonLabel="New workflow"
        disabled={disabled || createWorkflow.isPending}
        isCreating={createWorkflow.isPending}
      />
    </>
  );
};

export const WorkflowsContainer = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return (
    <EntityContainer
      header={<WorkflowsHeader />}
      search={<WorkflowsSearch />}
      pagination={<WorkflowsPagination />}>
      {children}
    </EntityContainer>
  );
};
