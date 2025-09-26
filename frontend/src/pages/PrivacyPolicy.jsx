import React from "react";
import { Link } from "react-router-dom";

export default function PrivacyPolicy() {
  return (
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Privacy Policy</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          Your privacy is important to us.
        </p>

        <div className="text-sm text-gray-300 space-y-4 max-h-96 overflow-y-auto">
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">1. Information We Collect</h3>
            <p>We collect information you provide directly to us, such as when you create an account, use our services, or contact us for support.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">2. How We Use Your Information</h3>
            <p>We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">3. Information Sharing</h3>
            <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">4. Data Security</h3>
            <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">5. Cookies and Tracking</h3>
            <p>We use cookies and similar technologies to enhance your experience, analyze usage patterns, and provide personalized content.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">6. Third-Party Services</h3>
            <p>Our service may contain links to third-party websites or services. We are not responsible for their privacy practices.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">7. Data Retention</h3>
            <p>We retain your information for as long as necessary to provide our services and fulfill the purposes outlined in this policy.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">8. Your Rights</h3>
            <p>You have the right to access, update, or delete your personal information. Contact us to exercise these rights.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">9. Changes to Privacy Policy</h3>
            <p>We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">10. Contact Us</h3>
            <p>If you have any questions about this Privacy Policy, please contact us through our support channels.</p>
          </div>
        </div>

        <div className="auth-links mt-6">
          <div className="text-sm text-center">
            <Link to="/register" className="link-quiet">Back to Register</Link>
            <span className="mx-2">•</span>
            <Link to="/terms-of-service" className="link-quiet">Terms of Service</Link>
          </div>
        </div>
      </div>

      <div className="site-banner bottom"></div>
      <div className="login-footer">
        <div className="login-tagline">You Envision it, We Generate it.</div>
      </div>
    </div>
  );
}