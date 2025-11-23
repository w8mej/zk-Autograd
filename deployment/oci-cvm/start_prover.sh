#!/usr/bin/env bash
#
# Starts the Prover Service on OCI CVM.
#
# This script changes to the application directory and launches the
# FastAPI prover service using uvicorn.
#
# Usage:
#   ./start_prover.sh
#
set -euo pipefail
cd /opt/zk-autograd
uvicorn prover.service:app --host 0.0.0.0 --port 8000
