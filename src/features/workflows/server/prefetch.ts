import { trpc } from "@/trpc/server";

export const prefetchWorkflow = async (id: string) => {
  // Hum 'getById' use kar rahe hain kyunke router main humne yahi naam rakha tha
  await trpc.workflows.getById.prefetch({ id });
};
