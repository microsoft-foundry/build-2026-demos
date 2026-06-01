FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

ENV GATEWAY_URL=https://fibey-apps-gateway.nicesmoke-dfb4fdf0.westus2.azurecontainerapps.io/api/
ENV GATEWAY_HOST=fibey-apps-gateway.nicesmoke-dfb4fdf0.westus2.azurecontainerapps.io

EXPOSE 80
