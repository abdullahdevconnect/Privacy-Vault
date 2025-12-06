//F:\nodebase_final_pro\src\app\(dashboard)\(rest)\credentials\page.tsx
import { requireAuth } from "@/lib/auth-utils";

const Page = async () => {
  await requireAuth();
  return <p>Credentials</p>;
};

export default Page;
