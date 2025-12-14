// src/features/editor/components/custom-node.tsx
import { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

export const CustomNode = memo(({ data, selected }: NodeProps) => {
  return (
    <Card
      className={cn(
        "w-[300px] border-2 shadow-sm transition-all",
        selected ? "border-primary" : "border-border"
      )}>
      {/* Top Handle (Input) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-muted-foreground !h-4 !w-4 !-top-2"
      />

      <CardHeader className="flex flex-row items-center gap-4 p-4">
        {/* Drag Handle Icon */}
        <div className="text-muted-foreground cursor-grab">
          <GripVertical size={20} />
        </div>

        <div className="flex flex-col gap-1">
          <CardTitle className="text-md font-semibold flex items-center gap-2">
            {/* Yahan hum future main icon bhi show karenge */}
            {data.label as string}
          </CardTitle>
          <CardDescription className="text-xs">
            {(data.description as string) || "No description"}
          </CardDescription>
        </div>
      </CardHeader>

      {/* Bottom Handle (Output) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !h-4 !w-4 !-bottom-2"
      />
    </Card>
  );
});

CustomNode.displayName = "CustomNode";
