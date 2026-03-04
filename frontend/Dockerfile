# ─── Stage 1: Build ───────────────────────────────────────────────
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=""
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ─── Stage 2: Development ─────────────────────────────────────────
FROM node:18-alpine as development

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]

# ─── Stage 3: Production ──────────────────────────────────────────
FROM nginx:1.25-alpine as production

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.frontend.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
