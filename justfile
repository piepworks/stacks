default:
  @just --list

setup-venv:
  python3 -m venv --prompt . .venv
  .venv/bin/pip install -U pip setuptools wheel
  .venv/bin/python -m pip install -r requirements/requirements.txt

reset-venv:
  rm -rf .venv
  just setup-venv

bootstrap: setup-venv
  source ~/.nvm/nvm.sh
  npm install
  .venv/bin/python manage.py migrate
  .venv/bin/python manage.py createsuperuser
  pre-commit install

update-venv:
  .venv/bin/pip-compile requirements/requirements.in
  .venv/bin/python -m pip install -r requirements/requirements.txt

shell:
  .venv/bin/python manage.py shell

# Run all the tests (other than front-end Playwright) as fast as possible
pytest:
  pytest -n auto config/tests

playwright:
  npx playwright test

# Update all Python packages
update-packages:
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/pip-compile --upgrade requirements/requirements.in
  .venv/bin/python -m pip install -r requirements/requirements.txt

# Update a single package
update-a-package package:
  .venv/bin/pip-compile -P {{ package }} requirements/requirements.in
  .venv/bin/python -m pip install -r requirements/requirements.txt

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
