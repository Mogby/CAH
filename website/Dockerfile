FROM nginx

COPY nginx.conf /etc/nginx/nginx.conf

COPY . /usr/share/nginx/html

RUN chown -R 101:101 /usr/share/nginx/html
