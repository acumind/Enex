import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t py-6 text-sm text-muted-foreground">
      <div className="mx-auto max-w-6xl px-4">
        <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
          <p>
            Not financial advice. Predictions tracked for informational purposes
            only.
          </p>
          <div className="flex items-center gap-4">
            <Link
              href="/leaderboard"
              className="transition-colors hover:text-foreground"
            >
              Leaderboard
            </Link>
            <Link
              href="/about"
              className="transition-colors hover:text-foreground"
            >
              About
            </Link>
            <Link
              href="/terms"
              className="transition-colors hover:text-foreground"
            >
              Terms
            </Link>
            <Link
              href="/privacy"
              className="transition-colors hover:text-foreground"
            >
              Privacy
            </Link>
            <Link
              href="/contact"
              className="transition-colors hover:text-foreground"
            >
              Contact
            </Link>
            <span>&copy; {new Date().getFullYear()} Enex</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
