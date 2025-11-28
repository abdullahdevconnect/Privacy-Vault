import { inngest } from "@/inngest/client";
import { baseProcedure, createTRPCRouter, protectedProcedure } from "../init";
import prisma from "@/lib/db";
import { google } from "@ai-sdk/google";
import { generateText } from "ai";

export const appRouter = createTRPCRouter({
  getWorkflows: protectedProcedure.query(() => {
    return prisma.workflow.findMany();
  }),

  testAi: baseProcedure.mutation(async () => {
    await inngest.send({
      name: "execute/ai",
    });

    return {
      success: true,
      message: "Job sent to Inngest! Workflow queued successfully!",
    };
  }),

  createWorkflow: protectedProcedure.mutation(async () => {
    // Send event to Inngest
    await inngest.send({
      name: "test/hello.world",
      data: {
        email: "Abdullah@arqsis.com",
      },
    });

    return {
      success: true,
      message: "Job sent to Inngest! Workflow queued successfully!",
    };
  }),
});

// export type definition of API
export type AppRouter = typeof appRouter;
