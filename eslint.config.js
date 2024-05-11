module.exports = {
  languageOptions: {
    sourceType: 'module',
    ecmaVersion: 2022,
  },
  rules: {
    indent: ['error', 2],
    'linebreak-style': ['error', 'unix'],
    quotes: ['error', 'single', { allowTemplateLiterals: true }],
    semi: ['error', 'always'],
  },
};
