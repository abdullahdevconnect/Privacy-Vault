// src/features/editor/hooks/use-editor.ts
import { useCallback, useState } from "react";
import {
  addEdge,
  Connection,
  EdgeChange,
  NodeChange,
  ReactFlowInstance,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";

import { EditorEdge, EditorNode } from "../types";

// ✅ UPDATED: Ab humara custom card "NodebaseNode" use hoga
const initialNodes: EditorNode[] = [
  {
    id: "n1",
    type: "NodebaseNode", // 👈 Default box ki jagah Custom Card
    position: { x: 100, y: 100 },
    data: { label: "Start Trigger", description: "Entry point for flow" },
  },
];

const initialEdges: EditorEdge[] = [];

export const useEditor = () => {
  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance | null>(null);

  const [nodes, setNodes] = useState<EditorNode[]>(initialNodes);
  const [edges, setEdges] = useState<EditorEdge[]>(initialEdges);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((eds) => applyEdgeChanges(changes, eds));
  }, []);

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds));
  }, []);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    setReactFlowInstance(instance);
  }, []);

  return {
    onInit,
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    setNodes, // ✅ FIX: Ye line bohot zaroori hai Drag & Drop k liye
    setEdges, // Future usage k liye
  };
};
