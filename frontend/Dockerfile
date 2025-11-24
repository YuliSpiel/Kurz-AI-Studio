# Frontend Dockerfile - Multi-stage build for Cloud Run
FROM node:20-alpine AS builder

WORKDIR /app

# Hardcode API URL for production build
ENV VITE_API_URL=https://kurz-backend-233920104122.asia-northeast3.run.app

# Copy all files first
COPY . .

# Clean install and build using npx to avoid symlink issues
RUN rm -rf node_modules && npm install && npx tsc -b && npx vite build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Cloud Run uses port 8080
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
