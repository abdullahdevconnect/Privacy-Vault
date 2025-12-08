"use client";
import { TriangleAlert } from "lucide-react";

export const EditorError = () => {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-destructive">
      <TriangleAlert className="size-10" />
      <p>Failed to load editor</p>
    </div>
  );
};
