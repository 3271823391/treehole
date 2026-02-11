(function () {
    const STORAGE_USERNAME_KEY = "treehole_username";
    const STORAGE_USER_ID_KEY = "treehole_user_id";
    const STORAGE_AVATAR_KEY = "treehole_avatar_url";
    const DEFAULT_AVATAR_URL = "/static/avatars/default.svg";
    const USER_ID_UUID_PATTERN = /^u_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    const USER_ID_SHA1_PATTERN = /^u_[0-9a-f]{40}$/i;
    const FAVORABILITY_STATES = [
        { max: 20, cls: "favorability-cold", label: "冷淡 / 抵触" },
        { max: 40, cls: "favorability-distant", label: "疏离" },
        { max: 60, cls: "favorability-normal", label: "普通" },
        { max: 80, cls: "favorability-close", label: "亲近" },
        { max: 100, cls: "favorability-intimate", label: "高度亲密" }
    ];

    let currentAvatarUrl = DEFAULT_AVATAR_URL;
    let currentUserId = "";
    let currentUsername = "";
    let currentBaseUsername = "";
    let currentBaseAvatar = "";
    let toastTimer = null;

    const root = document.getElementById('vip-chat-page');
    if (!root) return;

    const config = {
        characterId: root.dataset.characterId || "unknown",
        characterName: root.dataset.characterName || "角色",
        roleName: root.dataset.roleName || "角色",
        roleAvatar: root.dataset.roleAvatar || "",
        initialMessage: root.dataset.initialMessage || "",
        inputPlaceholder: root.dataset.inputPlaceholder || "请输入消息..."
    };

    function safeLocalStorageGet(key) {
        try {
            return localStorage.getItem(key);
        } catch (e) {
            return "";
        }
    }

    function safeLocalStorageSet(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (e) {
            // ignore
        }
    }

    function isValidUserId(userId) {
        return typeof userId === 'string' && (USER_ID_UUID_PATTERN.test(userId) || USER_ID_SHA1_PATTERN.test(userId));
    }

    function createAnonymousUserId() {
        if (crypto?.randomUUID) {
            return `u_${crypto.randomUUID()}`;
        }
        return `u_${Math.random().toString(16).slice(2)}-${Date.now().toString(16)}`;
    }

    async function sha1Hex(input) {
        const data = new TextEncoder().encode(input);
        const buffer = await crypto.subtle.digest("SHA-1", data);
        return Array.from(new Uint8Array(buffer)).map((b) => b.toString(16).padStart(2, "0")).join("");
    }

    async function makeUserId(username) {
        const norm = (username || "").trim().toLowerCase();
        if (!norm) return "";
        const digest = await sha1Hex(norm);
        return `u_${digest}`;
    }

    function showToast(message) {
        const toast = document.getElementById('toast');
        if (!toast) return;
        toast.innerText = message || "服务暂不可用";
        toast.classList.add('show');
        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
    }

    function setUserIdentity({ username, avatarUrl }) {
        currentUsername = username || "";
        currentAvatarUrl = avatarUrl || DEFAULT_AVATAR_URL;
        const userNameNodes = document.querySelectorAll('[data-user-name]');
        const userAvatarNodes = document.querySelectorAll('[data-user-avatar]');
        userNameNodes.forEach((node) => {
            node.textContent = currentUsername || "用户名";
            node.title = currentUsername || "用户名";
        });
        userAvatarNodes.forEach((node) => {
            if (node.tagName === 'IMG') {
                node.src = currentAvatarUrl;
            } else {
                node.style.backgroundImage = `url('${currentAvatarUrl}')`;
            }
        });
    }

    function applyFavoriteView(score) {
        const clamped = Math.max(0, Math.min(100, Number(score) || 0));
        const state = FAVORABILITY_STATES.find((item) => clamped <= item.max) || FAVORABILITY_STATES[FAVORABILITY_STATES.length - 1];
        const card = document.querySelector('[data-favorability-card]');
        const stateEl = document.querySelector('[data-favorability-state]');
        const fillEl = document.querySelector('[data-favorability-fill]');
        const valueEl = document.querySelector('[data-favorability-value]');
        if (!card || !stateEl || !fillEl || !valueEl) return;
        card.classList.remove(...FAVORABILITY_STATES.map((item) => item.cls));
        card.classList.add(state.cls);
        stateEl.textContent = state.label;
        fillEl.style.width = `${clamped}%`;
        valueEl.textContent = `${clamped} / 100`;
    }

    function loadFavorability() {
        const fallbackId = isValidUserId(currentUserId) ? currentUserId : 'anonymous';
        const favorabilityKey = `favorability:${fallbackId}:${config.characterId}`;
        const stored = safeLocalStorageGet(favorabilityKey);
        const value = stored === null || stored === "" ? 50 : Number(stored);
        applyFavoriteView(Number.isFinite(value) ? value : 50);
    }

    async function resolveCurrentUserIdByUsername(username) {
        const userIdByName = await makeUserId(username);
        if (isValidUserId(userIdByName)) {
            safeLocalStorageSet(STORAGE_USER_ID_KEY, userIdByName);
            return userIdByName;
        }
        return "";
    }

    async function initUserIdentity() {
        const username = (safeLocalStorageGet(STORAGE_USERNAME_KEY) || "").trim();
        let resolvedId = "";
        if (username) {
            resolvedId = await resolveCurrentUserIdByUsername(username);
        }
        if (!resolvedId) {
            const fromParam = new URLSearchParams(window.location.search).get('user_id') || "";
            if (isValidUserId(fromParam)) {
                resolvedId = fromParam;
                safeLocalStorageSet(STORAGE_USER_ID_KEY, resolvedId);
            }
        }
        if (!resolvedId) {
            const fromStorage = safeLocalStorageGet(STORAGE_USER_ID_KEY);
            if (isValidUserId(fromStorage)) {
                resolvedId = fromStorage;
            }
        }
        if (!resolvedId) {
            resolvedId = createAnonymousUserId();
            safeLocalStorageSet(STORAGE_USER_ID_KEY, resolvedId);
        }

        currentUserId = resolvedId;

        setUserIdentity({ username: username, avatarUrl: safeLocalStorageGet(STORAGE_AVATAR_KEY) || DEFAULT_AVATAR_URL });
        await loadProfile();
        loadFavorability();
    }


    async function fetchJson(url, options = {}) {
        const res = await fetch(url, options);
        const contentType = res.headers.get('content-type') || "";
        if (!contentType.includes('application/json')) {
            return { ok: false, msg: '服务暂不可用' };
        }
        try {
            const data = await res.json();
            if (!res.ok) return { ok: false, msg: data?.msg || '服务暂不可用' };
            return data;
        } catch (e) {
            return { ok: false, msg: '服务暂不可用' };
        }
    }

    async function loadProfile() {
        if (!isValidUserId(currentUserId)) return false;
        const data = await fetchJson(`/profile?user_id=${encodeURIComponent(currentUserId)}&character_id=${encodeURIComponent(config.characterId)}`);
        if (!data?.ok) return false;
        const profile = data.profile || {};
        currentBaseUsername = profile.base_username || "";
        currentBaseAvatar = profile.base_avatar || "";
        const localAvatar = safeLocalStorageGet(STORAGE_AVATAR_KEY) || "";
        const mergedAvatar = localAvatar || profile.avatar_url || currentBaseAvatar || DEFAULT_AVATAR_URL;
        setUserIdentity({ username: profile.username || currentBaseUsername, avatarUrl: mergedAvatar });
        const ipInput = document.getElementById('ipDisplayUsername');
        const identityStatus = document.getElementById('identityStatusText');
        if (ipInput) {
            ipInput.value = profile.ip_display_username || "";
            ipInput.placeholder = currentBaseUsername ? `默认：${currentBaseUsername}` : '当前使用 Treehole 用户名';
        }
        if (identityStatus) {
            identityStatus.textContent = profile.ip_display_username
                ? `当前使用角色显示名：${profile.ip_display_username}`
                : '当前使用 Treehole 用户名';
        }
        return true;
    }

    async function persistIpProfile() {
        const ipInput = document.getElementById('ipDisplayUsername');
        if (!ipInput || !isValidUserId(currentUserId)) return;
        const username = ipInput.value.trim();
        const payload = {
            user_id: currentUserId,
            character_id: config.characterId
        };
        if (username) payload.username = username;
        const data = await fetchJson('/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!data?.ok) {
            showToast(data?.msg || '资料保存失败');
            return;
        }
        safeLocalStorageSet(STORAGE_USERNAME_KEY, data.profile?.base_username || username);
        setUserIdentity({ username: data.profile?.username, avatarUrl: data.profile?.avatar_url });
        currentBaseUsername = data.profile?.base_username || "";
        currentBaseAvatar = data.profile?.base_avatar || "";
        showToast('资料已同步到Treehole');
    }


    async function uploadIpAvatar(file) {
        if (!file || !isValidUserId(currentUserId)) return;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', currentUserId);
        formData.append('character_id', config.characterId);
        const data = await fetchJson('/avatar_upload', {
            method: 'POST',
            body: formData
        });
        if (!data?.ok) {
            showToast(data?.msg || '头像上传失败');
            return;
        }
        await loadProfile();
        safeLocalStorageSet(STORAGE_AVATAR_KEY, data.avatar_url || "");
        showToast('头像已同步到Treehole');
    }

    function appendMessageByRole(role, content) {
        if (!content) return;
        if (role === 'user') {
            addUserMessage(content);
            return;
        }
        const contentDiv = addRoleMessageShell();
        contentDiv.textContent = content;
        const chatContent = document.getElementById('chatContent');
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    async function loadChatHistory() {
        if (!isValidUserId(currentUserId)) return;
        const data = await fetchJson(`/load_history?user_id=${encodeURIComponent(currentUserId)}&character_id=${encodeURIComponent(config.characterId)}`);
        if (!data?.ok || !Array.isArray(data.history)) return;
        if (data.history.length > 0) {
            const initialMessage = document.querySelector('#chatContent #initialMessage')?.closest('.message');
            if (initialMessage) initialMessage.remove();
        }
        data.history.forEach((item) => appendMessageByRole(item?.role, item?.content || ''));
    }

    async function parseErrorMessage(res) {
        const contentType = res.headers.get('content-type') || "";
        if (contentType.includes('application/json')) {
            try {
                const data = await res.json();
                return data?.msg || "服务暂不可用";
            } catch (e) {
                return "服务暂不可用";
            }
        }
        return "服务暂不可用";
    }

    function addUserMessage(content) {
        const chatContent = document.getElementById('chatContent');
        const userMessage = document.createElement('div');
        userMessage.className = 'message user-message';
        userMessage.innerHTML = `
            <div class="avatar" data-user-avatar style="background-image: url('${currentAvatarUrl}');"></div>
            <div class="message-content"></div>
        `;
        userMessage.querySelector('.message-content').textContent = content;
        chatContent.appendChild(userMessage);
        chatContent.scrollTop = chatContent.scrollHeight;
    }

    function addRoleMessageShell() {
        const roleMessage = document.createElement('div');
        roleMessage.className = 'message role-message';
        roleMessage.innerHTML = `
            <div class="avatar" style="background-image: url('${config.roleAvatar}');"></div>
            <div class="message-wrapper">
                <div class="role-name">${config.roleName}</div>
                <div class="message-content"></div>
            </div>
        `;
        const chatContent = document.getElementById('chatContent');
        chatContent.appendChild(roleMessage);
        return roleMessage.querySelector('.message-content');
    }

    async function sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const inputText = messageInput.value.trim();
        if (!inputText) return;
        if (!isValidUserId(currentUserId)) {
            showToast("请输入用户名/初始化身份");
            return;
        }

        addUserMessage(inputText);
        messageInput.value = '';

        let contentDiv = null;
        let hasStarted = false;

        try {
            const res = await fetch('/chat_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: currentUserId,
                    user_input: inputText,
                    character_id: config.characterId
                })
            });

            const contentType = res.headers.get('content-type') || "";
            if (!res.ok || contentType.includes('application/json') || contentType.includes('text/html')) {
                showToast(await parseErrorMessage(res));
                return;
            }
            if (!res.body) {
                showToast('服务暂不可用');
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const text = decoder.decode(value, { stream: true });
                if (!text) continue;
                if (!hasStarted) {
                    hasStarted = true;
                    contentDiv = addRoleMessageShell();
                }
                contentDiv.textContent += text;
                const chatContent = document.getElementById('chatContent');
                chatContent.scrollTop = chatContent.scrollHeight;
            }
        } catch (e) {
            showToast('连接失败，请稍后再试');
        }
    }

    function updateDeviceMode() {
        const isMobile = window.innerWidth < 768;
        document.body.classList.toggle('is-mobile', isMobile);
        if (!isMobile) {
            document.body.classList.remove('drawer-open');
        }
    }

    function bindEvents() {
        const sendBtn = document.getElementById('sendBtn');
        const messageInput = document.getElementById('messageInput');
        const backBtn = document.getElementById('backBtn');
        const mobileMenuBtn = document.getElementById('mobileMenuBtn');
        const drawerCloseBtn = document.getElementById('drawerCloseBtn');
        const drawerBackdrop = document.getElementById('drawerBackdrop');
        const syncIpProfileBtn = document.getElementById('syncIpProfileBtn');
        const ipDisplayUsernameInput = document.getElementById('ipDisplayUsername');
        const uploadIpAvatarLink = document.getElementById('uploadIpAvatarLink');
        const ipAvatarInput = document.getElementById('ipAvatarInput');

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
        backBtn.addEventListener('click', () => history.back());

        mobileMenuBtn.addEventListener('click', () => {
            if (window.innerWidth < 768) document.body.classList.add('drawer-open');
        });
        drawerCloseBtn.addEventListener('click', () => document.body.classList.remove('drawer-open'));
        drawerBackdrop.addEventListener('click', () => document.body.classList.remove('drawer-open'));

        if (syncIpProfileBtn) {
            syncIpProfileBtn.addEventListener('click', (e) => {
                e.preventDefault();
                persistIpProfile();
            });
        }
        if (ipDisplayUsernameInput) {
            ipDisplayUsernameInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') persistIpProfile();
            });
        }
        if (uploadIpAvatarLink && ipAvatarInput) {
            uploadIpAvatarLink.addEventListener('click', (e) => {
                e.preventDefault();
                ipAvatarInput.click();
            });
            ipAvatarInput.addEventListener('change', (e) => {
                const file = e.target.files?.[0];
                if (file) uploadIpAvatar(file);
                e.target.value = '';
            });
        }

        window.addEventListener('resize', updateDeviceMode);

        window.addEventListener('storage', (event) => {
            if (event.key === STORAGE_USERNAME_KEY || event.key === STORAGE_AVATAR_KEY) {
                setUserIdentity({
                    username: (safeLocalStorageGet(STORAGE_USERNAME_KEY) || "").trim(),
                    avatarUrl: safeLocalStorageGet(STORAGE_AVATAR_KEY) || currentAvatarUrl || DEFAULT_AVATAR_URL
                });
            }
        });
    }

    function initConfigToDom() {
        document.body.style.backgroundImage = `url('${root.dataset.background}')`;
        document.documentElement.style.setProperty('--vip-accent', root.dataset.accent || '#8eb8e5');
        document.documentElement.style.setProperty('--vip-role-border', root.dataset.roleBorder || root.dataset.accent || '#8eb8e5');
        document.getElementById('chatTitleText').textContent = config.characterName;
        document.getElementById('roleTag').textContent = root.dataset.roleTag || '';
        document.getElementById('roleName').textContent = config.roleName;
        document.getElementById('initialMessage').textContent = config.initialMessage;
        document.getElementById('roleAvatar').style.backgroundImage = `url('${config.roleAvatar}')`;
        document.getElementById('messageInput').placeholder = config.inputPlaceholder;
        document.getElementById('sendBtn').textContent = root.dataset.sendIcon || '✈️';
        document.getElementById('favorabilityTitle').textContent = `${config.characterName} · 好感度`;
    }

    (async function init() {
        initConfigToDom();
        updateDeviceMode();
        bindEvents();
        await initUserIdentity();
        await loadChatHistory();
    })();
})();
