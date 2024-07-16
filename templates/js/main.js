document.body.removeEventListener('keyup', window.bsKeyupSlash);
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
document.body.addEventListener('keyup', window.bsKeyupSlash);

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
