FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /code

WORKDIR /code

# install stuff
RUN apt-get update && \
    apt-get install -y git && \
    apt-get remove nodejs npm && \
    apt-get install -y curl && \
    apt-get install -y ca-certificates curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install Litestream
RUN wget https://github.com/benbjohnson/litestream/releases/download/v0.3.13/litestream-v0.3.13-linux-amd64.deb \
    && dpkg -i litestream-v0.3.13-linux-amd64.deb

# Install cron and SQLite
RUN apt-get install -y cron && \
    apt-get install -y sqlite3

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

COPY pyproject.toml /tmp/pyproject.toml

RUN set -ex && \
    pip install --upgrade pip && \
    pip install uv && \
    uv pip install -r /tmp/pyproject.toml --system && \
    rm -rf /root/.cache/

COPY . /code/

EXPOSE 8000

RUN npm i && npm run build

CMD ["/code/fly/start.sh"]
