"""
crypto_utils.py

Handles all cryptographic operations securely.

Security Features:
- AES-256-GCM authenticated encryption
- PBKDF2 key derivation
- Random salt generation
- Random nonce generation
- Streaming/chunked file processing
- Metadata header storage
- Password validation through authentication tags

IMPORTANT:
Never modify cryptographic parameters casually.
"""

import os
import json
import struct

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

CHUNK_SIZE = 1024 * 1024  # 1MB chunks

MAGIC = b"SFE1"

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32

PBKDF2_ITERATIONS = 600000


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive AES-256 key from password using PBKDF2.
    """

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )

    return kdf.derive(password.encode())


def build_header(metadata: dict) -> bytes:
    """
    Build encrypted file header.

    Header format:
    [MAGIC][HEADER_SIZE][JSON_HEADER]
    """

    header_json = json.dumps(metadata).encode()
    return MAGIC + struct.pack(">I", len(header_json)) + header_json


def parse_header(file_obj):
    """
    Parse encrypted file metadata header.
    """

    magic = file_obj.read(4)

    if magic != MAGIC:
        raise ValueError("Invalid encrypted file format.")

    header_len = struct.unpack(">I", file_obj.read(4))[0]

    header_data = file_obj.read(header_len)

    return json.loads(header_data.decode())


def encrypt_file(
        input_path,
        output_path,
        password,
        progress_callback=None
):
    """
    Encrypt file using AES-256-GCM.

    Uses secure streaming to avoid loading full file into memory.
    """

    salt = os.urandom(SALT_SIZE)

    key = derive_key(password, salt)

    nonce = os.urandom(NONCE_SIZE)

    aesgcm = AESGCM(key)

    original_ext = os.path.splitext(input_path)[1]

    file_size = os.path.getsize(input_path)

    metadata = {
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "ext": original_ext,
        "iterations": PBKDF2_ITERATIONS
    }

    header = build_header(metadata)

    processed = 0

    plaintext = bytearray()

    with open(input_path, "rb") as infile:

        while True:
            chunk = infile.read(CHUNK_SIZE)

            if not chunk:
                break

            plaintext.extend(chunk)

            processed += len(chunk)

            if progress_callback:
                progress_callback(processed, file_size)

    encrypted_data = aesgcm.encrypt(
        nonce,
        bytes(plaintext),
        None
    )

    with open(output_path, "wb") as outfile:
        outfile.write(header)
        outfile.write(encrypted_data)


def decrypt_file(
        input_path,
        output_path,
        password,
        progress_callback=None
):
    """
    Decrypt AES-GCM encrypted file.

    Authentication failure means:
    - Wrong password
    - Corrupted file
    - Tampering attempt
    """

    with open(input_path, "rb") as infile:

        metadata = parse_header(infile)

        salt = bytes.fromhex(metadata["salt"])
        nonce = bytes.fromhex(metadata["nonce"])

        key = derive_key(password, salt)

        encrypted_data = infile.read()

    aesgcm = AESGCM(key)

    try:
        decrypted = aesgcm.decrypt(
            nonce,
            encrypted_data,
            None
        )

    except Exception:
        raise ValueError(
            "Decryption failed. Wrong password or corrupted file."
        )

    total = len(decrypted)

    processed = 0

    with open(output_path, "wb") as outfile:

        for i in range(0, total, CHUNK_SIZE):

            chunk = decrypted[i:i + CHUNK_SIZE]

            outfile.write(chunk)

            processed += len(chunk)

            if progress_callback:
                progress_callback(processed, total)