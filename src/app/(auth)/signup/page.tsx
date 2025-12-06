//F:\nodebase_final_pro\src\app\(auth)\signup\page.tsx
import RegisterForm from "@/features/auth/components/register-form"; 
import { requireUnauth } from "@/lib/auth-utils";

const Page = async () => {
  await requireUnauth();
  return <RegisterForm />;
};

export default Page;
