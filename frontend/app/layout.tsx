import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Career Agent",
  description: "Resume analysis, job matching, and tailoring dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <nav className="nav">
            <div className="nav-title">AI Career Agent</div>
            <div className="nav-links">
              <Link href="/">Resume</Link>
              <Link href="/jobs">Jobs</Link>
              <Link href="/matches">Matches</Link>
              <Link href="/tracker">Tracker</Link>
            </div>
          </nav>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
