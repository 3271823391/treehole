(function () {
  var STYLE_ID = 'admin-console-btn-style';
  var BTN_ID = 'settingsBtn';
  var LEGACY_BTN_ID = 'adminConsoleBtn';
  var allowPaths = ['/', '/treehole', '/home'];

  function removeSettingsButtons() {
    var btn = document.getElementById(BTN_ID);
    if (btn) btn.remove();
    var legacyBtn = document.getElementById(LEGACY_BTN_ID);
    if (legacyBtn) legacyBtn.remove();
  }

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = [
      '.admin-console-btn {',
      '  position: fixed;',
      '  top: max(14px, env(safe-area-inset-top));',
      '  right: max(14px, env(safe-area-inset-right));',
      '  z-index: 9999;',
      '  width: 36px;',
      '  height: 36px;',
      '  border-radius: 999px;',
      '  border: 1px solid rgba(0,0,0,0.08);',
      '  background: rgba(255,255,255,0.92);',
      '  box-shadow: 0 6px 18px rgba(0,0,0,0.10);',
      '  display: flex;',
      '  align-items: center;',
      '  justify-content: center;',
      '  cursor: pointer;',
      '  user-select: none;',
      '  -webkit-tap-highlight-color: transparent;',
      '  text-decoration: none;',
      '  color: #334155;',
      '  font-size: 16px;',
      '}',
      '.admin-console-btn:hover { transform: translateY(-1px); }',
      '.admin-console-btn:active { transform: translateY(0px) scale(0.98); }'
    ].join('\n');
    document.head.appendChild(style);
  }

  function ensureButton() {
    var btn = document.getElementById(BTN_ID) || document.getElementById(LEGACY_BTN_ID);
    if (!btn) {
      btn = document.createElement('a');
      btn.id = BTN_ID;
      btn.href = '/admin/console';
      btn.className = 'admin-console-btn';
      btn.setAttribute('aria-label', '后台控制台');
      btn.setAttribute('title', '后台控制台');
      btn.textContent = '⚙️';
      document.body.appendChild(btn);
    }
    if (btn.id !== BTN_ID) {
      btn.id = BTN_ID;
    }
    if (!btn.classList.contains('admin-console-btn')) {
      btn.classList.add('admin-console-btn');
    }
    return btn;
  }

  function bindClick(btn) {
    if (!btn || btn.dataset.adminConsoleBound === '1') return;
    btn.dataset.adminConsoleBound = '1';
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      window.location.href = '/admin/console';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      if (!allowPaths.includes(window.location.pathname)) {
        removeSettingsButtons();
        return;
      }
      ensureStyle();
      bindClick(ensureButton());
    });
    return;
  }

  if (!allowPaths.includes(window.location.pathname)) {
    removeSettingsButtons();
    return;
  }

  ensureStyle();
  bindClick(ensureButton());
})();
