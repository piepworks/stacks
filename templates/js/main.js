document.body.removeEventListener('keyup', window.bsKeyupSlash);
window.bsKeyupSlash = (e) => {
  if (e.code === 'Slash') {
    const searchForm = document.querySelector('.search-form form input');
    searchForm.focus();
  }
};
document.body.addEventListener('keyup', window.bsKeyupSlash);
