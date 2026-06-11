import type { Metadata } from "next";
import InsightAgentShell from "@/components/insight-agent/app-shell";
import { LocatorRuntime } from "./locator-runtime";
import "./globals.css";
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: "Insight Agent",
  description: "企业级数据智能分析与决策平台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
      <html lang="zh-CN" suppressHydrationWarning className={cn("font-sans", geist.variable)}>
        <body>
          <LocatorRuntime />
          <TooltipProvider>
            <InsightAgentShell>{children}</InsightAgentShell>
          </TooltipProvider>
        </body>
      </html>
    );
  }
