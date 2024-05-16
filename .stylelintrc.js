module.exports = {
  extends: 'stylelint-config-standard',
  rules: {
    'declaration-empty-line-before': 'never',
    'no-descending-specificity': null,
    'media-feature-range-notation': null,
    'function-no-unknown': [true, { ignoreFunctions: ['theme'] }],
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen',
        ],
      },
    ],
  },
  ignoreFiles: ['static_src/css/vendor/**'],
};
