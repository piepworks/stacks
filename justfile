default:
  @just --list

setup-venv:
  uv-sync

reset-venv:
  rm -rf .venv
  uv sync

bootstrap: setup-venv
  source ~/.nvm/nvm.sh
  npm install
  .venv/bin/python manage.py migrate
  .venv/bin/python manage.py createsuperuser
  pre-commit install

update-venv:
  just reset-venv

shell:
  .venv/bin/python manage.py shell

# Run all the tests (other than front-end Playwright) as fast as possible
pytest:
  pytest -n auto config/tests

playwright:
  npx playwright test

# Update all Python packages
update-packages:
  uv sync --upgrade

# Update a single package
update-a-package package:
  uv sync --upgrade-package {{ package }}

# Update Python and Node stuff
update: update-packages
  npm update
  npm outdated

build-static-files:
  .venv/bin/python manage.py collectstatic --noinput

generate-django-key:
  #!./.venv/bin/python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())

# Run the coverage report
coverage:
  .venv/bin/pytest -n auto --cov=core --cov-report=html

# Open the coverage report in Firefox
coverage-html:
  open -a firefox -g `pwd`/htmlcov/index.html

copy-npm-scripts:
  cp `pwd`/node_modules/htmx.org/dist/htmx.min.js `pwd`/static/js/vendor/htmx.min.js
  cp `pwd`/node_modules/htmx-ext-alpine-morph/alpine-morph.js `pwd`/static/js/vendor/htmx-alpine-morph.min.js
  cp `pwd`/node_modules/@alpinejs/sort/dist/cdn.min.js `pwd`/static/js/vendor/alpinejs-sort.min.js
  cp `pwd`/node_modules/@alpinejs/morph/dist/cdn.min.js `pwd`/static/js/vendor/alpinejs-morph.min.js
  cp `pwd`/node_modules/alpinejs/dist/cdn.min.js `pwd`/static/js/vendor/alpinejs.min.js

dev: copy-npm-scripts
  source .venv/bin/activate
  npm run dev

# Run Huey for long running tasks
huey:
  rm -f huey.*
  .venv/bin/python manage.py run_huey
