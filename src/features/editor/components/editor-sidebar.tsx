// src/features/editor/components/editor-sidebar.tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export const EditorSidebar = () => {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <aside className="w-[380px] h-full border-r bg-muted/20 p-4 flex flex-col gap-4 overflow-y-auto">
      <CardHeader className="p-0">
        <CardTitle>Elements</CardTitle>
        <CardDescription>Drag cards to the canvas</CardDescription>
      </CardHeader>
      <Separator />

      <div className="flex flex-col gap-4">
        <div className="text-sm font-medium text-muted-foreground">
          Triggers
        </div>

        {/* Draggable Card 1 */}
        <Card
          className="cursor-grab hover:border-primary transition-colors p-4 flex items-center gap-2"
          draggable
          onDragStart={(e) => onDragStart(e, "Slack")}>
          <div className="font-semibold">Slack Message</div>
        </Card>

        {/* Draggable Card 2 */}
        <Card
          className="cursor-grab hover:border-primary transition-colors p-4 flex items-center gap-2"
          draggable
          onDragStart={(e) => onDragStart(e, "Discord")}>
          <div className="font-semibold">Discord Notification</div>
        </Card>
      </div>
    </aside>
  );
};
