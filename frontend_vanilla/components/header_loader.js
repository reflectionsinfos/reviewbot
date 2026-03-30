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

      updateSharedUserInfo();
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

  return {
    email: payload.sub || payload.email || payload.preferred_username || payload.username || '',
    name: payload.full_name || payload.name || '',
    role: payload.role || payload.user_role || 'user'
  };
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
    tokenUserInfo = extractUserInfo(decodeJwtPayload(tok));
  } catch (e) {
    console.error('Error parsing token for header info:', e);
  }

  if (tokenUserInfo && (tokenUserInfo.name || tokenUserInfo.email)) {
    applySharedUserInfo(tokenUserInfo);
  } else {
    resetSharedUserInfo();
  }

  if (tokenUserInfo && tokenUserInfo.name) {
    return;
  }

  try {
    const currentUser = await fetchCurrentUser(tok);
    if (!currentUser.name && !currentUser.email) return;
    applySharedUserInfo(currentUser);
  } catch (e) {
    console.error('Error loading current user for header info:', e);
  }
}

window.updateSharedUserInfo = updateSharedUserInfo;
