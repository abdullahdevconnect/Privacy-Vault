//F:\nodebase_final_pro\src\app\(dashboard)\(rest)\executions\page.tsx
import { requireAuth } from "@/lib/auth-utils";

const Page = async () => {
  await requireAuth();
  return <p>Executions</p>;
};

export default Page;
