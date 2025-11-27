import prisma from "@/lib/db";
import { inngest } from "./client";

export const helloWorld = inngest.createFunction(
  { id: "hello-world" },
  {
    event: "test/hello.world",
    retries: 3,
    retryDelay: ({ retry }: { retry: number }) => retry * 5000, // 5s, 10s, 15s
  },
  async ({ event, step }) => {
    // Step 1
    await step.sleep("Fetching the video", "5s");

    // Step 2
    await step.sleep("Transcribing the video", "5s");

    // Step 3
    await step.sleep("Sending transcription to AI", "5s");

    // Step 4 - Create Workflow
    const workflow = await step.run("create-workflow", async () => {
      return prisma.workflow.create({
        data: {
          name: "workflow-from-inngest",
        },
      });
    });

    return { message: `Hello ${event.data.email}!`, workflow };
  }
);
