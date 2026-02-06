(function () {
  if (window.__adminConsoleLoggerInstalled) return;
  window.__adminConsoleLoggerInstalled = true;

  const endpoint = '/api/client_log';
  const queue = [];
  const blockedKeywords = ['zybtrackerstatisticsaction', 'chrome.devtools', 'favicon'];
  const sensitiveKeywords = ['prompt', 'system prompt', 'chat_history', 'messages', 'content'];
  const original = {
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console)
  };

  function safeStringify(value) {
    if (typeof value === 'string') return value;
    try {
      return JSON.stringify(value);
    } catch (e) {
      return String(value);
    }
  }

  function sanitizeMessage(message) {
    const msg = String(message || '');
    const lower = msg.toLowerCase();
    if (blockedKeywords.some((k) => lower.includes(k))) return '';
    if (sensitiveKeywords.some((k) => lower.includes(k))) return '[redacted-sensitive-log]';
    return msg.slice(0, 600);
  }

  function push(level, args, extra) {
    const joined = args.map((v) => safeStringify(v)).join(' ');
    const message = sanitizeMessage(joined);
    if (!message) return;

    queue.push({
      level,
      message,
      page: location.pathname,
      user_id: window.user_id || null,
      character_id: window.character_id || null,
      extra: extra || {}
    });
  }

  ['log', 'info', 'warn', 'error'].forEach((level) => {
    console[level] = function (...args) {
      push(level, args);
      original[level](...args);
    };
  });

  window.addEventListener('error', function (event) {
    push('error', [event.message || 'window.onerror'], {
      file: event.filename,
      line: event.lineno,
      col: event.colno
    });
  });

  window.addEventListener('unhandledrejection', function (event) {
    const reason = event.reason && (event.reason.message || safeStringify(event.reason));
    push('error', ['unhandledrejection', reason || 'unknown']);
  });

  async function flush() {
    if (!queue.length) return;
    const batch = queue.splice(0, queue.length);
    for (const item of batch) {
      try {
        await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(item),
          keepalive: true
        });
      } catch (e) {
        // ignore
      }
    }
  }

  setInterval(flush, 500);
})();
