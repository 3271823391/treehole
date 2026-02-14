(() => {
  const app = document.getElementById('app');
  const menuButtons = Array.from(document.querySelectorAll('.nav-btn'));
  let activeView = 'users';

  function setActive(view) {
    activeView = view;
    menuButtons.forEach((btn) => btn.classList.toggle('active', btn.dataset.view === view));
    render();
  }

  async function getJson(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`request failed: ${resp.status}`);
    return resp.json();
  }

  async function renderUsers() {
    const data = await getJson('/api/admin/users');
    const users = data.items || [];
    const userCount = data.count || users.length;
    const today = new Date().toISOString().slice(0, 10);
    const todayActive = users.filter((u) => String(u.last_active_at || u.updated_at || '').startsWith(today)).length;
    const chat7d = users.reduce((sum, u) => sum + Number(u.chat_count || 0), 0);

    app.innerHTML = `
      <section class="card"><div class="card-title">用户列表</div><p class="subtext">查看系统中已记录用户和会话概况。</p></section>
      <section class="kpi-grid">
        <article class="kpi"><div class="label">用户数</div><div class="value">${userCount}</div></article>
        <article class="kpi"><div class="label">今日活跃</div><div class="value">${todayActive}</div></article>
        <article class="kpi"><div class="label">7日聊天数</div><div class="value">${chat7d}</div></article>
      </section>
      <section class="card"><h2>用户列表 (${userCount})</h2>
      <table class="table"><thead><tr><th>user_id</th><th>昵称</th><th>计划</th><th>聊天数</th><th>虚拟IP</th></tr></thead>
      <tbody>${users.map((u) => `<tr><td>${u.user_id}</td><td>${u.display_name || '-'}</td><td>${u.plan}</td><td>${u.chat_count}</td><td>${u.ip_name || '-'}</td></tr>`).join('')}</tbody></table></section>`;
  }

  function renderUserDetailSelector() {
    app.innerHTML = `
      <section class="card"><div class="card-title">用户详情</div><p class="subtext">输入 user_id 查询完整资料。</p></section>
      <section class="card">
        <h2>用户详情</h2>
        <div class="row">
          <input id="userIdInput" placeholder="输入 user_id" />
          <button id="loadUserBtn">查询</button>
        </div>
        <div id="userDetailResult" class="muted">请输入 user_id 后查询。</div>
      </section>`;

    document.getElementById('loadUserBtn').addEventListener('click', async () => {
      const userId = document.getElementById('userIdInput').value.trim();
      if (!userId) return;
      const user = await getJson(`/api/admin/user/${encodeURIComponent(userId)}`);
      const resultEl = document.getElementById('userDetailResult');
      resultEl.classList.remove('muted');
      resultEl.innerHTML = `
        <div class="card"><strong>${user.user_id}</strong> | ${user.profile.display_name || user.profile.username || '-'} | ${user.plan}
          <pre>${JSON.stringify(user, null, 2)}</pre>
        </div>`;
    });
  }

  async function renderLogs() {
    app.innerHTML = `
      <section class="card"><div class="card-title">日志</div><p class="subtext">按分类快速筛选后台日志。</p></section>
      <section class="card">
        <h2>日志</h2>
        <div class="row">
          <select id="categorySel"><option value="">全部</option><option value="chat">chat</option><option value="user">user</option><option value="system">system</option><option value="error">error</option></select>
          <button id="refreshLogs">刷新</button>
        </div>
        <div id="logsWrap" class="muted">加载中...</div>
      </section>`;

    const load = async () => {
      const c = document.getElementById('categorySel').value;
      const query = c ? `?category=${encodeURIComponent(c)}` : '';
      const data = await getJson('/api/admin/logs' + query);
      document.getElementById('logsWrap').classList.remove('muted');
      document.getElementById('logsWrap').innerHTML = `<pre>${JSON.stringify(data.items || [], null, 2)}</pre>`;
    };

    document.getElementById('refreshLogs').addEventListener('click', load);
    document.getElementById('categorySel').addEventListener('change', load);
    load();
  }

  async function render() {
    try {
      if (activeView === 'users') return await renderUsers();
      if (activeView === 'user-detail') return renderUserDetailSelector();
      if (activeView === 'logs') return await renderLogs();
    } catch (e) {
      app.innerHTML = `<section class="card">
          <div class="card-title">加载失败</div>
          <div class="error">${String(e)}</div>
        </section>`;
    }
  }

  menuButtons.forEach((btn) => btn.addEventListener('click', () => setActive(btn.dataset.view)));
  render();
})();
