---
id: docker
name: Docker Expert
category: deploying
level1: "For Dockerfiles, docker-compose, containers, images, and networking"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Docker Expert** — Activate for: Dockerfile authoring, docker-compose, container networking, volumes, image optimization, multi-stage builds.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Docker — Core Instructions

1. **Multi-stage builds** to keep production images small — build stage (with dev tools) → runtime stage (minimal).
2. **`.dockerignore` always** — exclude `node_modules`, `.git`, `.env`, build outputs.
3. **Pin base image versions** — `node:20-alpine` not `node:latest`. Reproducible builds.
4. **Non-root user in production** — `USER node` or create a dedicated user. Never run containers as root.
5. **Layer caching:** copy `package.json` + install deps BEFORE copying source code. Deps change less often.
6. **Healthchecks in compose** — `healthcheck` ensures dependent services wait for readiness, not just startup.
7. **Never bake secrets into images** — use environment variables or Docker secrets, not `ARG`/`ENV` for passwords.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Docker — Full Reference

### Optimised Dockerfile (Node.js)
```dockerfile
# Stage 1: build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: runtime (no dev tools, no npm)
FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder /app/node_modules ./node_modules
COPY . .
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "src/index.js"]
```

### docker-compose.yml Pattern
```yaml
version: '3.9'
services:
  app:
    build: .
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mydb
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Useful Commands
```bash
docker build -t myapp:latest .           # build image
docker run --rm -p 3000:3000 myapp       # run container
docker compose up -d                     # start all services
docker compose logs -f app               # stream logs
docker exec -it <container> sh           # shell into running container
docker system prune -af                  # clean up all unused resources
docker image ls                          # list local images
```

### .dockerignore
```
node_modules
.git
.env
*.log
dist
coverage
.DS_Store
```
<!-- LEVEL 3 END -->
