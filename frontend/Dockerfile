# Stage 1: Build
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency configs
COPY package*.json ./

# Install packages
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Nginx server
FROM nginx:alpine

# Copy built outputs
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom Nginx proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
