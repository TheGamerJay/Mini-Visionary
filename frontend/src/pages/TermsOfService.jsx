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
          <div className="text-center mb-4">
            <p className="text-gray-400 italic">Last Updated: September 2025</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">1. Acceptance of Terms</h3>
            <p>By accessing or using Mini Visionary, you agree to be bound by these Terms. If you do not agree, do not use the Service.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">2. Service Description</h3>
            <p>Mini Visionary is an AI-powered poster generation platform that allows users to create custom posters and visual content.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">3. User Accounts</h3>
            <p>You must register for an account to access certain features. You are responsible for maintaining the confidentiality of your login credentials.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">4. Content Usage</h3>
            <p>You retain all rights to the content you create. By using Mini Visionary, you grant us a limited, non-exclusive, worldwide, royalty-free license to host, display, and use your content solely to operate and improve the Service.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">5. Prohibited Uses</h3>
            <p>You may not use the Service for illegal activity, harassment, spam, or harmful/inappropriate content.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">6. Service Availability</h3>
            <p>We strive to maintain availability but do not guarantee uninterrupted access. Scheduled maintenance or downtime may occur.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">7. Limitation of Liability</h3>
            <p>Mini Visionary is provided "as is." We are not liable for indirect, incidental, special, consequential, or punitive damages.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">8. Changes to Terms</h3>
            <p>We may update these Terms from time to time. Users will be notified of significant changes.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">9. Privacy</h3>
            <p>Use of the Service is also subject to our <Link to="/privacy-policy" className="text-indigo-300 hover:text-indigo-200 underline">Privacy Policy</Link>.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">10. Contact Information</h3>
            <p>For questions, please reach out through our support channels. Our email for support is <a href="mailto:MiniVisionary.contactus@gmail.com" className="text-indigo-300 hover:text-indigo-200 underline">MiniVisionary.contactus@gmail.com</a>.</p>
          </div>
        </div>

        <div className="auth-links mt-6">
          <div className="text-sm text-center">
            <Link to="/register" className="link-quiet">Back to Register</Link>
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