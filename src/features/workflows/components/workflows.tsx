"use client";

import { EntityContainer, EntityHeader } from "@/components/entity-components";
import {
  useCreateWorkflow,
  useSuspenseWorkflows,
} from "../hooks/use-workflows";
import { useUpgradeModal } from "@/hooks/use-upgrade-modal";
import React from "react";
import { useRouter } from "next/navigation";

export const WorkflowsList = () => {
  // FIX: Destructure the array.
  // The first item is the data, the second is the query info.
  const [workflows] = useSuspenseWorkflows();

  return (
    <div className="flex-1 flex justify-center items-center">
      {/* workflows is now the direct array, no need for .data */}
      <p>{JSON.stringify(workflows, null, 2)}</p>
    </div>
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

export const WorkflowsContainer = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return (
    <EntityContainer
      header={<WorkflowsHeader />}
      search={<></>}
      pagination={<></>}>
      {children}
    </EntityContainer>
  );
};
