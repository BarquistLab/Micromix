# Build stage
FROM node:lts-alpine as build-stage

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

# Copy the plugins.json file into the container
COPY plugins.json ./

COPY frontend/ ./

RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
