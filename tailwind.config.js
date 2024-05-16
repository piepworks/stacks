module.exports = {
  darkMode: 'class',
  content: [
    '**/templates/**/*.{html,js,svg}',
    '**/core/templates/**/*.{html,js,svg}',
  ],
  theme: {
    extend: {
      colors: {
        'pico-background-light': '#fff',
        'pico-background-dark': '#13171f',
      },
      screens: {
        tall: { raw: '(min-height: 450px)' },
      },
    },
  },
  plugins: [require('daisyui')],
};
