import Link from 'next/link';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700 mb-8 inline-block">&larr; Back to LeadFactory</Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
        <p className="text-sm text-gray-500 mb-10">Last updated: February 22, 2026</p>

        <div className="prose prose-gray max-w-none space-y-6 text-gray-700 text-sm leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing or using the LeadFactory platform (&quot;Service&quot;), you agree to be bound by these
              Terms of Service (&quot;Terms&quot;). If you do not agree, you may not use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">2. Description of Service</h2>
            <p>
              LeadFactory provides a multi-vertical lead generation platform that crawls publicly available
              information from VC fund websites, enriches contact data, and delivers structured leads to
              subscribers. The Service includes web-based dashboards, APIs, and data exports.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">3. Account Registration</h2>
            <p>
              You must provide accurate information when creating an account. You are responsible for
              maintaining the confidentiality of your credentials and for all activities under your account.
              You must notify us immediately of any unauthorized use.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">4. Billing and Credits</h2>
            <p>
              Paid plans are billed monthly via Stripe. Credits are consumed when leads are generated.
              Unused credits do not roll over between billing cycles unless otherwise stated. Credit pack
              purchases are non-refundable once credits have been used. Subscription cancellations take
              effect at the end of the current billing period.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">5. Acceptable Use</h2>
            <p>You agree not to:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li>Use the Service for unsolicited bulk email (spam) in violation of CAN-SPAM, GDPR, or equivalent laws</li>
              <li>Resell or redistribute lead data without authorization</li>
              <li>Attempt to circumvent rate limits, credit systems, or access controls</li>
              <li>Scrape or reverse-engineer the Service</li>
              <li>Use the Service for any unlawful purpose</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">6. Data Accuracy</h2>
            <p>
              Lead data is gathered from publicly available sources and algorithmically enriched. We do not
              guarantee the accuracy, completeness, or deliverability of any contact information. You are
              responsible for verifying data before use and for complying with applicable laws when
              contacting leads.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">7. Intellectual Property</h2>
            <p>
              The Service, including its software, design, and documentation, is the property of
              LeadFactory. You retain ownership of any data you upload. By using the Service, you grant
              us a limited license to process your data solely to provide the Service.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">8. Limitation of Liability</h2>
            <p>
              THE SERVICE IS PROVIDED &quot;AS IS&quot; WITHOUT WARRANTIES OF ANY KIND. IN NO EVENT SHALL
              LEADFACTORY BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES ARISING
              FROM YOUR USE OF THE SERVICE. OUR TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT YOU PAID IN
              THE TWELVE MONTHS PRECEDING THE CLAIM.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">9. Termination</h2>
            <p>
              We may suspend or terminate your account at any time for violation of these Terms. You may
              cancel your account at any time through the dashboard settings. Upon termination, your right
              to use the Service ceases immediately.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">10. Changes to Terms</h2>
            <p>
              We may update these Terms from time to time. Continued use of the Service after changes
              constitutes acceptance. We will notify registered users of material changes via email.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">11. Contact</h2>
            <p>
              For questions about these Terms, contact us at{' '}
              <a href="mailto:legal@leadfactory.io" className="text-blue-600 hover:underline">legal@leadfactory.io</a>.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200 flex gap-6 text-sm text-gray-500">
          <Link href="/privacy" className="hover:text-gray-700">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-gray-700 font-medium text-gray-900">Terms of Service</Link>
        </div>
      </div>
    </div>
  );
}
