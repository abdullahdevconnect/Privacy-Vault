import prisma from "@/lib/db";
import { inngest } from "./client";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { createOpenAI } from "@ai-sdk/openai"; // Fixed: Capitalization of 'AI'
import { createAnthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";

const google = createGoogleGenerativeAI();
const openai = createOpenAI();
const anthropic = createAnthropic();

export const execute = inngest.createFunction(
  { id: "execute-ai" },
  {
    event: "execute/ai",
    retries: 3,
  },
  async ({ event, step }) => {
    await step.sleep("pretend to execute", 1000);

    // Note: 'steps' property is usually populated when using tools/maxSteps.
    // For simple text generation, the main result is in the 'text' property,
    // but keeping your destructuring logic as requested.

    const { steps: geminiSteps } = await step.ai.wrap(
      "gemini-generate-text",
      generateText,
      {
        model: google("gemini-1.5-flash"), // Fixed: Changed to valid model ID
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
      }
    );

    const { steps: openaiSteps } = await step.ai.wrap(
      "openai-generate-text",
      generateText,
      {
        model: openai("gpt-4"), // Fixed: Changed 'gpt4' to 'gpt-4'
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
      }
    );

    const { steps: anthropicSteps } = await step.ai.wrap(
      "anthropic-generate-text",
      generateText,
      {
        model: anthropic("claude-3-opus-20240229"), 
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
      }
    );

    return {
      name: "execute/ai",
      data: {
        
        geminiSteps,
        openaiSteps,
        anthropicSteps,
      },
    };
  }
);
