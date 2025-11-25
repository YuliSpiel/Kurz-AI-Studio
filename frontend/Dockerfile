# Frontend Dockerfile - Multi-stage build for Railway
FROM node:20-alpine AS builder

WORKDIR /app

# API URL is set via Railway environment variable at build time
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY . .

# Build (uses VITE_API_URL from env)
RUN npx tsc -b && npx vite build

# Production stage with nginx
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Railway uses PORT env variable (defaults to 8080)
ARG PORT=8080
EXPOSE ${PORT}

CMD ["nginx", "-g", "daemon off;"]
