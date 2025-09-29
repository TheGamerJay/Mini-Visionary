// BLOCK 0 — utilities, theme, brand, topbar, layout, shared ui

// ——— Utilities
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

function fmt(value) {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(value);
}

// ——— Theme / Nav
const navItems = [
  { to: '/static/guide.html', label: 'Guide' },
  { to: '/static/gallery.html', label: 'Gallery' },
  { to: '/static/library.html', label: 'Library' },
  { to: '/static/store.html', label: '💎 Store' },
  { to: '/static/wallet.html', label: '💰 Wallet' },
  { to: '/static/profile.html', label: '🧑 Profile' }
];

// ——— Get user credits
function getUserCredits() {
  try {
    const token = localStorage.getItem('jwt_token');
    if (!token) return 0;

    // Try to get from cached user data
    const cached = localStorage.getItem('cached_user_data');
    if (cached) {
      const data = JSON.parse(cached);
      return data.credits || 0;
    }

    // Default fallback
    return 120;
  } catch (e) {
    return 120;
  }
}

// ——— Render topbar
function renderTopbar() {
  const currentPath = window.location.pathname;
  const credits = getUserCredits();

  return `
    <header class="mv-topbar">
      <div class="mv-topbar-container">
        <a href="/static/generate.html" class="mv-brand">
          <div class="mv-brand-icon"></div>
          <span class="mv-brand-text">Mini Visionary</span>
        </a>
        <nav class="mv-nav">
          ${navItems.map(item => {
            const isActive = currentPath === item.to || currentPath.endsWith(item.to);
            return `<a href="${item.to}" class="mv-nav-link ${isActive ? 'active' : ''}">${item.label}</a>`;
          }).join('')}
        </nav>
        <div class="mv-topbar-actions">
          <button class="mv-credits-btn" onclick="window.location.href='/static/wallet.html'">Credits: ${credits}</button>
          <button class="mv-logout-btn" onclick="logout()">Log out</button>
        </div>
      </div>
    </header>
  `;
}

// ——— Render footer
function renderFooter() {
  return `
    <footer class="mv-footer">
      © ${new Date().getFullYear()} Mini Visionary — All rights reserved.
    </footer>
  `;
}

// ——— Logout function
function logout() {
  localStorage.removeItem('jwt_token');
  localStorage.removeItem('cached_user_data');
  window.location.href = '/auth.html#login';
}

// ——— Initialize shared layout
function initSharedLayout() {
  // Insert topbar at the beginning of body
  const topbar = document.createElement('div');
  topbar.innerHTML = renderTopbar();
  document.body.insertBefore(topbar.firstElementChild, document.body.firstChild);

  // Insert footer at the end of body
  const footer = document.createElement('div');
  footer.innerHTML = renderFooter();
  document.body.appendChild(footer.firstElementChild);
}

// ——— Shared CSS styles
const sharedStyles = `
  /* Topbar */
  .mv-topbar {
    position: sticky;
    top: 0;
    z-index: 40;
    backdrop-filter: blur(12px);
    background: rgba(0, 0, 0, 0.3);
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    -webkit-backdrop-filter: blur(12px);
  }
  .mv-topbar-container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* Brand */
  .mv-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
    color: white;
    user-select: none;
  }
  .mv-brand-icon {
    height: 20px;
    width: 20px;
    border-radius: 12px;
    background: linear-gradient(135deg, #818cf8, #f0abfc, #22d3ee);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
  .mv-brand-text {
    font-weight: 600;
    letter-spacing: 0.025em;
  }

  /* Nav */
  .mv-nav {
    display: none;
    align-items: center;
    gap: 4px;
  }
  @media (min-width: 768px) {
    .mv-nav {
      display: flex;
    }
  }
  .mv-nav-link {
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
    color: rgba(255, 255, 255, 0.7);
    transition: all 0.2s;
  }
  .mv-nav-link:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  .mv-nav-link.active {
    background: rgba(255, 255, 255, 0.1);
    color: white;
  }

  /* Topbar actions */
  .mv-topbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .mv-credits-btn {
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 14px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    cursor: pointer;
    transition: all 0.2s;
  }
  .mv-credits-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }
  .mv-logout-btn {
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 14px;
    background: white;
    color: black;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
    font-weight: 500;
  }
  .mv-logout-btn:hover {
    background: #e5e5e5;
  }

  /* Footer */
  .mv-footer {
    max-width: 1280px;
    margin: 0 auto;
    padding: 48px 16px;
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
  }

  /* Shared utility classes */
  .mv-badge {
    padding: 4px 8px;
    border-radius: 9999px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    font-size: 12px;
  }

  .mv-stat {
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
    padding: 16px;
  }
  .mv-stat-label {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: rgba(255, 255, 255, 0.6);
  }
  .mv-stat-value {
    font-size: 24px;
    font-weight: 700;
    margin-top: 4px;
  }

  .mv-search {
    position: relative;
    width: 100%;
  }
  .mv-search input {
    width: 100%;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 10px 16px;
    outline: none;
    color: white;
  }
  .mv-search input::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  .mv-search input:focus {
    ring: 2px;
    ring-color: #f0abfc;
  }
  .mv-search-icon {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(255, 255, 255, 0.5);
    font-size: 14px;
    pointer-events: none;
  }

  .mv-empty {
    display: grid;
    place-items: center;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.05);
    padding: 40px;
    text-align: center;
  }
  .mv-empty-title {
    font-size: 20px;
    font-weight: 600;
  }
  .mv-empty-hint {
    color: rgba(255, 255, 255, 0.7);
    margin-top: 4px;
  }
  .mv-empty-action {
    margin-top: 16px;
  }
`;