document.body.removeEventListener('keyup', window.bsKeyupSlash);
document.body.removeEventListener('keyup', window.bsKeyupNew);
window.bsKeyupSlash = (e) => {
  if (
    e.code === 'Slash' &&
    document.activeElement.tagName !== 'INPUT' &&
    document.activeElement.tagName !== 'SELECT' &&
    document.activeElement.tagName !== 'TEXTAREA'
  ) {
    const searchForm = document.querySelector('.search-form form input');
    searchForm.focus();
  }
};
window.bsKeyupNew = (e) => {
  if (
    e.code === 'KeyN' &&
    document.activeElement.tagName !== 'INPUT' &&
    document.activeElement.tagName !== 'SELECT' &&
    document.activeElement.tagName !== 'TEXTAREA' &&
    document.getElementById('addBook')
  ) {
    document.getElementById('addBook').showModal();
  }
};
document.body.addEventListener('keyup', window.bsKeyupSlash);
document.body.addEventListener('keyup', window.bsKeyupNew);

// Show a badge on the changelog nav if there's something new
const changelogId = localStorage.getItem('changelogId');

fetch(`{% url 'changelog_latest' %}`, {
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
})
  .then((response) => response.json())
  .then((data) => {
    const latestId = data.id;
    if (changelogId < latestId) {
      const changelogBadge = document.querySelector('.changelog-badge');
      changelogBadge.classList.remove('hidden');
    }
  });

// {% if request.resolver_match and request.resolver_match.view_name == 'status' %}
window.bsResetFilters = (e) => {
  const filters = document
    .getElementById('filters')
    .querySelectorAll('input[type=radio]');
  filters.forEach((input) => {
    input.checked = false;
  });
  filters.forEach((input) => {
    if (input.value === 'all') {
      input.checked = true;
    }
  });
};
// {% endif %}

// On browser forward or back
window.onpageshow = (e) => {
  if (e.persisted) {
    let button = document.querySelector('#openLibraryForm button');
    if (button) {
      button.classList.toggle('loading');
    }
  }
};

// Offline notification
window.addEventListener('load', () => {
  function handleNetworkChange(event) {
    if (navigator.onLine) {
      document.body.classList.remove('offline');
      console.log('You’re ONline!');
    } else {
      document.body.classList.add('offline');
      console.log('You’re OFFline!');
    }
  }
  window.addEventListener('online', handleNetworkChange);
  window.addEventListener('offline', handleNetworkChange);
});
