FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY public/html/index.html /usr/share/nginx/html/index.html
COPY public/html/download.html /usr/share/nginx/html/download.html
COPY public/css /usr/share/nginx/html/css
COPY public/js /usr/share/nginx/html/js
COPY public/img /usr/share/nginx/html/img
