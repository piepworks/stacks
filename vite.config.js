import { defineConfig, loadEnv } from 'vite';
import { resolve, join } from 'path';

export default defineConfig((mode) => {
  const env = loadEnv(mode, process.cwd(), '');

  const INPUT_DIR = './static_src';
  const OUTPUT_DIR = './static';

  return {
    plugins: [],
    resolve: {
      alias: {
        '@': resolve(INPUT_DIR),
      },
    },
    root: resolve(INPUT_DIR),
    base: '/static/',
    server: {
      host: env.DJANGO_VITE_DEV_SERVER_HOST,
      port: env.DJANGO_VITE_DEV_SERVER_PORT,
    },
    build: {
      outDir: resolve(OUTPUT_DIR),
      rollupOptions: {
        input: {
          main: join(INPUT_DIR, '/js/main.js'),
        },
        output: {
          entryFileNames: 'js/main.min.js',
        },
      },
    },
  };
});
