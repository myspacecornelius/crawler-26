import Link from 'next/link';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/" className="text-sm text-gray-500 hover:text-gray-700 mb-8 inline-block">&larr; Back to LeadFactory</Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-500 mb-10">Last updated: February 22, 2026</p>

        <div className="prose prose-gray max-w-none space-y-6 text-gray-700 text-sm leading-relaxed">
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">1. Introduction</h2>
            <p>
              LeadFactory (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) respects your privacy. This Privacy Policy
              explains how we collect, use, and protect personal information when you use our lead
              generation platform (&quot;Service&quot;).
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">2. Information We Collect</h2>
            <p><strong>Account Information:</strong> When you register, we collect your name, email address, company name, and payment information (processed by Stripe).</p>
            <p className="mt-2"><strong>Lead Data:</strong> We collect publicly available professional contact information from fund websites, including names, email addresses, job titles, and LinkedIn profiles.</p>
            <p className="mt-2"><strong>Usage Data:</strong> We collect information about how you use the Service, including pages visited, searches performed, and campaigns run.</p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">3. How We Use Information</h2>
            <ul className="list-disc pl-6 space-y-1">
              <li>To provide, maintain, and improve the Service</li>
              <li>To process payments and manage billing</li>
              <li>To send transactional emails (account confirmation, billing receipts)</li>
              <li>To enforce our Terms of Service</li>
              <li>To comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">4. Legal Basis for Processing (GDPR)</h2>
            <p>We process personal data under the following legal bases:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li><strong>Contract:</strong> Processing necessary to provide the Service you subscribed to</li>
              <li><strong>Legitimate Interest:</strong> Processing publicly available professional data for B2B lead generation</li>
              <li><strong>Consent:</strong> Where explicitly provided</li>
              <li><strong>Legal Obligation:</strong> Where required by law</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">5. Data Subject Rights (GDPR / CCPA)</h2>
            <p>If you are a data subject whose information appears in our lead database, you have the right to:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li><strong>Access:</strong> Request a copy of the data we hold about you</li>
              <li><strong>Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong>Erasure:</strong> Request deletion of your data (&quot;right to be forgotten&quot;)</li>
              <li><strong>Opt-Out:</strong> Opt out of our database at any time via our public opt-out endpoint</li>
              <li><strong>Portability:</strong> Request your data in a machine-readable format</li>
            </ul>
            <p className="mt-3">
              <strong>To exercise your rights:</strong> Use our self-service opt-out at{' '}
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">GET /api/leads/optout?email=your@email.com</code>{' '}
              or email us at{' '}
              <a href="mailto:privacy@leadfactory.io" className="text-blue-600 hover:underline">privacy@leadfactory.io</a>.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">6. Data Sharing</h2>
            <p>We do not sell personal data. We share data only with:</p>
            <ul className="list-disc pl-6 mt-2 space-y-1">
              <li><strong>Stripe:</strong> For payment processing</li>
              <li><strong>Infrastructure providers:</strong> For hosting and data storage</li>
              <li><strong>Law enforcement:</strong> When required by law or valid legal process</li>
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">7. Data Retention</h2>
            <p>
              Account data is retained while your account is active and for 30 days after deletion.
              Lead data for opted-out individuals is anonymized within 30 days of the opt-out request.
              Payment records are retained as required by tax and accounting regulations.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">8. Security</h2>
            <p>
              We implement industry-standard security measures including encryption in transit (TLS),
              encryption at rest, access controls, and regular security reviews. However, no system is
              100% secure, and we cannot guarantee absolute security.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">9. Cookies</h2>
            <p>
              We use essential cookies for authentication and session management. We do not use
              third-party tracking cookies. You can control cookie settings through your browser.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">10. International Transfers</h2>
            <p>
              Data may be processed in the United States or other countries where our infrastructure
              providers operate. We ensure appropriate safeguards are in place for cross-border transfers
              in compliance with GDPR requirements.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">11. Changes to This Policy</h2>
            <p>
              We may update this Privacy Policy periodically. We will notify registered users of material
              changes via email. Continued use of the Service after changes constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-lg font-semibold text-gray-900 mt-8 mb-3">12. Contact</h2>
            <p>
              For privacy inquiries or data subject requests, contact us at{' '}
              <a href="mailto:privacy@leadfactory.io" className="text-blue-600 hover:underline">privacy@leadfactory.io</a>.
            </p>
          </section>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200 flex gap-6 text-sm text-gray-500">
          <Link href="/privacy" className="hover:text-gray-700 font-medium text-gray-900">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-gray-700">Terms of Service</Link>
        </div>
      </div>
    </div>
  );
}
