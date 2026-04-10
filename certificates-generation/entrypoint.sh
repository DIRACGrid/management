#!/bin/bash

### CA

echo "Generating DIRAC server certificate"
if ! openssl genrsa -out /ca/certs/hostkey.pem 2048; then
    echo "Failed to generate DIRAC server private key"
    exit 1
fi
chmod 400 /ca/certs/hostkey.pem

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

echo "Generating DIRAC user ciuser"
if ! openssl genrsa -out /ca/certs/client.key 2048; then
    echo "Failed to generate ciuser private key"
    exit 1
fi
chmod 400 /ca/certs/client.key

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

echo "Generating DIRAC user adminusername"
if ! openssl genrsa -out /ca/certs/adminusername.key 2048; then
    echo "Failed to generate adminusername private key"
    exit 1
fi
chmod 400 /ca/certs/adminusername.key

if ! openssl req -config /ca/openssl_config_adminusername.cnf \
                 -key /ca/certs/adminusername.key \
                 -new \
                 -out /ca/requests/adminusername.req; then
    echo "Failed to generate adminusername certificate signing request"
    exit 1
fi

if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -extensions usr_cert \
                -batch \
                -days 15 \
                -in /ca/requests/adminusername.req \
                -out /ca/certs/adminusername.pem; then
    echo "Failed to generate adminusername certificate"
    exit 1
fi

### DIRAC Pilot

echo "Generating DIRAC pilot cert"
if ! openssl genrsa -out /ca/certs/pilot.key 2048; then
    echo "Failed to generate pilot private key"
    exit 1
fi
chmod 400 /ca/certs/pilot.key

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

echo "Generating Certificate Revocation List (CRL)"
if ! openssl ca -config /ca/openssl_config_ca.cnf \
                -gencrl \
                -out /ca/crl/ca.crl.pem; then
    echo "Failed to generate CRL"
    exit 1
fi

echo "Converting CRL to DER format"
if ! openssl crl -in /ca/crl/ca.crl.pem \
                 -outform DER \
                 -out /ca/crl/ca.crl.der; then
    echo "Failed to convert CRL to DER format"
    exit 1
fi

# Copy CRL to certs directory for easy access
cp /ca/crl/ca.crl.pem /ca/certs/ca.crl.pem
cp /ca/crl/ca.crl.der /ca/certs/ca.crl.der

###

echo "DIRAC Certificates and CRL generated and available in /ca/certs"
ls -al --color /ca/certs

if ! chmod -R o=u /ca/certs; then
    echo "Failed to set read permissions on /ca/certs"
    exit 1
fi

exit 0
