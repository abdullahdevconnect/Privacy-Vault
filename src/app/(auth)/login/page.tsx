import LoginForm from "@/features/auth/components/login-form"; // ✅ Fixed typo
import { requireUnauth } from "@/lib/auth-utils";

const Page = async () => {
  await requireUnauth();
  return <LoginForm />;
};

export default Page;
