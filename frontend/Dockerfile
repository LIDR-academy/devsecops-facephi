# ==============================================================================
# Stage 1: Builder — install deps and build the React production bundle
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy manifests first for layer-caching
COPY package*.json ./

RUN npm ci

# Copy all source files
COPY public ./public/
COPY src ./src/
COPY tsconfig.json ./

# REACT_APP_API_URL is baked into the JS bundle at build time.
# Default is empty string so nginx proxies API calls from the same origin.
ARG REACT_APP_API_URL=""
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Disable the CRA interactive prompt in CI environments
ENV CI=true

RUN npm run build

# ==============================================================================
# Stage 2: Production — serve the static bundle with Nginx
# ==============================================================================
FROM nginx:1.27-alpine AS production

# Remove the default Nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy the React production build from the builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Nginx on Alpine already runs as the "nginx" user (non-root).
# The default nginx.conf in Alpine starts the master process as root to bind port 80
# but worker processes run as "nginx". For fully non-root operation port must be > 1024.
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
