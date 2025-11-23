"""anchor_service.py (outline)

Nitro-attested DynamoDB anchor gateway.

1) Verify Nitro attestation chain and PCR0/ImageSha384 allowlist.
2) Verify nonce freshness.
3) Conditional PutItem to DynamoDB.

See deployment/aws-nitro/README.md for flow.
"""
