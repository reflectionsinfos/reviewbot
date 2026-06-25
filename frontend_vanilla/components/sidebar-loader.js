window.toggleSidebarDropdown = function (e) {
  if (e) e.stopPropagation();
  var menu = document.getElementById('sidebar-user-menu');
  if (menu) menu.classList.toggle('open');
};

document.addEventListener('click', function (e) {
  var menu = document.getElementById('sidebar-user-menu');
  if (menu && menu.classList.contains('open')) {
    var btn = document.querySelector('.sidebar .user-dropdown-btn');
    if (btn && btn.contains(e.target)) return;
    if (!menu.contains(e.target)) {
      menu.classList.remove('open');
    }
  }
});

function resetSharedUserInfo() {
  var avatar = document.getElementById('shared-user-avatar');
  var nameSpan = document.getElementById('shared-user-name');
  var menuName = document.getElementById('shared-menu-name');
  var menuRole = document.getElementById('shared-menu-role');
  if (avatar) { avatar.className = 'user-avatar user-avatar-human'; avatar.textContent = '\uD83E\uDDD1'; }
  if (nameSpan) nameSpan.textContent = 'User';
  if (menuName) menuName.textContent = 'User Name';
  if (menuRole) menuRole.textContent = 'USER';
}

function getPreferredDisplayName(name, email) {
  var normalizedName = (name || '').trim();
  if (normalizedName) {
    var trimmedName = normalizedName.replace(/\s+user$/i, '').trim();
    return trimmedName || normalizedName;
  }
  var normalizedEmail = (email || '').trim();
  return normalizedEmail.split('@')[0] || 'User';
}

function applySharedUserInfo(userInfo) {
  var avatar = document.getElementById('shared-user-avatar');
  var nameSpan = document.getElementById('shared-user-name');
  var menuName = document.getElementById('shared-menu-name');
  var menuRole = document.getElementById('shared-menu-role');
  var role = (userInfo.role || 'user').trim() || 'user';
  var normalizedName = (userInfo.name || '').trim();
  var normalizedEmail = (userInfo.email || '').trim();
  var isBot = role.toLowerCase().includes('bot');
  var displayName = getPreferredDisplayName(normalizedName, normalizedEmail);
  if (avatar) {
    avatar.className = 'user-avatar ' + (isBot ? 'user-avatar-bot' : 'user-avatar-human');
    avatar.textContent = isBot ? '\uD83E\uDD16' : '\uD83E\uDDD1';
  }
  if (nameSpan) nameSpan.textContent = displayName;
  if (menuName) menuName.textContent = displayName;
  if (menuRole) menuRole.textContent = role.toUpperCase();
  var isAdmin = role.toLowerCase() === 'admin';
  var mgu = document.getElementById('sb-manage-users');
  var org = document.getElementById('sb-manage-orgs');
  if (mgu) mgu.style.display = isAdmin ? 'flex' : 'none';
  if (org) org.style.display = isAdmin ? 'flex' : 'none';
}

function decodeJwtPayload(token) {
  var base64Url = token.split('.')[1];
  if (!base64Url) return null;
  var base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  var jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
  }).join(''));
  return JSON.parse(jsonPayload);
}

function extractUserInfo(payload) {
  if (!payload || typeof payload !== 'object') return null;
  return {
    email: payload.sub || payload.email || payload.preferred_username || payload.username || '',
    name: payload.full_name || payload.name || '',
    role: payload.role || payload.user_role || 'user'
  };
}

async function fetchCurrentUser(token) {
  var response = await fetch('/api/auth/me', {
    headers: { Authorization: 'Bearer ' + token },
    credentials: 'same-origin'
  });
  if (!response.ok) throw new Error('Failed to load current user');
  var user = await response.json();
  return {
    email: user.email || '',
    name: user.full_name || user.name || '',
    role: user.role || 'user'
  };
}

async function updateSharedUserInfo() {
  var tok = localStorage.getItem('rb_token');
  if (!tok) {
    resetSharedUserInfo();
    return;
  }
  var tokenUserInfo = null;
  try {
    var payload = decodeJwtPayload(tok);
    if (payload) tokenUserInfo = extractUserInfo(payload);
  } catch (e) {}
  if (tokenUserInfo && (tokenUserInfo.name || tokenUserInfo.email)) {
    applySharedUserInfo(tokenUserInfo);
  }
  var currentName = document.getElementById('shared-user-name')?.textContent || '';
  if (!currentName || currentName === 'User' || currentName === 'Admin') {
    try {
      var currentUser = await fetchCurrentUser(tok);
      if (currentUser && (currentUser.name || currentUser.email)) {
        applySharedUserInfo(currentUser);
      }
    } catch (e) {}
  }
}

window.updateSharedUserInfo = updateSharedUserInfo;

/* ── Dev Auto-Login (local only) ─────────────────────────────────────────── */
async function tryDevAutoLogin() {
  var hostname = window.location.hostname;
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') return;
  try {
    var res = await fetch('/api/auth/dev-config');
    if (!res.ok) return;
    var cfg = await res.json();
    var emailEl = document.getElementById('login-email');
    var pwdEl   = document.getElementById('login-password');
    if (emailEl) emailEl.value = cfg.email;
    if (pwdEl)   pwdEl.value   = cfg.password;
    if (typeof window.login === 'function') await window.login();
  } catch (e) {}
}
window.tryDevAutoLogin = tryDevAutoLogin;

function syncSidebarAdminButtons() {
  var tok = localStorage.getItem('rb_token');
  if (!tok) return;
  var isAdmin = false;
  try {
    var payload = decodeJwtPayload(tok);
    var role = ((payload && (payload.role || payload.user_role)) || '').toLowerCase();
    isAdmin = role === 'admin';
  } catch (e) {}
  var mgu = document.getElementById('sb-manage-users');
  var org = document.getElementById('sb-manage-orgs');
  if (mgu) mgu.style.display = isAdmin ? 'flex' : 'none';
  if (org) org.style.display = isAdmin ? 'flex' : 'none';
}

document.addEventListener('DOMContentLoaded', function () {
  var root = document.getElementById('shared-sidebar-root');
  if (!root) return;

  fetch('/frontend_vanilla/components/sidebar.html', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) throw new Error('Failed to load sidebar');
      return response.text();
    })
    .then(function (html) {
      if (!root.isConnected) return;
      root.innerHTML = html;
      updateSharedUserInfo();

      var path = window.location.pathname;
      var links = root.querySelectorAll('.nav a');
      links.forEach(function (a) {
        a.classList.remove('active');
        if (path === '/' || path === '/dashboard') {
          if (a.getAttribute('href') === '/') a.classList.add('active');
        } else if (path.includes('/ui')) {
          if (a.getAttribute('href') === '/ui') a.classList.add('active');
        } else if (path.includes('/projects-ui') || path.includes('/project.html')) {
          if (a.getAttribute('href') === '/projects-ui') a.classList.add('active');
        } else if (path.includes('/globals')) {
          if (a.getAttribute('href') === '/globals') a.classList.add('active');
        } else if (path.includes('/history')) {
          if (a.getAttribute('href') === '/history') a.classList.add('active');
        } else if (path.includes('/system-config')) {
          if (a.getAttribute('href') === '/system-config') a.classList.add('active');
        } else if (path.includes('/documentation')) {
          if (a.getAttribute('href') === '/documentation') a.classList.add('active');
        }
      });
    })
    .catch(function (error) {
      console.error('Sidebar loader error:', error);
    });
});

/* ── Close both header + sidebar user menus ──────────────────────────────── */
function _closeUserMenus() {
  var hdr = document.getElementById('shared-user-menu');
  if (hdr) hdr.classList.add('hidden');
  var sbr = document.getElementById('sidebar-user-menu');
  if (sbr) sbr.classList.remove('open');
}

/* ── Change Password ─────────────────────────────────────────────────────── */
function openChangePassword() {
  _closeUserMenus();
  document.getElementById('chpwd-current').value = '';
  document.getElementById('chpwd-new').value = '';
  document.getElementById('chpwd-confirm').value = '';
  document.getElementById('chpwd-strength-bar').style.width = '0%';
  document.getElementById('chpwd-strength-label').textContent = '';
  var msg = document.getElementById('chpwd-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('chpwd-submit').disabled = false;
  document.getElementById('chpwd-overlay').classList.add('open');
  setTimeout(function () { document.getElementById('chpwd-current').focus(); }, 100);
}
function closeChangePassword() { document.getElementById('chpwd-overlay').classList.remove('open'); }
function handleChpwdOverlayClick(e) { if (e.target === document.getElementById('chpwd-overlay')) closeChangePassword(); }
function toggleChpwdEye(inputId, btn) {
  var input = document.getElementById(inputId);
  if (input.type === 'password') { input.type = 'text'; btn.textContent = '\uD83D\uDE48'; }
  else { input.type = 'password'; btn.textContent = '\uD83D\uDC41'; }
}
function updateStrength(val) {
  var bar = document.getElementById('chpwd-strength-bar');
  var label = document.getElementById('chpwd-strength-label');
  var score = 0;
  if (val.length >= 8) score++;
  if (val.length >= 12) score++;
  if (/[A-Z]/.test(val)) score++;
  if (/[0-9]/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  var levels = [
    { pct: '0%', color: '#0f172a', text: '' },
    { pct: '25%', color: '#ef4444', text: 'Weak' },
    { pct: '50%', color: '#f97316', text: 'Fair' },
    { pct: '75%', color: '#eab308', text: 'Good' },
    { pct: '90%', color: '#22c55e', text: 'Strong' },
    { pct: '100%', color: '#10b981', text: 'Very strong' }
  ];
  var l = levels[score] || levels[0];
  bar.style.width = l.pct; bar.style.background = l.color;
  label.textContent = l.text; label.style.color = l.color;
}
async function submitChangePassword() {
  var current = document.getElementById('chpwd-current').value.trim();
  var newPwd = document.getElementById('chpwd-new').value;
  var confirm = document.getElementById('chpwd-confirm').value;
  var msg = document.getElementById('chpwd-msg');
  var btn = document.getElementById('chpwd-submit');
  function showMsg(text, type) { msg.textContent = text; msg.className = type; msg.style.display = 'block'; }
  if (!current) { showMsg('Please enter your current password.', 'error'); return; }
  if (newPwd.length < 8) { showMsg('New password must be at least 8 characters.', 'error'); return; }
  if (newPwd !== confirm) { showMsg('New passwords do not match.', 'error'); return; }
  btn.disabled = true; btn.textContent = 'Updating\u2026';
  try {
    var token = localStorage.getItem('rb_token') || '';
    var res = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
      body: JSON.stringify({ current_password: current, new_password: newPwd })
    });
    var data = await res.json();
    if (!res.ok) { showMsg(data.detail || 'Failed to change password.', 'error'); btn.disabled = false; btn.textContent = 'Update Password'; }
    else { showMsg('Password updated successfully!', 'success'); btn.textContent = 'Done'; setTimeout(function () { closeChangePassword(); }, 1800); }
  } catch (e) { showMsg('Network error. Please try again.', 'error'); btn.disabled = false; btn.textContent = 'Update Password'; }
}

/* ── Manage Users (admin only) ───────────────────────────────────────────── */
function _adminToken() { return localStorage.getItem('rb_token') || ''; }
var _orgsCache = [];
var _editUserId = null;
var _editOrgId = null;

async function openManageUsers() {
  _closeUserMenus();
  document.getElementById('mgu-add-form').classList.remove('open');
  document.getElementById('mgu-new-pwd-box').classList.remove('show');
  document.getElementById('mgu-reset-pwd-box').classList.remove('show');
  document.getElementById('mgu-edit-bar').style.display = 'none';
  _editUserId = null;
  var msg = document.getElementById('mgusers-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('mgusers-overlay').classList.add('open');
  await loadOrgsIntoSelect('mgu-new-org');
  await loadUsersList();
}
function closeManageUsers() { document.getElementById('mgusers-overlay').classList.remove('open'); cancelMguConfirm(); }
function handleMguOverlayClick(e) { if (e.target === document.getElementById('mgusers-overlay')) closeManageUsers(); }

async function loadUsersList() {
  var loading = document.getElementById('mgu-loading');
  var table = document.getElementById('mgu-table');
  var tbody = document.getElementById('mgu-tbody');
  loading.style.display = 'block'; table.style.display = 'none';
  try {
    var res = await fetch('/api/admin/users', { headers: { 'Authorization': 'Bearer ' + _adminToken() } });
    if (!res.ok) throw new Error('Failed to load users');
    var users = await res.json();
    tbody.innerHTML = '';
    var currentPayload = _decodeToken(_adminToken());
    var currentEmail = currentPayload ? currentPayload.sub : null;
    users.forEach(function (u) {
      var isSelf = u.email === currentEmail;
      var roleClass = 'mgu-role-' + u.role;
      var statusHtml = u.is_active ? '<span class="mgu-status-active">\u25cf Active</span>' : '<span class="mgu-status-inactive">\u25cf Inactive</span>';
      var toggleLabel = u.is_active ? 'Deactivate' : 'Activate';
      var toggleClass = u.is_active ? 'danger' : 'success';
      var orgName = _esc(u.organization_name || '\u2014');
      var orgId = u.organization_id || 0;
      tbody.innerHTML += '<tr><td>' + _esc(u.full_name) + '</td><td style="color:#64748b">' + _esc(u.email) + '</td><td><span class="mgu-role-badge ' + roleClass + '">' + u.role + '</span></td><td style="color:#94a3b8">' + orgName + '</td><td>' + statusHtml + '</td><td><button class="mgu-action-btn" onclick="openEditUser(' + u.id + ', \'' + _esc(u.email) + '\', \'' + u.role + '\', ' + orgId + ')">Edit</button><button class="mgu-action-btn" onclick="mguResetPassword(' + u.id + ', \'' + _esc(u.email) + '\')">Reset Pwd</button>' + (!isSelf ? '<button class="mgu-action-btn ' + toggleClass + '" onclick="mguToggleActive(' + u.id + ', ' + u.is_active + ')">' + toggleLabel + '</button><button class="mgu-action-btn danger" onclick="mguDeleteUser(' + u.id + ', \'' + _esc(u.email) + '\')">Delete</button>' : '') + '</td></tr>';
    });
    loading.style.display = 'none'; table.style.display = 'table';
  } catch (e) { loading.textContent = 'Failed to load users.'; }
}

function toggleAddUserForm() {
  var form = document.getElementById('mgu-add-form');
  var isOpen = form.classList.toggle('open');
  if (isOpen) {
    document.getElementById('mgu-new-name').value = '';
    document.getElementById('mgu-new-email').value = '';
    document.getElementById('mgu-new-role').value = 'reviewer';
    document.getElementById('mgu-new-pwd-box').classList.remove('show');
    document.getElementById('mgu-submit-btn').disabled = false;
    document.getElementById('mgu-submit-btn').textContent = 'Create User';
    setTimeout(function () { document.getElementById('mgu-new-name').focus(); }, 80);
  }
}

async function submitAddUser() {
  var name = document.getElementById('mgu-new-name').value.trim();
  var email = document.getElementById('mgu-new-email').value.trim();
  var role = document.getElementById('mgu-new-role').value;
  var orgRaw = parseInt(document.getElementById('mgu-new-org').value, 10) || 0;
  var btn = document.getElementById('mgu-submit-btn');
  var msg = document.getElementById('mgusers-msg');
  if (!name || !email) { msg.textContent = 'Full name and email are required.'; msg.className = 'error'; return; }
  btn.disabled = true; btn.textContent = 'Creating\u2026';
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  var body = { full_name: name, email: email, role: role };
  if (orgRaw > 0) body.organization_id = orgRaw;
  try {
    var res = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() },
      body: JSON.stringify(body)
    });
    var data = await res.json();
    if (!res.ok) { msg.textContent = data.detail || 'Failed to create user.'; msg.className = 'error'; btn.disabled = false; btn.textContent = 'Create User'; }
    else { document.getElementById('mgu-new-pwd-text').textContent = data.generated_password; document.getElementById('mgu-new-pwd-box').classList.add('show'); btn.textContent = 'User Created'; await loadUsersList(); }
  } catch (e) { msg.textContent = 'Network error.'; msg.className = 'error'; btn.disabled = false; btn.textContent = 'Create User'; }
}

var _pendingAction = null;
function _showConfirmBar(title, desc, confirmLabel) {
  document.getElementById('mgu-confirm-title').textContent = title;
  document.getElementById('mgu-confirm-desc').textContent = desc;
  document.getElementById('mgu-confirm-bar').querySelector('.mgu-confirm-yes').textContent = confirmLabel;
  var bar = document.getElementById('mgu-confirm-bar');
  bar.classList.add('show'); bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function mguResetPassword(userId, email) { document.getElementById('mgu-reset-pwd-box').classList.remove('show'); _pendingAction = { type: 'reset', userId: userId, email: email }; _showConfirmBar('Reset password for this user?', email + ' will receive a new generated password.', 'Yes, Reset'); }
function mguDeleteUser(userId, email) { document.getElementById('mgu-reset-pwd-box').classList.remove('show'); _pendingAction = { type: 'delete', userId: userId, email: email }; _showConfirmBar('Permanently delete this user?', email + ' will be removed and cannot be recovered.', 'Yes, Delete'); }
function cancelMguConfirm() { _pendingAction = null; document.getElementById('mgu-confirm-bar').classList.remove('show'); }
async function executeMguConfirm() {
  if (!_pendingAction) return;
  var type = _pendingAction.type, userId = _pendingAction.userId, email = _pendingAction.email;
  _pendingAction = null;
  document.getElementById('mgu-confirm-bar').classList.remove('show');
  if (type === 'reset') {
    try {
      var res = await fetch('/api/admin/users/' + userId + '/reset-password', { method: 'POST', headers: { 'Authorization': 'Bearer ' + _adminToken() } });
      var data = await res.json();
      if (!res.ok) { var msg = document.getElementById('mgusers-msg'); msg.textContent = data.detail || 'Failed to reset password.'; msg.className = 'error'; }
      else { document.getElementById('mgu-reset-email').textContent = email; document.getElementById('mgu-reset-pwd-text').textContent = data.generated_password; document.getElementById('mgu-reset-pwd-box').classList.add('show'); document.getElementById('mgu-reset-pwd-box').scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
    } catch (e) { var msg = document.getElementById('mgusers-msg'); msg.textContent = 'Network error.'; msg.className = 'error'; }
  } else if (type === 'delete') {
    try {
      var res = await fetch('/api/admin/users/' + userId, { method: 'DELETE', headers: { 'Authorization': 'Bearer ' + _adminToken() } });
      if (!res.ok) { var data = await res.json(); var msg = document.getElementById('mgusers-msg'); msg.textContent = data.detail || 'Failed to delete user.'; msg.className = 'error'; }
      else { await loadUsersList(); }
    } catch (e) { var msg = document.getElementById('mgusers-msg'); msg.textContent = 'Network error.'; msg.className = 'error'; }
  }
}
async function mguToggleActive(userId, currentlyActive) {
  try {
    var res = await fetch('/api/admin/users/' + userId, { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() }, body: JSON.stringify({ is_active: !currentlyActive }) });
    if (!res.ok) throw new Error();
    await loadUsersList();
  } catch (e) { var msg = document.getElementById('mgusers-msg'); msg.textContent = 'Failed to update user status.'; msg.className = 'error'; }
}
function copyMguPwd(spanId, btn) {
  var text = document.getElementById(spanId).textContent;
  navigator.clipboard.writeText(text).then(function () { btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = 'Copy'; }, 2000); });
}

async function openEditUser(userId, email, role, orgId) {
  _editUserId = userId;
  document.getElementById('mgu-edit-email-label').textContent = email;
  document.getElementById('mgu-edit-role').value = role;
  await loadOrgsIntoSelect('mgu-edit-org');
  document.getElementById('mgu-edit-org').value = String(orgId || 0);
  var bar = document.getElementById('mgu-edit-bar');
  bar.style.display = 'block'; bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
async function submitEditUser() {
  if (!_editUserId) return;
  var role = document.getElementById('mgu-edit-role').value;
  var orgRaw = parseInt(document.getElementById('mgu-edit-org').value, 10) || 0;
  var msg = document.getElementById('mgusers-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  try {
    var res = await fetch('/api/admin/users/' + _editUserId, { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() }, body: JSON.stringify({ role: role, organization_id: orgRaw }) });
    if (!res.ok) { var data = await res.json(); msg.textContent = data.detail || 'Failed to update user.'; msg.className = 'error'; msg.style.display = 'block'; }
    else { closeEditUser(); await loadUsersList(); }
  } catch (e) { msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block'; }
}
function closeEditUser() { _editUserId = null; document.getElementById('mgu-edit-bar').style.display = 'none'; }

async function loadOrgsIntoSelect(selectId) {
  var sel = document.getElementById(selectId);
  if (!sel) return;
  if (_orgsCache.length === 0) {
    try { var res = await fetch('/api/organizations/', { headers: { 'Authorization': 'Bearer ' + _adminToken() } }); if (res.ok) _orgsCache = await res.json(); } catch (e) {}
  }
  sel.innerHTML = '<option value="0">\u2014 None \u2014</option>';
  _orgsCache.forEach(function (o) { var opt = document.createElement('option'); opt.value = o.id; opt.textContent = o.name; sel.appendChild(opt); });
}

/* ── Manage Organizations (admin only) ───────────────────────────────────── */
async function openManageOrgs() {
  _closeUserMenus();
  _orgsCache = [];
  document.getElementById('mgorgs-add-form').style.display = 'none';
  document.getElementById('mgorgs-edit-bar').style.display = 'none';
  _editOrgId = null;
  var msg = document.getElementById('mgorgs-msg');
  msg.className = ''; msg.textContent = ''; msg.style.display = 'none';
  document.getElementById('mgorgs-overlay').style.display = 'flex';
  await loadOrgsList();
}
function closeManageOrgs() { document.getElementById('mgorgs-overlay').style.display = 'none'; _editOrgId = null; }
function handleMgorgsOverlayClick(e) { if (e.target === document.getElementById('mgorgs-overlay')) closeManageOrgs(); }
async function loadOrgsList() {
  var loading = document.getElementById('mgorgs-loading');
  var table = document.getElementById('mgorgs-table');
  var tbody = document.getElementById('mgorgs-tbody');
  loading.style.display = 'block'; loading.textContent = 'Loading organizations\u2026';
  table.style.display = 'none';
  try {
    var res = await fetch('/api/organizations/?active_only=false', { headers: { 'Authorization': 'Bearer ' + _adminToken() } });
    if (!res.ok) throw new Error('Failed to load orgs');
    var data = await res.json();
    var orgs = Array.isArray(data) ? data : (data.organizations || []);
    _orgsCache = orgs.filter(function (o) { return o.is_active !== false; });
    tbody.innerHTML = '';
    orgs.forEach(function (o) {
      var statusHtml = o.is_active !== false ? '<span class="mgu-status-active">\u25cf Active</span>' : '<span class="mgu-status-inactive">\u25cf Inactive</span>';
      var toggleLabel = o.is_active !== false ? 'Deactivate' : 'Activate';
      var toggleClass = o.is_active !== false ? 'danger' : 'success';
      tbody.innerHTML += '<tr><td style="font-weight:600;color:#e2e8f0">' + _esc(o.name) + '</td><td style="color:#64748b;font-family:monospace;font-size:12px">' + _esc(o.slug || '') + '</td><td style="color:#94a3b8">' + _esc(o.description || '\u2014') + '</td><td>' + statusHtml + '</td><td><button class="mgu-action-btn" onclick="openEditOrg(' + o.id + ', \'' + _esc(o.name) + '\', \'' + _esc(o.description || '') + '\')">Edit</button><button class="mgu-action-btn ' + toggleClass + '" onclick="mguToggleOrgActive(' + o.id + ', ' + (o.is_active !== false) + ')">' + toggleLabel + '</button></td></tr>';
    });
    loading.style.display = 'none'; table.style.display = 'table';
  } catch (e) { loading.textContent = 'Failed to load organizations.'; }
}
function toggleAddOrgForm() {
  var form = document.getElementById('mgorgs-add-form');
  var isOpen = form.style.display === 'block';
  form.style.display = isOpen ? 'none' : 'block';
  if (!isOpen) { document.getElementById('mgorgs-new-name').value = ''; document.getElementById('mgorgs-new-desc').value = ''; document.getElementById('mgorgs-submit-btn').disabled = false; document.getElementById('mgorgs-submit-btn').textContent = 'Create'; setTimeout(function () { document.getElementById('mgorgs-new-name').focus(); }, 80); }
}
async function submitAddOrg() {
  var name = document.getElementById('mgorgs-new-name').value.trim();
  var desc = document.getElementById('mgorgs-new-desc').value.trim();
  var btn = document.getElementById('mgorgs-submit-btn');
  var msg = document.getElementById('mgorgs-msg');
  if (!name) { msg.textContent = 'Organization name is required.'; msg.className = 'error'; msg.style.display = 'block'; return; }
  btn.disabled = true; btn.textContent = 'Creating\u2026';
  msg.style.display = 'none';
  try {
    var res = await fetch('/api/organizations/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() }, body: JSON.stringify({ name: name, description: desc || null }) });
    var data = await res.json();
    if (!res.ok) { msg.textContent = data.detail || 'Failed to create organization.'; msg.className = 'error'; msg.style.display = 'block'; btn.disabled = false; btn.textContent = 'Create'; }
    else { toggleAddOrgForm(); _orgsCache = []; await loadOrgsList(); }
  } catch (e) { msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block'; btn.disabled = false; btn.textContent = 'Create'; }
}
function openEditOrg(orgId, name, desc) { _editOrgId = orgId; document.getElementById('mgorgs-edit-name').value = name; document.getElementById('mgorgs-edit-desc').value = desc; var bar = document.getElementById('mgorgs-edit-bar'); bar.style.display = 'block'; bar.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
async function submitEditOrg() {
  if (!_editOrgId) return;
  var name = document.getElementById('mgorgs-edit-name').value.trim();
  var desc = document.getElementById('mgorgs-edit-desc').value.trim();
  var msg = document.getElementById('mgorgs-msg');
  if (!name) { msg.textContent = 'Organization name is required.'; msg.className = 'error'; msg.style.display = 'block'; return; }
  msg.style.display = 'none';
  try {
    var res = await fetch('/api/organizations/' + _editOrgId, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() }, body: JSON.stringify({ name: name, description: desc || null }) });
    var data = await res.json();
    if (!res.ok) { msg.textContent = data.detail || 'Failed to update organization.'; msg.className = 'error'; msg.style.display = 'block'; }
    else { closeEditOrg(); _orgsCache = []; await loadOrgsList(); }
  } catch (e) { msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block'; }
}
function closeEditOrg() { _editOrgId = null; document.getElementById('mgorgs-edit-bar').style.display = 'none'; }
async function mguToggleOrgActive(orgId, currentlyActive) {
  var msg = document.getElementById('mgorgs-msg'); msg.style.display = 'none';
  try {
    var res = await fetch('/api/organizations/' + orgId, { method: 'PUT', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _adminToken() }, body: JSON.stringify({ is_active: !currentlyActive }) });
    if (!res.ok) { var data = await res.json(); msg.textContent = data.detail || 'Failed to update organization.'; msg.className = 'error'; msg.style.display = 'block'; }
    else { _orgsCache = []; await loadOrgsList(); }
  } catch (e) { msg.textContent = 'Network error.'; msg.className = 'error'; msg.style.display = 'block'; }
}
function _esc(str) { return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function _decodeToken(token) {
  try { var base64 = token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/'); return JSON.parse(decodeURIComponent(atob(base64).split('').map(function (c) { return '%' + ('00'+c.charCodeAt(0).toString(16)).slice(-2); }).join(''))); }
  catch (e) { return null; }
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
