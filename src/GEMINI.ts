// To run this code you need to install the following dependencies:
// npm install @google/genai mime
// npm install -D @types/node

// FIX 1: Import 'ThinkingLevel' along with GoogleGenAI
import { GoogleGenAI, ThinkingLevel } from "@google/genai";

async function main() {
  const ai = new GoogleGenAI({
    apiKey: process.env.GEMINI_API_KEY,
  });

  const tools = [
    {
      googleSearch: {},
    },
  ];

  const config = {
    thinkingConfig: {
      // FIX 2: Use the Enum member 'ThinkingLevel.HIGH' instead of the string "HIGH"
      thinkingLevel: ThinkingLevel.HIGH,
    },
    tools,
    responseMimeType: "application/json",
  };

  const model = "gemini-3-pro-preview";

  const contents = [
    {
      role: "user",
      parts: [
        {
          text: `INSERT_INPUT_HERE`,
        },
      ],
    },
  ];

  const response = await ai.models.generateContentStream({
    model,
    config,
    contents,
  });

  let fileIndex = 0;
  for await (const chunk of response) {
    console.log(chunk.text);
  }
}

main();
