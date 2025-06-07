# Dockerfile for Vue 3 + Vite frontend
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f pnpm-lock.yaml ]; then npm install -g pnpm && pnpm install; \
    elif [ -f yarn.lock ]; then yarn install; \
    else npm install; fi
COPY src ./src
COPY public ./public
COPY vite.config.* ./
COPY tsconfig*.json ./
COPY index.html ./
RUN npm run build
FROM nginx:alpine AS production
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
