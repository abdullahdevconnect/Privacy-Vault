"use client";

import {
  EntityContainer,
  EntityHeader,
  EntityPagination, // ✅ Import EntityPagination
  EntitySearch,
} from "@/components/entity-components";
import {
  useCreateWorkflow,
  useSuspenseWorkflows,
} from "../hooks/use-workflows";
import { useWorkflowsParams } from "../hooks/use-workflows-params";
import { useEntitySearch } from "@/hooks/use-entity-search";
import { useUpgradeModal } from "@/hooks/use-upgrade-modal";
import React from "react";
import { useRouter } from "next/navigation";

// --- Workflows List ---
export const WorkflowsList = () => {
  const [workflows] = useSuspenseWorkflows();

  return (
    <div className="flex-1 flex justify-center items-center">
      <p>{JSON.stringify(workflows, null, 2)}</p>
    </div>
  );
};

// --- Workflows Search ---
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

// --- Workflows Pagination (✅ NEW Component) ---
export const WorkflowsPagination = () => {
  // Data fetch karein (Backend se totalPages milta hai)
  const [data] = useSuspenseWorkflows();
  // URL update karne ke liye params hook
  const [, setParams] = useWorkflowsParams();

  return (
    <EntityPagination
      page={data.page}
      totalPages={data.totalPages}
      onPageChange={(page) => setParams({ page })}
    />
  );
};

// --- Workflows Header ---
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
            onSuccess: (data) => {
              router.push(`/workflows/${data.id}`);
            },
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

// --- Workflows Container ---
export const WorkflowsContainer = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return (
    <EntityContainer
      header={<WorkflowsHeader />}
      search={<WorkflowsSearch />}
      pagination={<WorkflowsPagination />} 
    >
      {children}
    </EntityContainer>
  );
};
