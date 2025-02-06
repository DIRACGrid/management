FROM debian:latest

# Install necessary packages
RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# Create necessary CA directories
RUN mkdir -p /ca/certs && \
    mkdir -p /ca/private && \
    mkdir -p /ca/newcerts && \
    mkdir -p /ca/crl && \
    mkdir -p /ca/requests
RUN chmod 700 /ca/private && \
    touch /ca/index.txt && \
    echo 1000 > /ca/serial && \
    echo 1000 > /ca/crlnumber

# Copy OpenSSL config file
COPY openssl_config_ca.cnf /ca/openssl_config_ca.cnf
COPY openssl_config_host.cnf /ca/openssl_config_host.cnf
COPY openssl_config_user.cnf /ca/openssl_config_user.cnf

# Generate CA private key and certificate
RUN openssl genrsa -out /ca/private/ca.key 2048
RUN openssl req -config /ca/openssl_config_ca.cnf -x509 -new -nodes -key /ca/private/ca.key -sha256 -days 365 -extensions v3_ca -out /ca/certs/ca.cert.pem

# Entry point script to generate certs on startup
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
