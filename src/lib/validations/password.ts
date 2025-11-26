// lib/validations/password.ts
import zxcvbn from "zxcvbn";
import { z } from "zod";

export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password must be less than 128 characters")
  .refine(
    (password) => {
      const result = zxcvbn(password);
      return result.score >= 3; // Require "Strong" or "Very Strong"
    },
    {
      message: "Password is too weak. Please choose a stronger password.",
    }
  );

export const loginPasswordSchema = z.string().min(1, "Password is required");

export const emailSchema = z
  .string()
  .email("Please enter a valid email address")
  .min(1, "Email is required");
