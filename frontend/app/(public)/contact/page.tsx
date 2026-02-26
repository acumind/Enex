import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact — Enex",
  description:
    "Get in touch with the Enex team for questions, feedback, predictor profile issues, or data requests.",
};

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">Contact</h1>

      <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
        <section>
          <h2 className="mb-3 text-xl font-semibold">General Inquiries</h2>
          <p>
            For general questions about Enex, how the platform works, or
            partnership opportunities, email us at{" "}
            <a
              href="mailto:hello@enex.in"
              className="underline hover:text-foreground"
            >
              hello@enex.in
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            Predictor Profile Issues
          </h2>
          <p>
            If you are a predictor tracked on Enex and wish to request
            corrections to your profile, dispute a prediction attribution, or
            request removal of your profile, please email{" "}
            <a
              href="mailto:hello@enex.in"
              className="underline hover:text-foreground"
            >
              hello@enex.in
            </a>{" "}
            with the subject line &ldquo;Predictor Profile Request&rdquo;.
            Include your name or the predictor profile in question, and a
            description of the issue.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            Bug Reports &amp; Feedback
          </h2>
          <p>
            Found a bug or have a suggestion? You can:
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              Open an issue on our{" "}
              <a
                href="https://github.com/acumind/Enex/issues"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-foreground"
              >
                GitHub repository
              </a>
              .
            </li>
            <li>
              Email us at{" "}
              <a
                href="mailto:hello@enex.in"
                className="underline hover:text-foreground"
              >
                hello@enex.in
              </a>
              .
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            Privacy &amp; Data Requests
          </h2>
          <p>
            For requests related to your personal data under the Digital
            Personal Data Protection Act (DPDPA) 2023 — including access,
            correction, erasure, or grievance redressal — please email{" "}
            <a
              href="mailto:privacy@enex.in"
              className="underline hover:text-foreground"
            >
              privacy@enex.in
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">Response Time</h2>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              <strong>General inquiries</strong> — 48 to 72 hours.
            </li>
            <li>
              <strong>Data &amp; privacy requests</strong> — Within 7 working
              days.
            </li>
            <li>
              <strong>Bug reports</strong> — Acknowledged within 48 hours;
              resolution time depends on severity.
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
