#!/usr/bin/env bash
#
# Runs the AWS Nitro Enclave.
#
# This script defines the EIF filename and prints the command to run the
# enclave using the nitro-cli.
#
# Usage:
#   ./run_enclave.sh
#
set -euo pipefail
EIF=zk-autograd-prover.eif
echo "Run enclave:"
echo "  nitro-cli run-enclave --eif-path $EIF --cpu-count 2 --memory 2048 --enclave-cid 16"
