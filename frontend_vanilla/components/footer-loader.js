document.addEventListener('DOMContentLoaded', function () {
  var root = document.getElementById('shared-footer-root');

  if (!root) {
    return;
  }

  fetch('/frontend_vanilla/components/footer.html', { credentials: 'same-origin' })
    .then(function (response) {
      if (!response.ok) {
        throw new Error('Failed to load shared footer');
      }

      return response.text();
    })
    .then(function (html) {
      if (!root.isConnected) {
        return;
      }

      root.innerHTML = html;
    })
    .catch(function () {
      if (root && root.isConnected) {
        root.innerHTML = '';
      }
    });
});
