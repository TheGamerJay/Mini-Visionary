import React from "react";
import { Link } from "react-router-dom";

export default function TermsOfService() {
  return (
    <div id="login-root">
      <div className="login-header">MINI VISIONARY</div>

      <div className="site-banner top"></div>

      <div className="login-card">
        <h2 className="login-title">Terms of Service</h2>
        <div className="login-logo">
          <img src="/logo.png" alt="Mini Visionary" />
        </div>
        <p className="login-subtitle">
          Please read our Terms of Service carefully.
        </p>

        <div className="text-sm text-gray-300 space-y-4 max-h-96 overflow-y-auto">
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">1. Acceptance of Terms</h3>
            <p>By accessing and using Mini Visionary, you accept and agree to be bound by the terms and provision of this agreement.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">2. Service Description</h3>
            <p>Mini Visionary is an AI-powered poster generation platform that allows users to create custom posters and visual content.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">3. User Accounts</h3>
            <p>Users must register for an account to access certain features. You are responsible for maintaining the confidentiality of your account credentials.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">4. Content Usage</h3>
            <p>You retain ownership of content you create using our platform. However, you grant us a license to use, modify, and display your content for service operation purposes.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">5. Prohibited Uses</h3>
            <p>Users may not use the service for illegal activities, harassment, spam, or creation of harmful or inappropriate content.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">6. Service Availability</h3>
            <p>We strive to maintain service availability but do not guarantee uninterrupted access. Scheduled maintenance may occur.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">7. Limitation of Liability</h3>
            <p>Mini Visionary shall not be liable for any indirect, incidental, special, consequential, or punitive damages.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">8. Changes to Terms</h3>
            <p>We reserve the right to modify these terms at any time. Users will be notified of significant changes.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">9. Contact Information</h3>
            <p>For questions about these Terms of Service, please contact us through our support channels.</p>
          </div>
        </div>

        <div className="auth-links mt-6">
          <div className="text-sm text-center">
            <Link to="/register" className="link-quiet">Back to Register</Link>
            <span className="mx-2">•</span>
            <Link to="/privacy-policy" className="link-quiet">Privacy Policy</Link>
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