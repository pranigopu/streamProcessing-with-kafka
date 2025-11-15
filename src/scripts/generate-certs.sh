#!/bin/bash

set -e

# Use /certs as the base directory (mounted from host)
CERT_DIR="/certs"
VALIDITY_DAYS=365
KEYSTORE_PASSWORD="kafka-keystore-pass"
TRUSTSTORE_PASSWORD="kafka-truststore-pass"
CA_PASSWORD="kafka-ca-pass"

# Create directory structure
mkdir -p ${CERT_DIR}/{ca,kafka,clients,credentials}

# ... rest of your cert generation script ...

# Create credential files
echo "${KEYSTORE_PASSWORD}" > ${CERT_DIR}/credentials/keystore_creds
echo "${KEYSTORE_PASSWORD}" > ${CERT_DIR}/credentials/key_creds
echo "${TRUSTSTORE_PASSWORD}" > ${CERT_DIR}/credentials/truststore_creds

echo "==== Certificate generation complete ===="