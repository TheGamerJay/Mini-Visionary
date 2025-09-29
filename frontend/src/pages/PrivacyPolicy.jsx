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
            <h3 className="text-lg font-semibold text-white mb-2">Information We Collect</h3>
            <p>We may collect:</p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Account details you provide when creating an account (name, email, password)</li>
              <li>Content you generate through our platform</li>
              <li>Technical data such as device info, usage logs, and cookies</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">How We Use Your Information</h3>
            <p>We use collected data to:</p>
            <ul className="list-disc list-inside ml-4 space-y-1">
              <li>Operate and improve our services</li>
              <li>Process transactions and provide support</li>
              <li>Personalize your experience and deliver updates</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Information Sharing</h3>
            <p>We do not sell or rent your personal information. We may share limited data only with trusted providers for service operation, or as required by law.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Data Security</h3>
            <p>We apply reasonable safeguards to protect your personal information. However, no system can be guaranteed 100% secure.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Cookies and Tracking</h3>
            <p>Cookies and similar tools are used to remember preferences, analyze usage, and improve your experience.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Third-Party Links</h3>
            <p>Our platform may link to external sites. We are not responsible for the privacy practices of third parties.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Data Retention</h3>
            <p>We keep your data only as long as needed for the purposes in this policy, or as required by law.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Your Rights</h3>
            <p>You may request to access, update, or delete your information at any time. Please contact us to exercise these rights.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Changes to This Policy</h3>
            <p>We may revise this Privacy Policy from time to time. Updates will be posted here, with significant changes communicated directly.</p>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Contact Information</h3>
            <p>If you have questions or requests, please reach us through our official support channels. Our email for support is <a href="mailto:MiniVisionary.contactus@gmail.com" className="text-indigo-300 hover:text-indigo-200 underline">MiniVisionary.contactus@gmail.com</a>.</p>
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