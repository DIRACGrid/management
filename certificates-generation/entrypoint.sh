#!/bin/bash

### CA

echo "Generating DIRAC server certificate"
if ! openssl genrsa -out /ca/certs/hostkey.pem 2048; then
    echo "Failed to generate DIRAC server private key"
    exit 1
fi
chmod 400 hostkey.pem

### DIRAC Server

if ! openssl req -config /ca/openssl_config_host.cnf \
                 -new \
                 -sha256 \
                 -key /ca/certs/hostkey.pem \
                 -out /ca/requests/server.csr; then
    echo "Failed to generate  DIRAC server certificate signing request"
    exit 1
fi
if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -batch \
                -days 15 \
                -in /ca/requests/server.csr \
                -extensions server_cert \
                -out /ca/certs/hostcert.pem; then
    echo "Failed to generate DIRAC server certificate"
    exit 1
fi

### DIRAC User ciuser

if ! openssl genrsa -out /ca/certs/client.key 2048; then
    echo "Failed to generate ciuser private key"
    exit 1
fi
chmod 400 client.key

if ! openssl req -config /ca/openssl_config_user.cnf \
                 -key /ca/certs/client.key \
                 -new \
                 -out /ca/requests/client.req; then
    echo "Failed to generate ciuser certificate signing request"
    exit 1
fi

if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -extensions usr_cert \
                -batch \
                -days 15 \
                -in /ca/requests/client.req \
                -out /ca/certs/client.pem; then
    echo "Failed to generate ciuser certificate"
    exit 1
fi

### DIRAC User adminusername

if ! openssl genrsa -out /ca/certs/client.key 2048; then
    echo "Failed to generate adminusername private key"
    exit 1
fi
chmod 400 client.key

if ! openssl req -config /ca/openssl_config_user.cnf \
                 -key /ca/certs/client.key \
                 -new \
                 -out /ca/requests/client.req; then
    echo "Failed to generate adminusername certificate signing request"
    exit 1
fi

if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -extensions usr_cert \
                -batch \
                -days 15 \
                -in /ca/requests/client.req \
                -out /ca/certs/client.pem; then
    echo "Failed to generate adminusername certificate"
    exit 1
fi

### DIRAC Pilot

if ! openssl genrsa -out /ca/certs/pilot.key 2048; then
    echo "Failed to generate pilot private key"
    exit 1
fi
chmod 400 pilot.key

if ! openssl req -config /ca/openssl_config_pilot.cnf \
                 -key /ca/certs/pilot.key \
                 -new \
                 -out /ca/requests/pilot.req; then
    echo "Failed to generate pilot certificate signing request"
    exit 1
fi

if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -extensions usr_cert \
                -batch \
                -days 15 \
                -in /ca/requests/pilot.req \
                -out /ca/certs/pilot.pem; then
    echo "Failed to generate pilot certificate"
    exit 1
fi

###

echo "DIRAC Certificates generated and available in /ca/certs"

if ! chmod -R o=u /ca/certs; then
    echo "Failed to set read permissions on /ca/certs"
    exit 1
fi

exit 0
