import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — Enex",
  description:
    "Terms of Service for using Enex, the analyst prediction tracker for Indian equity markets.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="mb-8 text-3xl font-bold">Terms of Service</h1>

      <div className="space-y-8 text-sm leading-relaxed text-foreground/90">
        <p className="text-muted-foreground">
          Last updated: February 2026
        </p>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            1. Acceptance of Terms
          </h2>
          <p>
            By accessing or using Enex, you agree to be bound by these Terms of
            Service. If you do not agree to these terms, you must not use the
            platform.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">2. What Enex Is</h2>
          <p>
            Enex is a data aggregation platform that tracks publicly available
            stock price target predictions made by analysts, brokerage firms,
            research houses, media personalities, and influencers in the Indian
            equity market. We evaluate these predictions against actual market
            outcomes and rank predictors by accuracy.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            3. No Investment Advice
          </h2>
          <p>
            Enex is <strong>not</strong> a registered investment advisor or
            research analyst under SEBI (Securities and Exchange Board of India)
            regulations. All prediction accuracy data, scores, and rankings
            displayed on this platform are provided for{" "}
            <strong>informational and educational purposes only</strong>.
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              Past prediction accuracy does not guarantee future results.
            </li>
            <li>
              Nothing on Enex constitutes a recommendation to buy, sell, or hold
              any security.
            </li>
            <li>
              Users make all investment decisions entirely at their own risk.
            </li>
            <li>
              Always consult a qualified financial advisor before making
              investment decisions.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">4. User Accounts</h2>
          <p>
            You may create one account per person. You must provide accurate
            information when registering. Accounts may be suspended or
            permanently banned for violations of these terms, including but not
            limited to providing false information, operating multiple accounts,
            or engaging in prohibited behaviour.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">5. Acceptable Use</h2>
          <p>You agree not to:</p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              Scrape, crawl, or use automated tools to extract data from the
              platform without prior written permission.
            </li>
            <li>
              Submit spam, duplicate, or fabricated predictions.
            </li>
            <li>
              Impersonate any person or entity, including analysts or
              predictors tracked on the platform.
            </li>
            <li>
              Attempt to manipulate prediction data, scores, or rankings.
            </li>
            <li>
              Interfere with the operation, security, or availability of the
              platform.
            </li>
          </ul>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            6. Content &amp; Submissions
          </h2>
          <p>
            By submitting predictions, suggestions, or other content to Enex,
            you grant the platform a non-exclusive, royalty-free, worldwide
            licence to display, process, evaluate, and store that content as
            part of the service. AI-assisted extraction (powered by Anthropic
            Claude) is used to parse predictions from submitted URLs; all
            AI-extracted data is reviewed by human moderators before publication.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">7. Predictor Rights</h2>
          <p>
            Predictors tracked on Enex are sourced from publicly available
            information including news articles, interviews, research reports,
            social media, and podcasts. If you are a tracked predictor and wish
            to request corrections to your profile or the removal of your
            profile from the platform, please contact us using the details on
            our{" "}
            <a href="/contact" className="underline hover:text-foreground">
              Contact page
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            8. Intellectual Property
          </h2>
          <p>
            The platform design, code, branding, and original content are owned
            by Enex. Prediction data aggregated on the platform is factual
            information sourced from public records and is not claimed as
            proprietary content.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">
            9. Limitation of Liability
          </h2>
          <p>
            To the fullest extent permitted by law, Enex and its operators shall
            not be liable for:
          </p>
          <ul className="ml-4 mt-2 list-disc space-y-1">
            <li>
              Any investment losses incurred based on information displayed on
              the platform.
            </li>
            <li>
              Inaccuracies in prediction data, evaluation scores, or rankings.
            </li>
            <li>
              Service interruptions, downtime, or data loss.
            </li>
          </ul>
          <p className="mt-2">
            The platform is provided on an &ldquo;as is&rdquo; and &ldquo;as
            available&rdquo; basis without warranties of any kind.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">10. Modifications</h2>
          <p>
            We may update these Terms of Service from time to time. Continued
            use of the platform after changes constitutes acceptance of the
            revised terms. Material changes will be communicated via
            announcement banner on the platform or email notification to
            registered users.
          </p>
        </section>

        <section>
          <h2 className="mb-3 text-xl font-semibold">11. Governing Law</h2>
          <p>
            These terms are governed by and construed in accordance with the
            laws of India. Any disputes arising from the use of the platform
            shall be subject to the exclusive jurisdiction of the courts of
            India.
          </p>
        </section>
      </div>
    </div>
  );
}
