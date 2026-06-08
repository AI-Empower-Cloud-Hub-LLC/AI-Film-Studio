'use client'

import Link from 'next/link'
import Sidebar from '../components/Sidebar'

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:via-gray-900 dark:to-black">
      <Sidebar />
      <div className="pl-0 lg:pl-64">
        <div className="max-w-3xl mx-auto px-4 sm:px-8 py-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2">Privacy Policy</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-8">Last updated: May 2026</p>

          <div className="prose prose-gray dark:prose-invert max-w-none space-y-6 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">1. Information We Collect</h2>
              <p><strong>Account Information:</strong> Email address, username, full name, and password (stored as a bcrypt hash).</p>
              <p><strong>Usage Data:</strong> Project prompts, generated content, uploaded files, and interaction logs used to provide and improve the Service.</p>
              <p><strong>Technical Data:</strong> IP addresses, browser type, and device information for security and analytics purposes.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">2. How We Use Your Information</h2>
              <ul className="list-disc pl-5 space-y-1">
                <li>To provide and maintain the AI Film Studio service</li>
                <li>To authenticate your account and protect against unauthorized access</li>
                <li>To process your prompts and generate film content</li>
                <li>To send service-related communications (email verification, password resets)</li>
                <li>To monitor and improve service quality</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">3. Data Storage and Security</h2>
              <p>Your data is stored securely using industry-standard encryption. Passwords are hashed using bcrypt. File uploads are stored server-side with access controls. We use HTTPS for all data transmission.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">4. Third-Party Services</h2>
              <p>We use third-party AI services (Claude, Google AI, ElevenLabs, Runway) to generate content. Your prompts may be processed by these services under their respective privacy policies. We do not share your personal account information with these providers.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">5. Data Retention</h2>
              <p>Your account data is retained as long as your account is active. Project data and generated content are retained until you delete them. You may delete your projects at any time through the application.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">6. Your Rights</h2>
              <ul className="list-disc pl-5 space-y-1">
                <li>Access and download your personal data</li>
                <li>Update or correct your account information</li>
                <li>Delete your projects and uploaded files</li>
                <li>Request account deletion by contacting support</li>
              </ul>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">7. Cookies</h2>
              <p>We use localStorage for authentication tokens and user preferences (theme setting, notification history). No third-party tracking cookies are used.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">8. Changes to This Policy</h2>
              <p>We may update this Privacy Policy periodically. We will notify users of significant changes through the application.</p>
            </section>

            <section>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">9. Contact</h2>
              <p>For privacy-related inquiries, contact us at privacy@aifilmstudio.com.</p>
            </section>
          </div>

          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <Link href="/terms" className="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-500">
              View Terms of Service &rarr;
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
