# Build stage - Angular production build
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source files
COPY . .

# Build Angular app for production with custom output path
RUN npm run build:prod -- --output-path dist/chmusicproweb

# Production stage - Nginx with built Angular app
FROM nginx:1.26-alpine AS production

# Copy built Angular app
COPY --from=builder /app/dist/chmusicproweb/browser /usr/share/nginx/html/chmusicproweb/browser

# Expose ports
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
  CMD wget -q --spider http://localhost/nginx_status || exit 1

CMD ["nginx", "-g", "daemon off;"]
