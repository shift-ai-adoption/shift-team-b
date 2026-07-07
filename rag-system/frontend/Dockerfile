# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build

# --- serve stage ---
FROM nginx:alpine
RUN apk add --no-cache openssl && \
    printf "admin:%s\n" "$(openssl passwd -apr1 'admin123!')" > /etc/nginx/.htpasswd
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
