"use client";

import { Button } from "@/components/ui/button";
import { authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export const LogoutButton = () => {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await authClient.signOut({
        fetchOptions: {
          onSuccess: () => {
            toast.success("Logged out successfully!");
            router.push("/login");
          },
          onError: () => {
            toast.error("Failed to logout. Please try again.");
          },
        },
      });
    } catch (error) {
      toast.error("Something went wrong!");
    }
  };

  return <Button onClick={handleLogout}>Logout</Button>;
};
