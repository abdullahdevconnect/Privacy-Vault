//F:\nodebase_final_pro\src\inngest\functions.ts
import { inngest } from "./client";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { createOpenAI } from "@ai-sdk/openai";
import { createAnthropic } from "@ai-sdk/anthropic";
import { generateText } from "ai";
import * as Sentry from "@sentry/nextjs";

// Initialize providers (Ensure ENV variables are set for these)
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

    // ✅ FIX: Use public API to send logs to Sentry
    Sentry.captureMessage("User triggered test log", {
      level: "info",
      extra: {
        log_source: "sentry_test",
      },
    });

    console.warn("Something is missing");
    console.error("This is an error i want to track");

    // FIX: generateText returns { text, usage, ... }, not { steps }
    const geminiResult = await step.ai.wrap(
      "gemini-generate-text",
      generateText,
      {
        model: google("gemini-2.5-flash"), 
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
        experimental_telemetry: {
          isEnabled: true,
          recordInputs: true,
          recordOutputs: true,
        },
      }
    );

    const openaiResult = await step.ai.wrap(
      "openai-generate-text",
      generateText,
      {
        model: openai("gpt-4"),
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
        experimental_telemetry: {
          isEnabled: true,
          recordInputs: true,
          recordOutputs: true,
        },
      }
    );

    const anthropicResult = await step.ai.wrap(
      "anthropic-generate-text",
      generateText,
      {
        model: anthropic("claude-3-opus-20240229"),
        system: "You are a helpful assistant.",
        prompt: "What is 2 + 2?",
        experimental_telemetry: {
          isEnabled: true,
          recordInputs: true,
          recordOutputs: true,
        },
      }
    );

    return {
      name: "execute/ai",
      data: {
        geminiResult,
        openaiResult,
        anthropicResult,
      },
    };
  }
);
