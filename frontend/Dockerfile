# Stage 1: build React app
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Use relative API path so nginx can proxy /api/ to backend
RUN VITE_API_BASE=/api/v1 npm run build

# Stage 2: serve with nginx
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Remove the default nginx config that binds to port 80
RUN rm -f /etc/nginx/conf.d/default.conf.bak
EXPOSE 3000
