// components/ui/password-strength.tsx
"use client";

import { useMemo } from "react";
import zxcvbn from "zxcvbn";
import { cn } from "@/lib/utils";

interface PasswordStrengthProps {
  password: string;
  className?: string;
}

const strengthConfig = [
  {
    label: "Very Weak",
    color: "strength-very-weak",
    textColor: "text-red-500",
  },
  { label: "Weak", color: "strength-weak", textColor: "text-orange-500" },
  { label: "Fair", color: "strength-fair", textColor: "text-yellow-600" },
  { label: "Strong", color: "strength-strong", textColor: "text-lime-600" },
  {
    label: "Very Strong",
    color: "strength-very-strong",
    textColor: "text-green-600",
  },
];

export function PasswordStrength({
  password,
  className,
}: PasswordStrengthProps) {
  const result = useMemo(() => {
    if (!password) return null;
    return zxcvbn(password);
  }, [password]);

  if (!password || !result) {
    return null;
  }

  const score = result.score;
  const config = strengthConfig[score];

  return (
    <div className={cn("space-y-2 mt-2 animate-fade-in", className)}>
      {/* Strength Bar */}
      <div className="flex gap-1">
        {[0, 1, 2, 3, 4].map((index) => (
          <div
            key={index}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-all duration-300",
              index <= score ? config.color : "bg-muted"
            )}
          />
        ))}
      </div>

      {/* Strength Label */}
      <div className="flex justify-between items-center text-xs">
        <span className={cn("font-medium", config.textColor)}>
          {config.label}
        </span>

        <span className="text-muted-foreground">
          Crack time:{" "}
          {result.crack_times_display.offline_slow_hashing_1e4_per_second}
        </span>
      </div>

      {/* Feedback */}
      {(result.feedback.warning || result.feedback.suggestions.length > 0) && (
        <div className="text-xs space-y-1 animate-fade-up">
          {result.feedback.warning && (
            <p className="text-warning flex items-center gap-1">
              <span>⚠️</span> {result.feedback.warning}
            </p>
          )}
          {result.feedback.suggestions.map((suggestion, index) => (
            <p
              key={index}
              className="text-muted-foreground flex items-center gap-1">
              <span>💡</span> {suggestion}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
