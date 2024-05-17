module.exports = {
  content: [
    '**/templates/**/*.{html,js,svg}',
    '**/core/templates/**/*.{html,js,svg}',
  ],
  plugins: [require('@tailwindcss/typography'), require('daisyui')],
};
