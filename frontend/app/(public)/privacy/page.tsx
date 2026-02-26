import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — Enex",
  description:
    "How Enex collects, uses, and protects your personal data. DPDPA 2023 compliant.",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">Privacy Policy</h1>

      <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
        <p className="text-muted-foreground">
          Last updated: February 2026
        </p>

        <section>
          <h2 className="mb-3 text-xl font-semibold">1. Overview</h2>
          <p>
            This Privacy Policy describes how Enex collects, uses, stores, and
            protects your personal data when you use our platform. By using
            Enex, you consent to the data practices described in this policy.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">2. Data We Collect</h2>
          <p>We collect the following categories of personal data:</p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              <strong>Account information</strong> — Email address, name, and
              phone number (when provided for OTP-based login).
            </li>
            <li>
              <strong>OAuth data</strong> — Google profile information (name,
              email, profile picture) when you sign in with Google.
            </li>
            <li>
              <strong>Technical data</strong> — IP address, user agent, browser
              type, and login timestamps collected automatically when you access
              the platform.
            </li>
            <li>
              <strong>Submission data</strong> — Predictions, suggestions, and
              URLs you submit to the platform.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            3. How We Use Your Data
          </h2>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              <strong>Authentication</strong> — To verify your identity and
              manage your account.
            </li>
            <li>
              <strong>Notifications</strong> — To send you email updates about
              prediction outcomes, platform announcements, and account activity.
            </li>
            <li>
              <strong>Platform improvement</strong> — To analyse usage patterns
              and improve the user experience.
            </li>
            <li>
              <strong>Abuse prevention</strong> — To detect and prevent spam,
              fraud, and violations of our Terms of Service.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            4. AI &amp; Data Processing
          </h2>
          <p>
            Enex uses the Anthropic Claude API for AI-assisted prediction
            extraction. When you submit an article URL for prediction
            extraction, the content of that URL is sent to Anthropic for
            processing. AI-extracted results are always reviewed by human
            moderators before being published on the platform. Please refer to{" "}
            <a
              href="https://www.anthropic.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              Anthropic&apos;s Privacy Policy
            </a>{" "}
            for details on how they handle data.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            5. Third-Party Services
          </h2>
          <p>
            We share limited data with the following third-party services to
            operate the platform:
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              <strong>Google</strong> — OAuth authentication (receives your
              authorisation grant and returns profile information).
            </li>
            <li>
              <strong>Resend</strong> — Email delivery (receives your email
              address to send notifications).
            </li>
            <li>
              <strong>MSG91</strong> — SMS delivery (receives your phone number
              to send OTP codes).
            </li>
            <li>
              <strong>Anthropic</strong> — AI prediction extraction (receives
              article URL content for processing).
            </li>
            <li>
              <strong>Microsoft Azure</strong> — Cloud hosting (all platform
              data is hosted on Azure infrastructure).
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            6. Cookies &amp; Local Storage
          </h2>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              <strong>JWT access tokens</strong> — Stored as httpOnly cookies
              for secure session management.
            </li>
            <li>
              <strong>Refresh tokens</strong> — Stored as httpOnly cookies for
              session renewal.
            </li>
            <li>
              <strong>Local storage</strong> — Used for UI preferences such as
              theme selection and announcement dismissal state. No personal data
              is stored in local storage.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">7. Data Retention</h2>
          <ul className="ml-4 list-disc space-y-1">
            <li>
              <strong>Account data</strong> — Retained for as long as your
              account is active.
            </li>
            <li>
              <strong>Login events</strong> — Retained for 12 months for
              security and auditing purposes.
            </li>
            <li>
              <strong>OTPs</strong> — Expire after 5 minutes and are
              automatically deleted.
            </li>
            <li>
              <strong>Account deletion</strong> — You may request deletion of
              your account and associated personal data at any time by
              contacting us.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            8. Your Rights (DPDPA 2023)
          </h2>
          <p>
            Under the Digital Personal Data Protection Act, 2023, you have the
            following rights:
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              <strong>Right to access</strong> — Request a summary of the
              personal data we hold about you.
            </li>
            <li>
              <strong>Right to correction</strong> — Request correction of
              inaccurate or incomplete personal data.
            </li>
            <li>
              <strong>Right to erasure</strong> — Request deletion of your
              personal data, subject to legal retention requirements.
            </li>
            <li>
              <strong>Right to grievance redressal</strong> — Raise concerns
              about our data handling practices.
            </li>
          </ul>
          <p className="mt-2">
            To exercise any of these rights, please email us at{" "}
            <a
              href="mailto:privacy@enex.in"
              className="underline hover:text-foreground"
            >
              privacy@enex.in
            </a>
            . We will respond within 7 working days.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">9. Data Security</h2>
          <p>We implement the following measures to protect your data:</p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>Encryption at rest via Azure-managed encryption.</li>
            <li>TLS encryption for all data in transit.</li>
            <li>Hashed OTP storage (OTPs are never stored in plaintext).</li>
            <li>
              Role-based access control limiting data access to authorised
              personnel.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">10. Children</h2>
          <p>
            Enex is not intended for use by individuals under the age of 18. We
            do not knowingly collect personal data from minors. If you believe a
            minor has provided us with personal data, please contact us and we
            will delete it promptly.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            11. Changes to This Policy
          </h2>
          <p>
            We may update this Privacy Policy from time to time. Material
            changes will be communicated via email to registered users or
            through an announcement banner on the platform. Continued use of
            Enex after changes constitutes acceptance of the updated policy.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">12. Contact</h2>
          <p>
            For privacy-related queries or to exercise your data rights, please
            email{" "}
            <a
              href="mailto:privacy@enex.in"
              className="underline hover:text-foreground"
            >
              privacy@enex.in
            </a>
            . For other enquiries, visit our{" "}
            <a href="/contact" className="underline hover:text-foreground">
              Contact page
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
