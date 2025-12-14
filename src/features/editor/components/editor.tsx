"use client";

import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useReactFlow,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRef, useCallback } from "react";

// Hook import
import { useEditor } from "@/features/editor/hooks/use-editor";

// Custom Components Imports
import { CustomNode } from "./custom-node";
import { EditorSidebar } from "./editor-sidebar";

// 1. Node Types Register karna (Taky ReactFlow ko pata ho k 'NodebaseNode' kya hai)
const nodeTypes = {
  NodebaseNode: CustomNode, // Humara naya card style
};

const EditorContent = () => {
  // Make sure apka useEditor hook 'setNodes' return kar raha ho
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    onInit,
    setNodes,
  } = useEditor();

  const { screenToFlowPosition } = useReactFlow();
  const wrapperRef = useRef<HTMLDivElement>(null);

  // 2. Drag Over Handler (Allow Drop)
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // 3. Drop Handler (Jab user card choray ga)
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData("application/reactflow");

      // Agar type undefined hai to wapis jao
      if (typeof type === "undefined" || !type) {
        return;
      }

      // Mouse ki position calculate karna
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      // Naya Node Create karna
      const newNode = {
        id: crypto.randomUUID(),
        type: "NodebaseNode", // Ye upar walay 'nodeTypes' se match hona chahiye
        position,
        data: { label: type, description: "New action node" },
      };

      // State update karna
      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Sidebar Left Side Par */}
      <EditorSidebar />

      {/* Canvas Right Side Par */}
      <div className="flex-1 h-full bg-background" ref={wrapperRef}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={onInit}
          onDragOver={onDragOver}
          onDrop={onDrop}
          nodeTypes={nodeTypes} // 👈 Custom Nodes yahan pass kiye
          minZoom={0.1}
          maxZoom={2}
          fitView>
          <Background gap={12} size={1} />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
};

export const Editor = ({ workflowId }: { workflowId: string }) => {
  return (
    <ReactFlowProvider>
      <EditorContent />
    </ReactFlowProvider>
  );
};
