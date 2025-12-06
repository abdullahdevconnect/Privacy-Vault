//F:\nodebase_final_pro\src\hooks\use-upgrade-modal.tsx
import { TRPCClientError } from "@trpc/client";
import { useState, useCallback } from "react";
import { UpgradeModal } from "@/components/upgrade-modal";

export const useUpgradeModal = (): {
  open: boolean;
  setOpen: (open: boolean) => void;
  handleError: (error: unknown) => boolean;
  modal: React.ReactNode;
} => {
  const [open, setOpen] = useState(false);

  // useCallback add kiya taake function reference stable rahe
  const handleError = useCallback((error: unknown) => {
    if (error instanceof TRPCClientError) {
      if (error.data?.code === "FORBIDDEN") {
        setOpen(true);
        return true;
      }
    }
    return false;
  }, []);

  return {
    open,
    setOpen,
    handleError,
    modal: <UpgradeModal open={open} onOpenChange={setOpen} />,
  };
};
