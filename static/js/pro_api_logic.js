(function (global) {
  const USER_ID_UUID_PATTERN = /^u_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const USER_ID_SHA1_PATTERN = /^u_[0-9a-f]{40}$/i;

  function isValidUserId(userId) {
    return typeof userId === 'string' && (USER_ID_UUID_PATTERN.test(userId) || USER_ID_SHA1_PATTERN.test(userId));
  }

  function safeLocalStorageGet(key) {
    try {
      return localStorage.getItem(key);
    } catch (e) {
      return '';
    }
  }

  function getToken() {
    const candidates = [
      safeLocalStorageGet('token'),
      safeLocalStorageGet('auth_token'),
      safeLocalStorageGet('treehole_token')
    ];
    return candidates.find((item) => typeof item === 'string' && item.trim()) || '';
  }

  async function fetchJson(url, options = {}) {
    let res;
    try {
      res = await fetch(url, options);
    } catch (e) {
      return { ok: false, msg: '网络异常，请稍后再试', status: 0 };
    }
    const contentType = res.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      const text = await res.text();
      return { ok: false, msg: '服务暂不可用', status: res.status, raw: text, nonJson: true };
    }
    try {
      const data = await res.json();
      if (!res.ok) {
        return { ok: false, msg: data?.msg || '服务暂不可用', status: res.status, raw: data };
      }
      return data;
    } catch (e) {
      return { ok: false, msg: '服务暂不可用', status: res.status };
    }
  }

  async function fetchProfile() {
    const res = await fetch('/profile', { credentials: 'include' });
    const data = await res.json();
    if (!data.ok) return null;
    return data.profile;
  }

  async function getUserContext() {
    const profile = await fetchProfile();
    const user_id = (profile?.user_id || '').trim();
    return {
      user_id,
      token: (profile?.token || getToken() || '').trim(),
      profile: profile || null,
      isValidUserId: isValidUserId(user_id)
    };
  }

  async function parseErrorMessage(res) {
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        const data = await res.json();
        return data?.msg || '服务暂不可用';
      } catch (e) {
        return '服务暂不可用';
      }
    }
    try {
      const text = await res.text();
      if (text) {
        return text.length > 160 ? `${text.slice(0, 160)}...` : text;
      }
    } catch (e) {
      // ignore
    }
    return '服务暂不可用';
  }

  async function parseErrorPayload(res) {
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        const data = await res.json();
        return { msg: data?.msg || '服务暂不可用', detail: data?.detail };
      } catch (e) {
        return { msg: '服务暂不可用', detail: null };
      }
    }
    try {
      const text = await res.text();
      if (text) {
        return { msg: text.length > 160 ? `${text.slice(0, 160)}...` : text, detail: null };
      }
    } catch (e) {
      // ignore
    }
    return { msg: '服务暂不可用', detail: null };
  }

  async function safeParseEmotionResponse(res) {
    const contentType = res.headers.get('content-type') || '';
    const cloned = res.clone();
    if (!res.ok) {
      return null;
    }
    if (!contentType.includes('application/json')) {
      return null;
    }
    try {
      return await res.json();
    } catch (e) {
      try {
        await cloned.text();
      } catch (_) {
        // ignore
      }
      return null;
    }
  }

  async function sendMessageAPI({ userId, history = [], userInput, roundId, signal, onChunk }) {
    if (!isValidUserId(userId)) {
      return { ok: false, msg: '身份失效，请重新登录', code: 'user_id_invalid' };
    }
    const resp = await fetch('/chat_stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        history,
        user_input: userInput,
        round_id: roundId
      }),
      signal
    });

    const contentType = resp.headers.get('content-type') || '';
    if (!resp.ok || contentType.includes('application/json') || contentType.includes('text/html')) {
      const errMsg = await parseErrorMessage(resp);
      return { ok: false, msg: errMsg, code: 'http_error' };
    }
    if (!resp.body) {
      return { ok: false, msg: '服务暂不可用', code: 'empty_stream' };
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let fullText = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunkText = decoder.decode(value);
      fullText += chunkText;
      if (typeof onChunk === 'function') {
        onChunk(chunkText, fullText);
      }
    }
    return { ok: true, text: fullText };
  }

  async function analyzeEmotionAPI({ userId, history = [], currentInput, roundId, signal }) {
    if (!isValidUserId(userId)) {
      return { ok: false, msg: '身份失效，请重新登录', code: 'user_id_invalid' };
    }
    const res = await fetch('/api/emotion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        history,
        current_input: currentInput,
        round_id: roundId
      }),
      signal
    });

    const payload = await safeParseEmotionResponse(res);
    if (!payload || !payload.ok || !payload.data) {
      return { ok: false, msg: '情绪分析暂不可用', code: 'emotion_unavailable' };
    }
    return { ok: true, data: payload.data };
  }

  function voiceCloneAPI(formData) {
    return fetchJson('/api/voice_clone/reference/upload', {
      method: 'POST',
      body: formData
    });
  }

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function voiceCloneTtsAPI({ userId, text, ext = {}, speed, signal, pollTimeoutMs = 60000 }) {
    if (!isValidUserId(userId)) {
      throw new Error('user_id_invalid');
    }

    const createPayload = {
      user_id: userId,
      text,
      ext: ext || {}
    };
    if (Number.isFinite(speed)) {
      createPayload.speed = speed;
    }

    const createRes = await fetch('/api/voice_clone/tts/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(createPayload),
      signal
    });
    if (!createRes.ok) {
      const msg = await parseErrorMessage(createRes);
      throw new Error(msg || '语音合成失败');
    }

    const createData = await createRes.json();
    if (!createData.ok || !createData.taskId) {
      throw new Error(createData.msg || '语音合成失败');
    }

    const taskId = createData.taskId;
    const start = Date.now();
    let voiceUrl = '';
    let waitMs = 400;

    while (Date.now() - start < pollTimeoutMs) {
      const resultRes = await fetch(`/api/voice_clone/tts/result?user_id=${encodeURIComponent(userId)}&taskId=${encodeURIComponent(taskId)}`, {
        method: 'GET',
        signal
      });
      if (!resultRes.ok) {
        const msg = await parseErrorMessage(resultRes);
        throw new Error(msg || '语音合成失败');
      }
      const resultPayload = await resultRes.json();
      if (!resultPayload.ok) {
        throw new Error(resultPayload.msg || '语音合成失败');
      }
      if (resultPayload.status === 1) {
        await sleep(waitMs);
        waitMs = Math.min(waitMs + 200, 1000);
        continue;
      }
      if (resultPayload.status === 2 && resultPayload.voiceUrl) {
        voiceUrl = resultPayload.voiceUrl;
        break;
      }
      if (resultPayload.status === 3) {
        throw new Error('语音合成失败');
      }
    }

    if (!voiceUrl) {
      throw new Error('生成较慢，可稍后重试');
    }

    const audioRes = await fetch(`/api/voice_clone/tts/audio?voiceUrl=${encodeURIComponent(voiceUrl)}`, {
      method: 'GET',
      signal
    });
    if (!audioRes.ok) {
      const msg = await parseErrorMessage(audioRes);
      throw new Error(msg || '语音合成失败');
    }
    const contentType = audioRes.headers.get('content-type') || '';
    if (!contentType.startsWith('audio/') && contentType !== 'application/octet-stream') {
      const { msg } = await parseErrorPayload(audioRes);
      const err = new Error(msg || '语音合成失败');
      err.name = 'TtsNonAudioError';
      throw err;
    }

    return audioRes;
  }

  global.ProApiLogic = {
    isValidUserId,
    safeLocalStorageGet,
    getToken,
    fetchJson,
    fetchProfile,
    getUserContext,
    parseErrorMessage,
    parseErrorPayload,
    safeParseEmotionResponse,
    sendMessageAPI,
    analyzeEmotionAPI,
    voiceCloneAPI,
    voiceCloneTtsAPI
  };
})(window);
