# Dockerfile
FROM debian:bookworm-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/games:${PATH}"

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     bash \
     fortune-mod \
     fortunes \
     cowsay \
     netcat-openbsd \
     procps \
  && rm -rf /var/lib/apt/lists/*

COPY wisecow.sh /usr/local/bin/wisecow.sh
RUN chmod +x /usr/local/bin/wisecow.sh

EXPOSE 4499
CMD ["/usr/local/bin/wisecow.sh"]

