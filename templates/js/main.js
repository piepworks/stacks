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
