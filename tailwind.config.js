module.exports = {
  content: [
    '**/templates/**/*.{html,js,svg}',
    '**/core/templates/**/*.{html,js,svg}',
  ],
  theme: {
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        sm: '2rem',
      },
    },
  },
  plugins: [require('@tailwindcss/typography'), require('daisyui')],
};
