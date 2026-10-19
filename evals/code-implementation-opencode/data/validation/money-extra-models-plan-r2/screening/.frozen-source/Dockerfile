FROM node:24.9.0-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/*
RUN npm install --global typescript@5.9.3 && npm cache clean --force
WORKDIR /workspace
CMD ["sleep", "infinity"]
