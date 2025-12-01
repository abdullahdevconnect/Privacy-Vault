import { checkout, polar, portal } from "@polar-sh/better-auth";
import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import db from "@/lib/db";
import { polarClient } from "./polar";

export const auth = betterAuth({
  database: prismaAdapter(db, {
    provider: "postgresql",
  }),

  emailAndPassword: {
    enabled: true,
    autoSignIn: true,
  },
  plugins: [
    polar({
      client: polarClient,
      createCustomerOnSignUp: true,
      use: [
        checkout({
          products: [
            {
              productId: "9e8398d2-f0dc-4927-bbfc-0eb17db96ce5",
              slug: "pro",
            },
          ],
          successUrl: process.env.POLAR_SUCCESS_URL, // Ensure this ENV is set
          authenticatedUsersOnly: true,
        }),
        portal({}),
      ],
    }),
  ],
});
