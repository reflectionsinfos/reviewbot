document.addEventListener('DOMContentLoaded', function () {
  var root = document.getElementById('shared-header-root');
  if (!root) return;

  fetch('/frontend_vanilla/components/header.html', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) throw new Error('Failed to load shared header');
      return response.text();
    })
    .then(function (html) {
      if (!root.isConnected) return;
      root.innerHTML = html;

      // Set active nav link for the current page.
      const path = window.location.pathname;
      if (path.includes('/ui') || path.endsWith('/index.html')) {
        document.getElementById('nav-review')?.classList.add('active');
      } else if (path.includes('/projects-ui') || path.includes('/project.html')) {
        document.getElementById('nav-projects')?.classList.add('active');
      } else if (path.includes('/globals') || path.includes('/globals.html')) {
        document.getElementById('nav-globals')?.classList.add('active');
      } else if (path.includes('/system-config') || path.includes('/system_config.html')) {
        document.getElementById('nav-config')?.classList.add('active');
      } else if (path.includes('/documentation') || path.includes('/documentation.html')) {
        document.getElementById('nav-docs')?.classList.add('active');
      }

      window.toggleUserDropdown = function (e) {
        if (e) e.stopPropagation();
        const menu = document.getElementById('shared-user-menu');
        if (menu) menu.classList.toggle('hidden');
      };

      document.addEventListener('click', function (e) {
        const btn = document.querySelector('.user-dropdown-btn');
        const menu = document.getElementById('shared-user-menu');
        if (menu && !menu.classList.contains('hidden')) {
          if (btn && btn.contains(e.target)) return;
          if (!menu.contains(e.target)) {
            menu.classList.add('hidden');
          }
        }
      });

      userInfoSyncInterval = setInterval(function() {
        if (document.getElementById('shared-user-name')) {
          clearInterval(userInfoSyncInterval);
          updateSharedUserInfo();
        }
      }, 50);
      // Fallback: stop after 2s
      setTimeout(() => clearInterval(userInfoSyncInterval), 2000);
    })
    .catch(function (error) {
      console.error('Header loader error:', error);
    });
});

function resetSharedUserInfo() {
  const avatar = document.getElementById('shared-user-avatar');
  const nameSpan = document.getElementById('shared-user-name');
  const menuName = document.getElementById('shared-menu-name');
  const menuRole = document.getElementById('shared-menu-role');

  if (avatar) {
    avatar.className = 'user-avatar user-avatar-human';
    avatar.textContent = '\uD83E\uDDD1';
  }
  if (nameSpan) nameSpan.textContent = 'User';
  if (menuName) menuName.textContent = 'User Name';
  if (menuRole) menuRole.textContent = 'USER';
}

function getPreferredDisplayName(name, email) {
  const normalizedName = (name || '').trim();
  if (normalizedName) {
    const trimmedName = normalizedName.replace(/\s+user$/i, '').trim();
    return trimmedName || normalizedName;
  }

  const normalizedEmail = (email || '').trim();
  return normalizedEmail.split('@')[0] || 'User';
}

function applySharedUserInfo(userInfo) {
  const avatar = document.getElementById('shared-user-avatar');
  const nameSpan = document.getElementById('shared-user-name');
  const menuName = document.getElementById('shared-menu-name');
  const menuRole = document.getElementById('shared-menu-role');
  const role = (userInfo.role || 'user').trim() || 'user';
  const normalizedName = (userInfo.name || '').trim();
  const normalizedEmail = (userInfo.email || '').trim();
  const isBot = role.toLowerCase().includes('bot');
  const displayName = getPreferredDisplayName(normalizedName, normalizedEmail);

  if (avatar) {
    avatar.className = 'user-avatar ' + (isBot ? 'user-avatar-bot' : 'user-avatar-human');
    avatar.textContent = isBot ? '\uD83E\uDD16' : '\uD83E\uDDD1';
  }
  if (nameSpan) nameSpan.textContent = displayName;
  if (menuName) menuName.textContent = displayName;
  if (menuRole) menuRole.textContent = role.toUpperCase();

  const isAdmin = role.toLowerCase() === 'admin';
  const manageBtn = document.getElementById('btn-manage-users');
  if (manageBtn) manageBtn.style.display = isAdmin ? 'flex' : 'none';
  const manageOrgsBtn = document.getElementById('btn-manage-orgs');
  if (manageOrgsBtn) manageOrgsBtn.style.display = isAdmin ? 'flex' : 'none';
}

function decodeJwtPayload(token) {
  const base64Url = token.split('.')[1];
  if (!base64Url) return null;

  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
  }).join(''));

  return JSON.parse(jsonPayload);
}

function extractUserInfo(payload) {
  if (!payload || typeof payload !== 'object') return null;

  const email = payload.sub || payload.email || payload.preferred_username || payload.username || '';
  const name = payload.full_name || payload.name || '';
  const role = payload.role || payload.user_role || 'user';

  return { email, name, role };
}

async function fetchCurrentUser(token) {
  const response = await fetch('/api/auth/me', {
    headers: { Authorization: 'Bearer ' + token },
    credentials: 'same-origin'
  });

  if (!response.ok) {
    throw new Error('Failed to load current user');
  }

  const user = await response.json();
  return {
    email: user.email || '',
    name: user.full_name || user.name || '',
    role: user.role || 'user'
  };
}

async function updateSharedUserInfo() {
  const tok = localStorage.getItem('rb_token');
  if (!tok) {
    resetSharedUserInfo();
    return;
  }

  let tokenUserInfo = null;
  try {
    const payload = decodeJwtPayload(tok);
    if (payload) {
      tokenUserInfo = extractUserInfo(payload);
    }
  } catch (e) {
    console.error('Error parsing token for header info:', e);
  }

  if (tokenUserInfo && (tokenUserInfo.name || tokenUserInfo.email)) {
    applySharedUserInfo(tokenUserInfo);
  }

  // Always attempt to fetch absolute source of truth from /me if name is suspiciously generic
  const currentName = document.getElementById('shared-user-name')?.textContent || '';
  if (!currentName || currentName === 'User' || currentName === 'Admin') {
    try {
      const currentUser = await fetchCurrentUser(tok);
      if (currentUser && (currentUser.name || currentUser.email)) {
        applySharedUserInfo(currentUser);
      }
    } catch (e) {
      console.warn('Could not refresh full user info from API:', e);
    }
  }
}

window.updateSharedUserInfo = updateSharedUserInfo;

/* ── Dev Auto-Login (local only) ─────────────────────────────────────────── */
async function tryDevAutoLogin() {
  const hostname = window.location.hostname;
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') return;
  try {
    const res = await fetch('/api/auth/dev-config');
    if (!res.ok) return; // 404 in production — silent, do nothing
    const cfg = await res.json();
    const emailEl = document.getElementById('login-email');
    const pwdEl   = document.getElementById('login-password');
    if (emailEl) emailEl.value = cfg.email;
    if (pwdEl)   pwdEl.value   = cfg.password;
    if (typeof window.login === 'function') await window.login();
  } catch { /* network error or non-local env — silent */ }
}
window.tryDevAutoLogin = tryDevAutoLogin;

/* ── Change Password ─────────────────────────────────────────────────────── */

function openChangePassword() {
  const menu = document.getElementById('shared-user-menu');
  if (menu) menu.classList.add('hidden');
  document.getElementById('chpwd-current').value = '';
  document.getElementById('chpwd-new').value = '';
  document.getElementById('chpwd-confirm').value = '';
  document.getElementById('chpwd-strength-bar').style.width = '0%';
  document.getElementById('chpwd-strength-label').textContent = '';
  const msg = document.getElementById('chpwd-msg');
  msg.className = '';
  msg.textContent = '';
  msg.style.display = 'none';
  document.getElementById('chpwd-submit').disabled = false;
  document.getElementById('chpwd-overlay').classList.add('open');
  setTimeout(() => document.getElementById('chpwd-current').focus(), 100);
}

function closeChangePassword() {
  document.getElementById('chpwd-overlay').classList.remove('open');
}

function handleChpwdOverlayClick(e) {
  if (e.target === document.getElementById('chpwd-overlay')) closeChangePassword();
}

function toggleChpwdEye(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
  else { input.type = 'password'; btn.textContent = '👁'; }
}

function updateStrength(val) {
  const bar = document.getElementById('chpwd-strength-bar');
  const label = document.getElementById('chpwd-strength-label');
  let score = 0;
  if (val.length >= 8) score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const levels = [
    { pct: '0%',   color: '#0f172a', text: '' },
    { pct: '25%',  color: '#ef4444', text: 'Weak' },
    { pct: '50%',  color: '#f97316', text: 'Fair' },
    { pct: '75%',  color: '#eab308', text: 'Good' },
    { pct: '90%',  color: '#22c55e', text: 'Strong' },
    { pct: '100%', color: '#10b981', text: 'Very strong' },
  ];
  const l = levels[score] || levels[0];
  bar.style.width = l.pct;
  bar.style.background = l.color;
  label.textContent = l.text;
  label.style.color = l.color;
}

async function submitChangePassword() {
  const current = document.getElementById('chpwd-current').value.trim();
  const newPwd  = document.getElementById('chpwd-new').value;
  const confirm = document.getElementById('chpwd-confirm').value;
  const msg     = document.getElementById('chpwd-msg');
  const btn     = document.getElementById('chpwd-submit');

  const showMsg = (text, type) => {
    msg.textContent = text;
    msg.className = type;
    msg.style.display = 'block';
  };

  if (!current) { showMsg('Please enter your current password.', 'error'); return; }
  if (newPwd.length < 8) { showMsg('New password must be at least 8 characters.', 'error'); return; }
  if (newPwd !== confirm) { showMsg('New passwords do not match.', 'error'); return; }

  btn.disabled = true;
  btn.textContent = 'Updating…';

  try {
    const token = localStorage.getItem('rb_token') || '';
    const res = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ current_password: current, new_password: newPwd })
    });
    const data = await res.json();
    if (!res.ok) {
      showMsg(data.detail || 'Failed to change password.', 'error');
      btn.disabled = false;
      btn.textContent = 'Update Password';
    } else {
      showMsg('Password updated successfully!', 'success');
      btn.textContent = 'Done';
      setTimeout(() => closeChangePassword(), 1800);
    }
  } catch (e) {
    showMsg('Network error. Please try again.', 'error');
    btn.disabled = false;
    btn.textContent = 'Update Password';
  }
}

/* ── Manage Users (admin only) ───────────────────────────────────────────── */

function _adminToken() { return localStorage.getItem('rb_token') || ''; }

let _orgsCache = [];     // cached org list for populating dropdowns
let _editUserId = null;  // user currently being edited
let _editOrgId  = null;  // org currently being edited

async function openManageUsers() {
  const menu = document.getElementById('shared-user-menu');
  if (menu) menu.classList.add('hidden');
  document.getElementById('mgu-add-form').classList.remove('open');
  document.getElementById('mgu-new-pwd-box').classList.remove('show');
  document.getElementById('mgu-reset-pwd-box').classList.remove('show');
  document.getElementById('mgu-edit-bar').style.display = 'none';
  _editUserId = null;
  const msg = document.getElementById('mgusers-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('mgusers-overlay').classList.add('open');
  await loadOrgsIntoSelect('mgu-new-org');
  await loadUsersList();
}

function closeManageUsers() {
  document.getElementById('mgusers-overlay').classList.remove('open');
  cancelMguConfirm();
}

function handleMguOverlayClick(e) {
  if (e.target === document.getElementById('mgusers-overlay')) closeManageUsers();
}

async function loadUsersList() {
  const loading = document.getElementById('mgu-loading');
  const table   = document.getElementById('mgu-table');
  const tbody   = document.getElementById('mgu-tbody');
  loading.style.display = 'block';
  table.style.display = 'none';
  try {
    const res = await fetch('/api/admin/users', {
      headers: { 'Authorization': 'Bearer ' + _adminToken() }
    });
    if (!res.ok) throw new Error('Failed to load users');
    const users = await res.json();
    tbody.innerHTML = '';
    const currentPayload = _decodeToken(_adminToken());
    const currentEmail = currentPayload ? currentPayload.sub : null;
    users.forEach(u => {
      const isSelf = u.email === currentEmail;
      const roleClass = `mgu-role-${u.role}`;
      const statusHtml = u.is_active
        ? '<span class="mgu-status-active">● Active</span>'
        : '<span class="mgu-status-inactive">● Inactive</span>';
      const toggleLabel = u.is_active ? 'Deactivate' : 'Activate';
      const toggleClass = u.is_active ? 'danger' : 'success';
      const orgName = _esc(u.organization_name || '—');
      const orgId   = u.organization_id || 0;
      tbody.innerHTML += `
        <tr>
          <td>${_esc(u.full_name)}</td>
          <td style="color:#64748b">${_esc(u.email)}</td>
          <td><span class="mgu-role-badge ${roleClass}">${u.role}</span></td>
          <td style="color:#94a3b8">${orgName}</td>
          <td>${statusHtml}</td>
          <td>
            <button class="mgu-action-btn" onclick="openEditUser(${u.id}, '${_esc(u.email)}', '${u.role}', ${orgId})">Edit</button>
            <button class="mgu-action-btn" onclick="mguResetPassword(${u.id}, '${_esc(u.email)}')">Reset Pwd</button>
            ${!isSelf ? `<button class="mgu-action-btn ${toggleClass}" onclick="mguToggleActive(${u.id}, ${u.is_active})">${toggleLabel}</button>` : ''}
            ${!isSelf ? `<button class="mgu-action-btn danger" onclick="mguDeleteUser(${u.id}, '${_esc(u.email)}')">Delete</button>` : ''}
          </td>
        </tr>`;
    });
    loading.style.display = 'none';
    table.style.display = 'table';
  } catch (e) {
    loading.textContent = 'Failed to load users.';
  }
}

function toggleAddUserForm() {
  const form = document.getElementById('mgu-add-form');
  const isOpen = form.classList.toggle('open');
  if (isOpen) {
    document.getElementById('mgu-new-name').value = '';
    document.getElementById('mgu-new-email').value = '';
    document.getElementById('mgu-new-role').value = 'reviewer';
    document.getElementById('mgu-new-pwd-box').classList.remove('show');
    document.getElementById('mgu-submit-btn').disabled = false;
    document.getElementById('mgu-submit-btn').textContent = 'Create User';
    setTimeout(() => document.getElementById('mgu-new-name').focus(), 80);
  }
}

async function submitAddUser() {
  const name  = document.getElementById('mgu-new-name').value.trim();
  const email = document.getElementById('mgu-new-email').value.trim();
  const role  = document.getElementById('mgu-new-role').value;
  const orgRaw = parseInt(document.getElementById('mgu-new-org').value, 10) || 0;
  const btn   = document.getElementById('mgu-submit-btn');
  const msg   = document.getElementById('mgusers-msg');

  if (!name || !email) {
    msg.textContent = 'Full name and email are required.';
    msg.className = 'error'; return;
  }
  btn.disabled = true; btn.textContent = 'Creating…';
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';

  const body = { full_name: name, email, role };
  if (orgRaw > 0) body.organization_id = orgRaw;

  try {
    const res = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.detail || 'Failed to create user.';
      msg.className = 'error';
      btn.disabled = false; btn.textContent = 'Create User';
    } else {
      document.getElementById('mgu-new-pwd-text').textContent = data.generated_password;
      document.getElementById('mgu-new-pwd-box').classList.add('show');
      btn.textContent = 'User Created';
      await loadUsersList();
    }
  } catch (e) {
    msg.textContent = 'Network error.'; msg.className = 'error';
    btn.disabled = false; btn.textContent = 'Create User';
  }
}

let _pendingAction = null; // { type: 'reset'|'delete', userId, email }

function _showConfirmBar(title, desc, confirmLabel) {
  document.getElementById('mgu-confirm-title').textContent = title;
  document.getElementById('mgu-confirm-desc').textContent = desc;
  document.getElementById('mgu-confirm-bar').querySelector('.mgu-confirm-yes').textContent = confirmLabel;
  const bar = document.getElementById('mgu-confirm-bar');
  bar.classList.add('show');
  bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function mguResetPassword(userId, email) {
  document.getElementById('mgu-reset-pwd-box').classList.remove('show');
  _pendingAction = { type: 'reset', userId, email };
  _showConfirmBar('Reset password for this user?', email + ' will receive a new generated password.', 'Yes, Reset');
}

function mguDeleteUser(userId, email) {
  document.getElementById('mgu-reset-pwd-box').classList.remove('show');
  _pendingAction = { type: 'delete', userId, email };
  _showConfirmBar('Permanently delete this user?', email + ' will be removed and cannot be recovered.', 'Yes, Delete');
}

function cancelMguConfirm() {
  _pendingAction = null;
  document.getElementById('mgu-confirm-bar').classList.remove('show');
}

async function executeMguConfirm() {
  if (!_pendingAction) return;
  const { type, userId, email } = _pendingAction;
  _pendingAction = null;
  document.getElementById('mgu-confirm-bar').classList.remove('show');

  if (type === 'reset') {
    try {
      const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + _adminToken() }
      });
      const data = await res.json();
      if (!res.ok) {
        const msg = document.getElementById('mgusers-msg');
        msg.textContent = data.detail || 'Failed to reset password.'; msg.className = 'error';
      } else {
        document.getElementById('mgu-reset-email').textContent = email;
        document.getElementById('mgu-reset-pwd-text').textContent = data.generated_password;
        document.getElementById('mgu-reset-pwd-box').classList.add('show');
        document.getElementById('mgu-reset-pwd-box').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    } catch (e) {
      const msg = document.getElementById('mgusers-msg');
      msg.textContent = 'Network error.'; msg.className = 'error';
    }
  } else if (type === 'delete') {
    try {
      const res = await fetch(`/api/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { 'Authorization': 'Bearer ' + _adminToken() }
      });
      if (!res.ok) {
        const data = await res.json();
        const msg = document.getElementById('mgusers-msg');
        msg.textContent = data.detail || 'Failed to delete user.'; msg.className = 'error';
      } else {
        await loadUsersList();
      }
    } catch (e) {
      const msg = document.getElementById('mgusers-msg');
      msg.textContent = 'Network error.'; msg.className = 'error';
    }
  }
}

async function mguToggleActive(userId, currentlyActive) {
  try {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ is_active: !currentlyActive })
    });
    if (!res.ok) throw new Error();
    await loadUsersList();
  } catch (e) {
    const msg = document.getElementById('mgusers-msg');
    msg.textContent = 'Failed to update user status.'; msg.className = 'error';
  }
}

function copyMguPwd(spanId, btn) {
  const text = document.getElementById(spanId).textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
  });
}

/* ── Edit User (inline bar) ──────────────────────────────────────────────── */

async function openEditUser(userId, email, role, orgId) {
  _editUserId = userId;
  document.getElementById('mgu-edit-email-label').textContent = email;
  document.getElementById('mgu-edit-role').value = role;
  await loadOrgsIntoSelect('mgu-edit-org');
  document.getElementById('mgu-edit-org').value = String(orgId || 0);
  const bar = document.getElementById('mgu-edit-bar');
  bar.style.display = 'block';
  bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function submitEditUser() {
  if (!_editUserId) return;
  const role   = document.getElementById('mgu-edit-role').value;
  const orgRaw = parseInt(document.getElementById('mgu-edit-org').value, 10) || 0;
  const msg    = document.getElementById('mgusers-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';

  try {
    const res = await fetch(`/api/admin/users/${_editUserId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ role, organization_id: orgRaw })
    });
    if (!res.ok) {
      const data = await res.json();
      msg.textContent = data.detail || 'Failed to update user.'; msg.className = 'error'; msg.style.display = 'block';
    } else {
      closeEditUser();
      await loadUsersList();
    }
  } catch (e) {
    msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block';
  }
}

function closeEditUser() {
  _editUserId = null;
  document.getElementById('mgu-edit-bar').style.display = 'none';
}

/* ── Org dropdown helper ─────────────────────────────────────────────────── */

async function loadOrgsIntoSelect(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;

  // Re-use cache if already populated; if empty, fetch
  if (_orgsCache.length === 0) {
    try {
      const res = await fetch('/api/organizations/', {
        headers: { 'Authorization': 'Bearer ' + _adminToken() }
      });
      if (res.ok) _orgsCache = await res.json();
    } catch { /* silent */ }
  }

  // Keep only the first "None" option, then append orgs
  sel.innerHTML = '<option value="0">— None —</option>';
  _orgsCache.forEach(o => {
    const opt = document.createElement('option');
    opt.value = o.id;
    opt.textContent = o.name;
    sel.appendChild(opt);
  });
}

/* ── Manage Organizations (admin only) ───────────────────────────────────── */

async function openManageOrgs() {
  const menu = document.getElementById('shared-user-menu');
  if (menu) menu.classList.add('hidden');
  _orgsCache = []; // force fresh fetch
  document.getElementById('mgorgs-add-form').style.display = 'none';
  document.getElementById('mgorgs-edit-bar').style.display = 'none';
  _editOrgId = null;
  const msg = document.getElementById('mgorgs-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('mgorgs-overlay').style.display = 'flex';
  await loadOrgsList();
}

function closeManageOrgs() {
  document.getElementById('mgorgs-overlay').style.display = 'none';
  _editOrgId = null;
}

function handleMgorgsOverlayClick(e) {
  if (e.target === document.getElementById('mgorgs-overlay')) closeManageOrgs();
}

async function loadOrgsList() {
  const loading = document.getElementById('mgorgs-loading');
  const table   = document.getElementById('mgorgs-table');
  const tbody   = document.getElementById('mgorgs-tbody');
  loading.style.display = 'block'; loading.textContent = 'Loading organizations…';
  table.style.display = 'none';
  try {
    const res = await fetch('/api/organizations/?active_only=false', {
      headers: { 'Authorization': 'Bearer ' + _adminToken() }
    });
    if (!res.ok) throw new Error('Failed to load orgs');
    const data = await res.json();
    const orgs = Array.isArray(data) ? data : (data.organizations || []);
    _orgsCache = orgs.filter(o => o.is_active !== false); // keep active ones cached
    tbody.innerHTML = '';
    orgs.forEach(o => {
      const statusHtml = o.is_active !== false
        ? '<span class="mgu-status-active">● Active</span>'
        : '<span class="mgu-status-inactive">● Inactive</span>';
      const toggleLabel = o.is_active !== false ? 'Deactivate' : 'Activate';
      const toggleClass = o.is_active !== false ? 'danger' : 'success';
      tbody.innerHTML += `
        <tr>
          <td style="font-weight:600;color:#e2e8f0">${_esc(o.name)}</td>
          <td style="color:#64748b;font-family:monospace;font-size:12px">${_esc(o.slug || '')}</td>
          <td style="color:#94a3b8">${_esc(o.description || '—')}</td>
          <td>${statusHtml}</td>
          <td>
            <button class="mgu-action-btn" onclick="openEditOrg(${o.id}, '${_esc(o.name)}', '${_esc(o.description || '')}')">Edit</button>
            <button class="mgu-action-btn ${toggleClass}" onclick="mguToggleOrgActive(${o.id}, ${o.is_active !== false})">${toggleLabel}</button>
          </td>
        </tr>`;
    });
    loading.style.display = 'none';
    table.style.display = 'table';
  } catch (e) {
    loading.textContent = 'Failed to load organizations.';
  }
}

function toggleAddOrgForm() {
  const form = document.getElementById('mgorgs-add-form');
  const isOpen = form.style.display === 'block';
  form.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) {
    document.getElementById('mgorgs-new-name').value = '';
    document.getElementById('mgorgs-new-desc').value = '';
    document.getElementById('mgorgs-submit-btn').disabled = false;
    document.getElementById('mgorgs-submit-btn').textContent = 'Create';
    setTimeout(() => document.getElementById('mgorgs-new-name').focus(), 80);
  }
}

async function submitAddOrg() {
  const name = document.getElementById('mgorgs-new-name').value.trim();
  const desc = document.getElementById('mgorgs-new-desc').value.trim();
  const btn  = document.getElementById('mgorgs-submit-btn');
  const msg  = document.getElementById('mgorgs-msg');

  if (!name) {
    msg.textContent = 'Organization name is required.'; msg.className = 'error'; msg.style.display = 'block'; return;
  }
  btn.disabled = true; btn.textContent = 'Creating…';
  msg.style.display = 'none';

  try {
    const res = await fetch('/api/organizations/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ name, description: desc || null })
    });
    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.detail || 'Failed to create organization.'; msg.className = 'error'; msg.style.display = 'block';
      btn.disabled = false; btn.textContent = 'Create';
    } else {
      toggleAddOrgForm();
      _orgsCache = []; // invalidate cache
      await loadOrgsList();
    }
  } catch (e) {
    msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block';
    btn.disabled = false; btn.textContent = 'Create';
  }
}

function openEditOrg(orgId, name, desc) {
  _editOrgId = orgId;
  document.getElementById('mgorgs-edit-name').value = name;
  document.getElementById('mgorgs-edit-desc').value = desc;
  const bar = document.getElementById('mgorgs-edit-bar');
  bar.style.display = 'block';
  bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function submitEditOrg() {
  if (!_editOrgId) return;
  const name = document.getElementById('mgorgs-edit-name').value.trim();
  const desc = document.getElementById('mgorgs-edit-desc').value.trim();
  const msg  = document.getElementById('mgorgs-msg');

  if (!name) {
    msg.textContent = 'Organization name is required.'; msg.className = 'error'; msg.style.display = 'block'; return;
  }
  msg.style.display = 'none';

  try {
    const res = await fetch(`/api/organizations/${_editOrgId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ name, description: desc || null })
    });
    const data = await res.json();
    if (!res.ok) {
      msg.textContent = data.detail || 'Failed to update organization.'; msg.className = 'error'; msg.style.display = 'block';
    } else {
      closeEditOrg();
      _orgsCache = []; // invalidate cache
      await loadOrgsList();
    }
  } catch (e) {
    msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block';
  }
}

function closeEditOrg() {
  _editOrgId = null;
  document.getElementById('mgorgs-edit-bar').style.display = 'none';
}

async function mguToggleOrgActive(orgId, currentlyActive) {
  const msg = document.getElementById('mgorgs-msg');
  msg.style.display = 'none';
  try {
    const res = await fetch(`/api/organizations/${orgId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ is_active: !currentlyActive })
    });
    if (!res.ok) {
      const data = await res.json();
      msg.textContent = data.detail || 'Failed to update organization.'; msg.className = 'error'; msg.style.display = 'block';
    } else {
      _orgsCache = [];
      await loadOrgsList();
    }
  } catch (e) {
    msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block';
  }
}

function _esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _decodeToken(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/');
    return JSON.parse(decodeURIComponent(atob(base64).split('').map(c => '%' + ('00'+c.charCodeAt(0).toString(16)).slice(-2)).join('')));
  } catch { return null; }
}

window.openManageUsers       = openManageUsers;
window.closeManageUsers      = closeManageUsers;
window.handleMguOverlayClick = handleMguOverlayClick;
window.toggleAddUserForm     = toggleAddUserForm;
window.submitAddUser         = submitAddUser;
window.mguResetPassword      = mguResetPassword;
window.mguDeleteUser         = mguDeleteUser;
window.cancelMguConfirm      = cancelMguConfirm;
window.executeMguConfirm     = executeMguConfirm;
window.mguToggleActive       = mguToggleActive;
window.copyMguPwd            = copyMguPwd;
window.openEditUser          = openEditUser;
window.submitEditUser        = submitEditUser;
window.closeEditUser         = closeEditUser;

window.openManageOrgs           = openManageOrgs;
window.closeManageOrgs          = closeManageOrgs;
window.handleMgorgsOverlayClick = handleMgorgsOverlayClick;
window.toggleAddOrgForm         = toggleAddOrgForm;
window.submitAddOrg             = submitAddOrg;
window.openEditOrg              = openEditOrg;
window.submitEditOrg            = submitEditOrg;
window.closeEditOrg             = closeEditOrg;
window.mguToggleOrgActive       = mguToggleOrgActive;

window.openChangePassword    = openChangePassword;
window.closeChangePassword   = closeChangePassword;
window.handleChpwdOverlayClick = handleChpwdOverlayClick;
window.toggleChpwdEye        = toggleChpwdEye;
window.updateStrength        = updateStrength;
window.submitChangePassword  = submitChangePassword;
