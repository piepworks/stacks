module.exports = {
  extends: 'stylelint-config-standard',
  rules: {
    'declaration-empty-line-before': 'never',
    'no-descending-specificity': null,
    'media-feature-range-notation': null,
  },
  ignoreFiles: ['static_src/css/vendor/**'],
};
