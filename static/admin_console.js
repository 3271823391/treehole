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
    app.innerHTML = `
      <section class="card"><div class="card-title">用户列表</div><p class="subtext">查看系统中已记录用户和会话概况。</p></section>
      <section class="card"><h2>用户列表 (${data.count || 0})</h2>
      <table class="table"><thead><tr><th>user_id</th><th>昵称</th><th>计划</th><th>聊天数</th><th>关系数</th><th>虚拟IP</th></tr></thead>
      <tbody>${(data.items || []).map((u) => `<tr><td>${u.user_id}</td><td>${u.display_name || '-'}</td><td>${u.plan}</td><td>${u.chat_count}</td><td>${u.relationship_count}</td><td>${u.ip_name || '-'}</td></tr>`).join('')}</tbody></table></section>`;
  }

  function renderUserDetailSelector() {
    app.innerHTML = `
      <section class="card"><div class="card-title">用户详情</div><p class="subtext">输入 user_id 查询完整资料与角色关系。</p></section>
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
      const [user, chars] = await Promise.all([
        getJson(`/api/admin/user/${encodeURIComponent(userId)}`),
        getJson(`/api/admin/user/${encodeURIComponent(userId)}/characters`),
      ]);
      const resultEl = document.getElementById('userDetailResult');
      resultEl.classList.remove('muted');
      resultEl.innerHTML = `
        <div class="card"><strong>${user.user_id}</strong> | ${user.profile.display_name || user.profile.username || '-'} | ${user.plan}
          <pre>${JSON.stringify(user, null, 2)}</pre>
        </div>
        <div class="card"><strong>角色关系 (${chars.count || 0})</strong>
          <pre>${JSON.stringify(chars.items || [], null, 2)}</pre>
        </div>`;
    });
  }

  async function renderRelationship() {
    const data = await getJson('/api/admin/relationship');
    app.innerHTML = `
      <section class="card"><div class="card-title">好感度总览</div><p class="subtext">查看全部用户与角色间的当前亲密度状态。</p></section>
      <section class="card"><h2>好感度总览 (${data.count || 0})</h2>
      <table class="table"><thead><tr><th>user_id</th><th>character_id</th><th>affinity</th><th>streak</th><th>last_eval</th></tr></thead>
      <tbody>${(data.items || []).map((r) => `<tr><td>${r.user_id}</td><td>${r.character_id}</td><td>${r.affinity_score}</td><td>${r.stable_streak}</td><td>${r.last_affinity_eval_at || '-'}</td></tr>`).join('')}</tbody></table></section>`;
  }

  async function renderLogs() {
    app.innerHTML = `
      <section class="card"><div class="card-title">日志</div><p class="subtext">按分类快速筛选后台日志。</p></section>
      <section class="card">
        <h2>日志</h2>
        <div class="row">
          <select id="categorySel"><option value="">全部</option><option value="chat">chat</option><option value="relationship">relationship</option><option value="user">user</option><option value="system">system</option><option value="error">error</option></select>
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
      if (activeView === 'relationship') return await renderRelationship();
      if (activeView === 'logs') return await renderLogs();
    } catch (e) {
      app.innerHTML = `<section class="card">\n          <div class="card-title">加载失败</div>\n          <div class="error">${String(e)}</div>\n        </section>`;
    }
  }

  menuButtons.forEach((btn) => btn.addEventListener('click', () => setActive(btn.dataset.view)));
  render();
})();
