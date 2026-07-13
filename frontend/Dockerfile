FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
# nginx.conf is mounted by docker-compose from docker/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
