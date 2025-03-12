import { ConnectButton } from "@rainbow-me/rainbowkit";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/router";
import logo from "../../../public/logo.png";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout = ({ children }: LayoutProps) => {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 to-gray-800">
      <main className="mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-12">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-3">
              <Image src={logo} alt="Predict Pool" height={42} />
            </div>
            {/* Navigation Links */}
            <nav className="flex space-x-6">
              <Link
                href="/"
                className={`text-lg ${
                  router.pathname === "/"
                    ? "text-white font-semibold"
                    : "text-gray-300 hover:text-white"
                }`}
              >
                Home
              </Link>
              <Link
                href="/predict"
                className={`text-lg ${
                  router.pathname === "/predict"
                    ? "text-white font-semibold"
                    : "text-gray-300 hover:text-white"
                }`}
              >
                Predict
              </Link>
            </nav>
          </div>
          <ConnectButton />
        </div>
        {children}
      </main>
    </div>
  );
};
