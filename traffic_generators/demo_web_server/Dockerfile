FROM node:alpine

COPY aviserver /
COPY customizer.sh /

CMD sh customizer.sh && node webserver.js