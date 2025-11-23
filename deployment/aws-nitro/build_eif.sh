#!/usr/bin/env bash
#
# Builds the Enclave Image File (EIF) for AWS Nitro Enclaves.
#
# This script builds a Docker image from the enclave Dockerfile and then
# provides instructions on how to convert it to an EIF using the nitro-cli.
#
# Usage:
#   ./build_eif.sh
#
set -euo pipefail
IMG=zk-autograd-prover-enclave:latest
EIF=zk-autograd-prover.eif

docker build -f enclave.Dockerfile -t $IMG ../..
echo "Built $IMG. Convert to EIF with nitro-cli:"
echo "  nitro-cli build-enclave --docker-uri $IMG --output-file $EIF"
