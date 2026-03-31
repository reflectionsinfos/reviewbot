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

  const manageBtn = document.getElementById('btn-manage-users');
  if (manageBtn) manageBtn.style.display = role.toLowerCase() === 'admin' ? 'flex' : 'none';
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

async function openManageUsers() {
  const menu = document.getElementById('shared-user-menu');
  if (menu) menu.classList.add('hidden');
  document.getElementById('mgu-add-form').classList.remove('open');
  document.getElementById('mgu-new-pwd-box').classList.remove('show');
  document.getElementById('mgu-reset-pwd-box').classList.remove('show');
  const msg = document.getElementById('mgusers-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('mgusers-overlay').classList.add('open');
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
      tbody.innerHTML += `
        <tr>
          <td>${_esc(u.full_name)}</td>
          <td style="color:#64748b">${_esc(u.email)}</td>
          <td><span class="mgu-role-badge ${roleClass}">${u.role}</span></td>
          <td>${statusHtml}</td>
          <td>
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
  const btn   = document.getElementById('mgu-submit-btn');
  const msg   = document.getElementById('mgusers-msg');

  if (!name || !email) {
    msg.textContent = 'Full name and email are required.';
    msg.className = 'error'; return;
  }
  btn.disabled = true; btn.textContent = 'Creating…';
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';

  try {
    const res = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify({ full_name: name, email, role })
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

window.openChangePassword    = openChangePassword;
window.closeChangePassword   = closeChangePassword;
window.handleChpwdOverlayClick = handleChpwdOverlayClick;
window.toggleChpwdEye        = toggleChpwdEye;
window.updateStrength        = updateStrength;
window.submitChangePassword  = submitChangePassword;
