# ==============================================================================
# Stage 1: Builder — compile TypeScript and install all dependencies
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies needed to compile native addons (Prisma engine)
RUN apk add --no-cache openssl

# Copy manifests first for layer-caching
COPY package*.json ./
COPY prisma ./prisma/

# Install all deps (including devDependencies for the TS compiler and Prisma CLI)
RUN npm ci

# Generate Prisma client for the Alpine (musl) target
RUN npx prisma generate

# Copy source and config
COPY tsconfig.json ./
COPY src ./src/

# Compile TypeScript → dist/
RUN npm run build

# ==============================================================================
# Stage 2: Production — minimal runtime image
# ==============================================================================
FROM node:20-alpine AS production

# dumb-init: proper PID 1 signal handling, no zombie processes
RUN apk add --no-cache dumb-init openssl

WORKDIR /app

# Create uploads directory before switching to non-root user
RUN mkdir -p /app/uploads

# The "node" user (UID 1000) is pre-created in the official node image
# Copy application files with correct ownership
COPY --chown=node:node package*.json ./
COPY --chown=node:node prisma ./prisma/

# Install only production dependencies
RUN npm ci --omit=dev

# Prisma CLI is needed at runtime for `migrate deploy`.
# It is a devDependency so we copy the binary from the builder stage.
COPY --chown=node:node --from=builder /app/node_modules/.bin/prisma ./node_modules/.bin/prisma
COPY --chown=node:node --from=builder /app/node_modules/prisma ./node_modules/prisma

# Copy compiled application code
COPY --chown=node:node --from=builder /app/dist ./dist/

# Copy the pre-generated Prisma client artifacts
COPY --chown=node:node --from=builder /app/node_modules/.prisma ./node_modules/.prisma

# Ensure uploads directory is owned by the node user
RUN chown node:node /app/uploads

USER node

EXPOSE 8080

# Persist uploaded files across container restarts
VOLUME ["/app/uploads"]

ENTRYPOINT ["dumb-init", "--"]
# Migrations run before the app starts; handled via docker-compose command override
CMD ["node", "dist/index.js"]
