/* ========== SmartPlan SPA - 原生 JS ========== */
(function () {
  'use strict';

  // ========== 状态管理 ==========
  const state = {
    token: localStorage.getItem('smartplan_token') || null,
    user: null,
  };

  // ========== API 封装 ==========
  const API = {
    base: '/api',

    async request(method, path, body) {
      const headers = { 'Content-Type': 'application/json' };
      if (state.token) headers['Authorization'] = 'Bearer ' + state.token;

      const opts = { method, headers };
      if (body) opts.body = JSON.stringify(body);

      const res = await fetch(this.base + path, opts);
      const data = await res.json();
      if (!res.ok && data.message) throw new Error(data.message);
      return data;
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    del(path) { return this.request('DELETE', path); },
  };

  // ========== 路由 ==========
  let currentPage = null;

  function getRoute() {
    const hash = location.hash.slice(1) || '/login';
    const [path, queryStr] = hash.split('?');
    const params = {};
    if (queryStr) {
      queryStr.split('&').forEach(p => {
        const [k, v] = p.split('=');
        params[decodeURIComponent(k)] = decodeURIComponent(v || '');
      });
    }
    return { path, params };
  }

  function navigate(hash) {
    location.hash = hash;
  }

  function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    const el = document.getElementById('page-' + name);
    if (el) el.style.display = '';
    currentPage = name;

    // 高亮导航
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const navEl = document.querySelector(`[data-nav="${name}"]`);
    if (navEl) navEl.classList.add('active');
  }

  function showAuth(showRegister) {
    document.getElementById('app-main').style.display = 'none';
    document.getElementById('page-login').style.display = showRegister ? 'none' : '';
    document.getElementById('page-register').style.display = showRegister ? '' : 'none';
  }

  function showApp() {
    document.getElementById('page-login').style.display = 'none';
    document.getElementById('page-register').style.display = 'none';
    document.getElementById('app-main').style.display = '';
  }

  // ========== 工具函数 ==========
  function formatDate(date) {
    const d = new Date(date);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function todayStr() {
    return formatDate(new Date());
  }

  function getStatusBadge(status) {
    const map = {
      TODO: 'badge-todo',
      IN_PROGRESS: 'badge-progress',
      DONE: 'badge-done',
      UNDONE: 'badge-undone',
      CANCELLED: 'badge-cancelled',
    };
    const labels = {
      TODO: '待办',
      IN_PROGRESS: '进行中',
      DONE: '已完成',
      UNDONE: '未完成',
      CANCELLED: '已取消',
    };
    return `<span class="badge ${map[status] || 'badge-todo'}">${labels[status] || status}</span>`;
  }

  function getQuadrantBadge(q) {
    const map = {
      IMPORTANT_URGENT: 'qb-iu',
      IMPORTANT_NOT_URGENT: 'qb-inu',
      NOT_IMPORTANT_URGENT: 'qb-niu',
      NOT_IMPORTANT_NOT_URGENT: 'qb-ninu',
    };
    const labels = {
      IMPORTANT_URGENT: '重要且紧急',
      IMPORTANT_NOT_URGENT: '重要不紧急',
      NOT_IMPORTANT_URGENT: '不重要紧急',
      NOT_IMPORTANT_NOT_URGENT: '不重要不紧急',
    };
    return `<span class="quadrant-badge ${map[q] || ''}">${labels[q] || q}</span>`;
  }

  function getQuadrantPreview() {
    const imp = document.getElementById('tf-important').checked;
    const urg = document.getElementById('tf-urgent').checked;
    const preview = document.getElementById('quadrant-preview');
    if (imp && urg) preview.textContent = '→ 重要且紧急';
    else if (imp && !urg) preview.textContent = '→ 重要但不紧急';
    else if (!imp && urg) preview.textContent = '→ 不重要但紧急';
    else preview.textContent = '→ 不重要且不紧急';
  }

  function showError(elId, msg) {
    const el = document.getElementById(elId);
    el.textContent = msg;
    el.style.display = '';
  }

  function hideError(elId) {
    document.getElementById(elId).style.display = 'none';
  }

  // ========== 鉴权检查 ==========
  async function checkAuth() {
    if (!state.token) return false;
    try {
      const res = await API.get('/auth/me');
      if (res.success) {
        state.user = res.data;
        return true;
      }
    } catch (e) { /* ignore */ }
    state.token = null;
    localStorage.removeItem('smartplan_token');
    return false;
  }

  // ========== 页面渲染 ==========

  // --- Dashboard ---
  async function renderDashboard() {
    const dateEl = document.getElementById('dash-date');
    if (!dateEl.value) dateEl.value = todayStr();
    const date = dateEl.value;
    const status = document.getElementById('filter-status').value;
    const quadrant = document.getElementById('filter-quadrant').value;

    let query = `?date=${date}`;
    if (status) query += `&status=${status}`;
    if (quadrant) query += `&quadrant=${quadrant}`;

    const res = await API.get('/tasks' + query);
    const tasks = res.data || [];
    const container = document.getElementById('task-list');

    if (tasks.length === 0) {
      container.innerHTML = '<div class="empty-state">暂无任务，点击右上角「新增任务」开始规划今天吧！</div>';
      return;
    }

    container.innerHTML = tasks.map(t => `
      <div class="task-card">
        <div class="task-card-left">
          <div class="task-card-title">${escHtml(t.title)}</div>
          ${t.description ? `<div class="task-card-desc">${escHtml(t.description)}</div>` : ''}
          <div class="task-card-meta">
            ${getStatusBadge(t.status)}
            ${getQuadrantBadge(t.quadrant)}
            ${t.planned_start_time ? `<span>🕐 ${t.planned_start_time}${t.planned_end_time ? ' - ' + t.planned_end_time : ''}</span>` : ''}
          </div>
        </div>
        <div class="task-card-actions">
          <button class="btn btn-sm btn-ghost" onclick="window._spEdit(${t.id})">编辑</button>
          <button class="btn btn-sm btn-ghost" onclick="window._spReview(${t.id})">复盘</button>
          <button class="btn btn-sm btn-ghost" style="color:var(--color-danger)" onclick="window._spDelete(${t.id})">删除</button>
        </div>
      </div>
    `).join('');
  }

  function escHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // --- Task Form ---
  async function renderTaskForm(taskId) {
    document.getElementById('task-form-title').textContent = taskId ? '编辑任务' : '新增任务';
    document.getElementById('tf-id').value = taskId || '';
    document.getElementById('task-form-error').style.display = 'none';

    if (!taskId) {
      document.getElementById('tf-date').value = todayStr();
      return;
    }

    const res = await API.get('/tasks/' + taskId);
    if (!res.success) { alert(res.message); navigate('#/dashboard'); return; }
    const t = res.data;
    document.getElementById('tf-title').value = t.title || '';
    document.getElementById('tf-date').value = t.task_date || '';
    document.getElementById('tf-status').value = t.status || 'TODO';
    document.getElementById('tf-start').value = t.planned_start_time || '';
    document.getElementById('tf-end').value = t.planned_end_time || '';
    document.getElementById('tf-desc').value = t.description || '';
    document.getElementById('tf-s').value = t.smart_specific || '';
    document.getElementById('tf-m').value = t.smart_measurable || '';
    document.getElementById('tf-a').value = t.smart_achievable || '';
    document.getElementById('tf-r').value = t.smart_relevant || '';
    document.getElementById('tf-t').value = t.smart_time_bound || '';
    document.getElementById('tf-important').checked = !!t.important;
    document.getElementById('tf-urgent').checked = !!t.urgent;
    getQuadrantPreview();
  }

  async function handleTaskFormSubmit(e) {
    e.preventDefault();
    hideError('task-form-error');

    const id = document.getElementById('tf-id').value;
    const data = {
      title: document.getElementById('tf-title').value.trim(),
      task_date: document.getElementById('tf-date').value,
      status: document.getElementById('tf-status').value,
      planned_start_time: document.getElementById('tf-start').value || null,
      planned_end_time: document.getElementById('tf-end').value || null,
      description: document.getElementById('tf-desc').value.trim(),
      smart_specific: document.getElementById('tf-s').value.trim(),
      smart_measurable: document.getElementById('tf-m').value.trim(),
      smart_achievable: document.getElementById('tf-a').value.trim(),
      smart_relevant: document.getElementById('tf-r').value.trim(),
      smart_time_bound: document.getElementById('tf-t').value.trim(),
      important: document.getElementById('tf-important').checked,
      urgent: document.getElementById('tf-urgent').checked,
    };

    // 前端校验必填
    if (!data.title) { showError('task-form-error', '请输入任务标题'); return; }
    if (!data.task_date) { showError('task-form-error', '请选择任务日期'); return; }
    if (!data.smart_specific) { showError('task-form-error', '请填写 SMART-Specific'); return; }
    if (!data.smart_measurable) { showError('task-form-error', '请填写 SMART-Measurable'); return; }
    if (!data.smart_time_bound) { showError('task-form-error', '请填写 SMART-TimeBound'); return; }

    try {
      if (id) {
        await API.put('/tasks/' + id, data);
      } else {
        await API.post('/tasks', data);
      }
      navigate('#/dashboard');
    } catch (e) {
      showError('task-form-error', e.message);
    }
  }

  // --- Quadrant ---
  async function renderQuadrant() {
    const dateEl = document.getElementById('quad-date');
    if (!dateEl.value) dateEl.value = todayStr();
    const date = dateEl.value;

    const res = await API.get('/tasks?date=' + date);
    const tasks = res.data || [];

    const quadrants = {
      IMPORTANT_URGENT: { el: 'quad-iu', tasks: [] },
      IMPORTANT_NOT_URGENT: { el: 'quad-inu', tasks: [] },
      NOT_IMPORTANT_URGENT: { el: 'quad-niu', tasks: [] },
      NOT_IMPORTANT_NOT_URGENT: { el: 'quad-ninu', tasks: [] },
    };

    tasks.forEach(t => {
      if (quadrants[t.quadrant]) quadrants[t.quadrant].tasks.push(t);
    });

    Object.values(quadrants).forEach(q => {
      const el = document.getElementById(q.el);
      if (q.tasks.length === 0) {
        el.innerHTML = '<div style="color:#94A3B8;font-size:13px;padding:8px;">暂无任务</div>';
      } else {
        el.innerHTML = q.tasks.map(t => `
          <div class="quadrant-task" onclick="window._spEdit(${t.id})">
            <div class="qt-title">${escHtml(t.title)}</div>
            <div class="qt-meta">${getStatusBadge(t.status)} ${t.planned_start_time || ''}</div>
          </div>
        `).join('');
      }
    });
  }

  // --- Task Review ---
  async function renderTaskReview(taskId) {
    const res = await API.get('/tasks/' + taskId);
    if (!res.success) { alert(res.message); navigate('#/dashboard'); return; }
    const t = res.data;

    document.getElementById('review-task-info').innerHTML = `
      <h3>${escHtml(t.title)}</h3>
      <div class="review-task-summary">
        <p><span class="label-inline">状态：</span>${getStatusBadge(t.status)} ${getQuadrantBadge(t.quadrant)}</p>
        <p><span class="label-inline">计划时间：</span>${t.planned_start_time || '-'} ~ ${t.planned_end_time || '-'}</p>
        <p><span class="label-inline">S：</span>${escHtml(t.smart_specific || '')}</p>
        <p><span class="label-inline">M：</span>${escHtml(t.smart_measurable || '')}</p>
        <p><span class="label-inline">A：</span>${escHtml(t.smart_achievable || '')}</p>
        <p><span class="label-inline">R：</span>${escHtml(t.smart_relevant || '')}</p>
        <p><span class="label-inline">T：</span>${escHtml(t.smart_time_bound || '')}</p>
      </div>
    `;

    // 尝试加载已有复盘
    try {
      const rr = await API.get('/tasks/' + taskId + '/review');
      if (rr.success && rr.data) {
        const r = rr.data;
        document.getElementById('rv-start').value = r.actual_start_time || '';
        document.getElementById('rv-end').value = r.actual_end_time || '';
        document.getElementById('rv-completed').checked = !!r.is_completed;
        document.getElementById('rv-note').value = r.completion_note || '';
        document.getElementById('rv-reason').value = r.unfinished_reason || '';
        document.getElementById('rv-problems').value = r.problems || '';
        document.getElementById('rv-learnings').value = r.learnings || '';
        document.getElementById('rv-improvement').value = r.improvement || '';
        document.getElementById('rv-rating').value = r.self_rating || '';
      }
    } catch (e) { /* ignore */ }
  }

  async function handleReviewSubmit(e) {
    e.preventDefault();
    hideError('review-error');

    const hash = location.hash.slice(1);
    const params = new URLSearchParams(hash.split('?')[1] || '');
    const taskId = params.get('id');
    if (!taskId) return;

    const data = {
      actual_start_time: document.getElementById('rv-start').value || null,
      actual_end_time: document.getElementById('rv-end').value || null,
      is_completed: document.getElementById('rv-completed').checked,
      completion_note: document.getElementById('rv-note').value.trim(),
      unfinished_reason: document.getElementById('rv-reason').value.trim(),
      problems: document.getElementById('rv-problems').value.trim(),
      learnings: document.getElementById('rv-learnings').value.trim(),
      improvement: document.getElementById('rv-improvement').value.trim(),
      self_rating: document.getElementById('rv-rating').value ? parseInt(document.getElementById('rv-rating').value) : null,
    };

    try {
      await API.post('/tasks/' + taskId + '/review', data);
      alert('复盘保存成功！');
      navigate('#/dashboard');
    } catch (e) {
      showError('review-error', e.message);
    }
  }

  // --- Daily Review ---
  async function renderDailyReview() {
    const dateEl = document.getElementById('dr-date');
    if (!dateEl.value) dateEl.value = todayStr();
    const date = dateEl.value;

    // 获取任务统计
    const taskRes = await API.get('/tasks?date=' + date);
    const tasks = taskRes.data || [];

    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'DONE').length;
    const unfinished = tasks.filter(t => t.status === 'UNDONE' || t.status === 'TODO' || t.status === 'IN_PROGRESS').length;
    const cancelled = tasks.filter(t => t.status === 'CANCELLED').length;

    document.getElementById('dr-stats').innerHTML = `
      <div class="stat-card"><div class="stat-num">${total}</div><div class="stat-label">总任务</div></div>
      <div class="stat-card"><div class="stat-num">${completed}</div><div class="stat-label">已完成</div></div>
      <div class="stat-card"><div class="stat-num">${unfinished}</div><div class="stat-label">未完成</div></div>
      <div class="stat-card"><div class="stat-num">${cancelled}</div><div class="stat-label">已取消</div></div>
    `;

    // 任务复盘摘要
    const summaryEl = document.getElementById('dr-reviews-summary');
    const reviewedTasks = [];
    for (const t of tasks) {
      try {
        const rr = await API.get('/tasks/' + t.id + '/review');
        if (rr.success && rr.data) {
          reviewedTasks.push({ task: t, review: rr.data });
        }
      } catch (e) { /* ignore */ }
    }

    if (reviewedTasks.length === 0) {
      summaryEl.innerHTML = '<p style="color:var(--color-text-muted);">暂无任务复盘记录</p>';
    } else {
      summaryEl.innerHTML = reviewedTasks.map(({ task, review }) => `
        <div style="margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--color-border);">
          <strong>${escHtml(task.title)}</strong>
          ${review.is_completed ? ' ✅ 已完成' : ' ❌ 未完成'}
          ${review.self_rating ? ` · 评分: ${review.self_rating}/5` : ''}
          ${review.problems ? `<br><span style="color:var(--color-text-muted);font-size:13px;">问题：${escHtml(review.problems)}</span>` : ''}
          ${review.learnings ? `<br><span style="color:var(--color-accent);font-size:13px;">收获：${escHtml(review.learnings)}</span>` : ''}
        </div>
      `).join('');
    }

    // 尝试加载已有每日复盘
    try {
      const dr = await API.get('/daily-reviews?date=' + date);
      if (dr.success && dr.data && dr.data.ai_summary) {
        document.getElementById('dr-summary-content').style.display = '';
        document.getElementById('dr-summary-content').innerHTML = renderMarkdown(dr.data.ai_summary);
      } else {
        document.getElementById('dr-summary-content').style.display = 'none';
      }
    } catch (e) {
      document.getElementById('dr-summary-content').style.display = 'none';
    }
  }

  async function handleGenerateSummary() {
    const date = document.getElementById('dr-date').value || todayStr();
    const btn = document.getElementById('btn-generate-summary');
    const loading = document.getElementById('dr-generating');
    btn.disabled = true;
    loading.style.display = '';

    try {
      const res = await API.post('/daily-reviews/generate', { date });
      if (res.success) {
        document.getElementById('dr-summary-content').style.display = '';
        document.getElementById('dr-summary-content').innerHTML = renderMarkdown(res.data.summary);
      }
    } catch (e) {
      alert('生成失败：' + e.message);
    } finally {
      btn.disabled = false;
      loading.style.display = 'none';
    }
  }

  function renderMarkdown(md) {
    // 简单 Markdown 渲染
    let html = escHtml(md);
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    // 处理连续 li
    html = html.replace(/<\/li>\s*<li>/g, '</li><li>');
    html = html.replace(/((?:<li>.*?<\/li>\s*)+)/g, '<ul>$1</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');
    html = html.replace(/\n\n/g, '<br><br>');
    html = html.replace(/\n/g, '<br>');
    return html;
  }

  // --- Profile ---
  async function renderProfile() {
    if (state.user) {
      document.getElementById('prof-username').textContent = state.user.username;
      document.getElementById('prof-email').textContent = state.user.email;
    }
  }

  // ========== 路由调度 ==========
  async function handleRoute() {
    const { path, params } = getRoute();

    // 未登录只能访问 auth 页面
    if (!state.token && path !== '/login' && path !== '/register') {
      navigate('#/login');
      return;
    }

    // 已登录从 auth 页面重定向
    if (state.token && (path === '/login' || path === '/register')) {
      navigate('#/dashboard');
      return;
    }

    // 验证 token
    if (state.token && !state.user) {
      const ok = await checkAuth();
      if (!ok) {
        navigate('#/login');
        return;
      }
    }

    switch (path) {
      case '/login':
        showAuth(false);
        break;
      case '/register':
        showAuth(true);
        break;
      case '/dashboard':
        showApp(); showPage('dashboard'); await renderDashboard();
        break;
      case '/task-form':
        showApp(); showPage('task-form'); await renderTaskForm(params.id);
        break;
      case '/quadrant':
        showApp(); showPage('quadrant'); await renderQuadrant();
        break;
      case '/task-review':
        if (!params.id) { navigate('#/dashboard'); return; }
        showApp(); showPage('task-review'); await renderTaskReview(params.id);
        break;
      case '/daily-review':
        showApp(); showPage('daily-review'); await renderDailyReview();
        break;
      case '/profile':
        showApp(); showPage('profile'); await renderProfile();
        break;
      default:
        navigate('#/dashboard');
    }
  }

  // ========== 事件绑定 ==========

  // 登录表单
  document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    hideError('login-error');
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    try {
      const res = await API.post('/auth/login', { email, password });
      if (res.success) {
        state.token = res.data.token;
        state.user = res.data.user;
        localStorage.setItem('smartplan_token', state.token);
        navigate('#/dashboard');
      } else {
        showError('login-error', res.message);
      }
    } catch (e) {
      showError('login-error', e.message);
    }
  });

  // 注册表单
  document.getElementById('register-form').addEventListener('submit', async function (e) {
    e.preventDefault();
    hideError('register-error');
    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const password2 = document.getElementById('reg-password2').value;

    if (password !== password2) {
      showError('register-error', '两次密码输入不一致');
      return;
    }
    if (password.length < 6) {
      showError('register-error', '密码长度不能少于 6 位');
      return;
    }

    try {
      const res = await API.post('/auth/register', { username, email, password });
      if (res.success) {
        alert('注册成功！请登录');
        navigate('#/login');
      } else {
        showError('register-error', res.message);
      }
    } catch (e) {
      showError('register-error', e.message);
    }
  });

  // 任务表单
  document.getElementById('task-form').addEventListener('submit', handleTaskFormSubmit);

  // 四象限预览
  document.getElementById('tf-important').addEventListener('change', getQuadrantPreview);
  document.getElementById('tf-urgent').addEventListener('change', getQuadrantPreview);

  // 复盘表单
  document.getElementById('review-form').addEventListener('submit', handleReviewSubmit);

  // Dashboard 筛选
  document.getElementById('dash-date').addEventListener('change', renderDashboard);
  document.getElementById('filter-status').addEventListener('change', renderDashboard);
  document.getElementById('filter-quadrant').addEventListener('change', renderDashboard);

  // 四象限日期
  document.getElementById('quad-date').addEventListener('change', renderQuadrant);

  // 每日复盘日期
  document.getElementById('dr-date').addEventListener('change', renderDailyReview);

  // 生成小结按钮
  document.getElementById('btn-generate-summary').addEventListener('click', handleGenerateSummary);

  // 新增任务按钮
  document.getElementById('btn-new-task').addEventListener('click', function () {
    navigate('#/task-form');
  });

  // 退出登录
  document.getElementById('btn-logout').addEventListener('click', function () {
    localStorage.removeItem('smartplan_token');
    state.token = null;
    state.user = null;
    navigate('#/login');
  });

  // Hash 变化监听
  window.addEventListener('hashchange', handleRoute);

  // 全局方法暴露（用于动态按钮）
  window._spEdit = function (id) { navigate('#/task-form?id=' + id); };
  window._spReview = function (id) { navigate('#/task-review?id=' + id); };
  window._spDelete = async function (id) {
    if (!confirm('确定要删除这个任务吗？相关复盘也会一并删除。')) return;
    try {
      await API.del('/tasks/' + id);
      handleRoute();
    } catch (e) {
      alert('删除失败：' + e.message);
    }
  };

  // ========== 启动 ==========
  handleRoute();
})();
