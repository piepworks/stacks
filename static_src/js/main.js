import 'vite/modulepreload-polyfill';
import htmx from 'htmx.org';
import './vendor/htmx-1.9.12-alpine-morph';

window.htmx = htmx;

console.log('Hello from main.js!');
