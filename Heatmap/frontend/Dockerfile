# Build stage
FROM node:lts-alpine as build-stage

# Make /app the working directory
WORKDIR /app

# Copy packages.json and the lock file to the container
COPY frontend/package*.json ./

# Install npm dependencies from packages.json
RUN npm install

# Copy the frontend folder into the container
COPY frontend/ ./

# Build the site - creating a /dir directory containing the static files to use
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# Copy the static site
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]