# Multi-stage build for Angular app
FROM node:20-alpine AS builder

# Create non-root user for build
RUN addgroup -g 1001 -S nodejs && adduser -S angular -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY bun.lock ./

# Install dependencies (including dev dependencies needed for build)
RUN npm ci --no-audit

# Copy source code and change ownership
COPY --chown=angular:nodejs . .

# Change ownership of the entire app directory to angular user
RUN chown -R angular:nodejs /app

# Switch to non-root user for build
USER angular

# Build the Angular app for production
RUN npm run build -- --configuration=production

# Production stage with Nginx
FROM nginx:alpine

# Install security updates
RUN apk update && apk upgrade && apk add --no-cache ca-certificates

# Create non-root user for nginx
RUN addgroup -g 1001 -S nginx-app && adduser -S nginx-app -u 1001 -G nginx-app

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built Angular app from builder stage (browser subdirectory contains the actual files)
COPY --from=builder --chown=nginx-app:nginx-app /app/dist/company-portal/browser /usr/share/nginx/html

# Copy environment setup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown nginx-app:nginx-app /docker-entrypoint.sh

# Create necessary directories with correct permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /tmp && \
    chown -R nginx-app:nginx-app /var/cache/nginx /var/log/nginx /tmp /usr/share/nginx/html && \
    chmod 755 /tmp

# Switch to non-root user
USER nginx-app

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Use custom entrypoint for environment variable injection
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
