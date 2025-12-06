//F:\nodebase_final_pro\src\app\(auth)\login\page.tsx
import LoginForm from "@/features/auth/components/login-form"; 
import { requireUnauth } from "@/lib/auth-utils";

const Page = async () => {
  await requireUnauth();
  return <LoginForm />;
};

export default Page;
