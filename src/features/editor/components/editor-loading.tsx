"use client";
import { Loader2 } from "lucide-react";

export const EditorLoading = () => {
  return (
    <div className="flex h-full w-full items-center justify-center">
      <Loader2 className="size-10 animate-spin text-muted-foreground" />
    </div>
  );
};
