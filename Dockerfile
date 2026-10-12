FROM python:3.12.14-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f AS api-build
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends g++ ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --no-cache-dir cmake==4.4.3 ninja==1.13.2
COPY CMakeLists.txt ./
COPY simulator/ simulator/
RUN cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    && cmake --build build --parallel 2
COPY requirements.lock ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --require-hashes -r requirements.lock \
    && /opt/venv/bin/pip check

FROM python:3.12.14-slim-trixie@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f AS api
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home aerotest
WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY --from=api-build /opt/venv /opt/venv
COPY --from=api-build /app/build/aerotest-sim build/aerotest-sim
COPY backend/aerotest/ backend/aerotest/
RUN mkdir runtime && chown aerotest:aerotest runtime
USER aerotest
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "aerotest.app:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]

FROM node:25.0.0-bookworm-slim@sha256:cb4db5ec2a285632fbd8ff2fc2cc3c4cc393245b0e4d8419fc08909bf29c52ea AS web-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm test && npm run build

FROM nginx:1.30.5-alpine@sha256:0985e772fb9f729e6fa0980da05fca5d9c468e870eed43071545afa9d2e27d94 AS web
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /app/frontend/dist/ /usr/share/nginx/html/
EXPOSE 80
