"""Create (once) and reuse a self-signed certificate for the callback server.

The Gira X1 documentation explicitly states that HTTPS connections in this
ecosystem cannot use a trusted certificate ("it is not technically possible
that the server provides a trusted TLS certificate"), and that clients must
skip certificate validation. We rely on the same tolerance holding for the
reverse direction (X1 -> our callback server); a self-signed certificate is
therefore sufficient here.
"""
from __future__ import annotations

import datetime
import os


def ensure_certificate(cert_path: str, key_path: str) -> None:
    """Generate a self-signed cert/key pair if it doesn't exist yet."""
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return

    # Imported lazily: 'cryptography' ships with Home Assistant core already.
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    os.makedirs(os.path.dirname(cert_path), exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "homeassistant-gira-x1-callback")]
    )
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(days=1))
        .not_valid_after(now + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("homeassistant-gira-x1-callback")]
            ),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with open(key_path, "wb") as handle:
        handle.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(cert_path, "wb") as handle:
        handle.write(cert.public_bytes(serialization.Encoding.PEM))
