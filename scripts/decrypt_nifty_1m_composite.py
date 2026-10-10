#!/usr/bin/env python3
"""Decrypt the encrypted NIFTY one-minute CSV artifact for local/offline analysis.

Required: the same HF_TOKEN value used by the collection workflow. It is read
only from the environment or a hidden prompt; it is never written to disk.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import gzip
import hashlib
import json
import os
import pathlib
import shutil
import sys
from typing import Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
except ImportError as exc:
    raise SystemExit("Install the repository's requirements-composite.txt first.") from exc

MAGIC = b"N1C1"
AAD = b"Naked-option-v1:NIFTY-1m-composite:v1"
KEY_SALT = b"Naked-option-v1-HF-TOKEN-DERIVATION-v1"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_key(secret: str) -> bytes:
    if not isinstance(secret, str) or len(secret.strip()) < 16:
        raise ValueError("HF_TOKEN missing or too short.")
    return Scrypt(salt=KEY_SALT, length=32, n=2**14, r=8, p=1).derive(secret.encode("utf-8"))


def decrypt_bytes(encrypted: bytes, key: bytes) -> bytes:
    if len(encrypted) < 32 or not encrypted.startswith(MAGIC):
        raise ValueError("Encrypted file header is invalid.")
    nonce = encrypted[4:16]
    try:
        return AESGCM(key).decrypt(nonce, encrypted[16:], AAD)
    except Exception:
        raise ValueError("Decryption/authentication failed. Check that HF_TOKEN is the same token value used for collection.") from None


def read_manifest(input_dir: pathlib.Path) -> dict[str, Any]:
    path = input_dir / "dataset_manifest.json"
    if not path.is_file():
        raise FileNotFoundError("dataset_manifest.json not found in input directory.")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("parts"), list):
        raise ValueError("dataset manifest schema is invalid.")
    return obj


def decrypt_dataset(input_dir: pathlib.Path, output_dir: pathlib.Path, key: bytes,
                    overwrite: bool = False) -> list[pathlib.Path]:
    manifest = read_manifest(input_dir)
    if manifest.get("download_bundle_contains_encrypted_data_only") is not True:
        raise ValueError("Unexpected manifest scope: encrypted-only bundle marker missing.")
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[pathlib.Path] = []
    for part in manifest["parts"]:
        name = str(part.get("file", ""))
        if not name.endswith(".csv.gz.enc") or pathlib.Path(name).name != name:
            raise ValueError("Unsafe encrypted part filename in manifest.")
        encrypted_path = input_dir / name
        if not encrypted_path.is_file():
            raise FileNotFoundError(f"Encrypted part missing: {name}")
        if sha256(encrypted_path) != part.get("encrypted_sha256"):
            raise ValueError(f"Encrypted checksum mismatch: {name}")
        plaintext = decrypt_bytes(encrypted_path.read_bytes(), key)
        if hashlib.sha256(plaintext).hexdigest() != part.get("plain_gzip_sha256"):
            raise ValueError(f"Decrypted gzip checksum mismatch: {name}")
        output_name = name.removesuffix(".enc")
        output_path = output_dir / output_name
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"{output_path} exists; pass --overwrite to replace it.")
        output_path.write_bytes(plaintext)
        results.append(output_path)
    return results


def merge_month_parts(parts: list[pathlib.Path], output_path: pathlib.Path, overwrite: bool = False) -> int:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"{output_path} exists; pass --overwrite to replace it.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    try:
        with gzip.open(temporary, "wt", encoding="utf-8", newline="", compresslevel=6) as out_handle:
            writer = None
            for part in sorted(parts):
                with gzip.open(part, "rt", encoding="utf-8", newline="") as in_handle:
                    reader = csv.reader(in_handle)
                    try:
                        header = next(reader)
                    except StopIteration:
                        continue
                    if writer is None:
                        writer = csv.writer(out_handle)
                        writer.writerow(header)
                    elif header != writer_header:
                        raise ValueError(f"CSV schema mismatch in part: {part.name}")
                    if writer is None:
                        continue
                    writer_header = header
                    for row in reader:
                        writer.writerow(row)
                        row_count += 1
        temporary.replace(output_path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return row_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Decrypt the offline NIFTY 1-minute dataset bundle.")
    parser.add_argument("--input-dir", default=".", help="directory containing dataset_manifest.json and *.csv.gz.enc")
    parser.add_argument("--output-dir", default="nifty_1m_composite_plain", help="where decrypted monthly CSV.GZ parts are written")
    parser.add_argument("--merge-output", default="", help="optional path for one merged .csv.gz after monthly decryption")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output files")
    args = parser.parse_args()
    input_dir = pathlib.Path(args.input_dir).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()
    secret = os.environ.get("HF_TOKEN", "")
    if not secret:
        secret = getpass.getpass("Enter the same HF_TOKEN used when the bundle was collected: ")
    key = derive_key(secret)
    parts = decrypt_dataset(input_dir, output_dir, key, overwrite=args.overwrite)
    merged_rows = None
    if args.merge_output:
        merged_rows = merge_month_parts(parts, pathlib.Path(args.merge_output).resolve(), overwrite=args.overwrite)
    print(json.dumps({
        "decrypted_parts": len(parts),
        "output_dir": str(output_dir),
        "merged_output": str(pathlib.Path(args.merge_output).resolve()) if args.merge_output else None,
        "merged_data_rows": merged_rows,
        "source_artifact_plaintext_rows_were_never_published": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("DECRYPT_ERROR " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        raise SystemExit(1)
