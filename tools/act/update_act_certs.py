#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
import subprocess
import socket

# Default paths
CERT_DIR = "/server/ssl_certificates/certificates"
KEY_DIR = "/server/ssl_certificates/private_keys"
UPLOAD_DIR = "/server/uploads"

DEFAULT_CERT_NAME = "certificate.pem"
DEFAULT_KEY_NAME = "private-key.pem"

BACKUP_CERT_NAME = "certificate_default.pem"
BACKUP_KEY_NAME = "private-key_default.pem"

def move_with_optional_backup(src, dest, backup):
    if os.path.exists(dest):
        if not os.path.exists(backup):
            print(f"Backing up {dest} to {backup}")
            os.rename(dest, backup)
        else:
            print(f"Backup already exists at {backup}, skipping backup step.")
    else:
        print(f"WARNING: Destination {dest} not found to backup.")

    print(f"Replacing {dest} with {src}")
    shutil.copy2(src, dest)

def restore_default(cert_dest, key_dest, cert_backup, key_backup):
    if os.path.exists(cert_backup):
        print(f"Restoring {cert_backup} -> {cert_dest}")
        shutil.move(cert_backup, cert_dest)
    else:
        print(f"WARNING: Backup certificate not found at {cert_backup}")

    if os.path.exists(key_backup):
        print(f"Restoring {key_backup} -> {key_dest}")
        shutil.move(key_backup, key_dest)
    else:
        print(f"WARNING: Backup key not found at {key_backup}")

def restart_docker_container():
    print("\nAttempting to restart the container by signaling the main process...")
    try:
        command = ["kill", "1"]
        print(f"Executing command: {' '.join(command)} to trigger graceful shutdown.")
        subprocess.Popen(command)
        print("Restart signal sent. The container should restart shortly.")
    except FileNotFoundError:
        print("Error: 'kill' command not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during container restart: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    # Check if running inside the correct Docker container
    if socket.gethostname() != 'migrationTools':
        print("ERROR: This script must be run from inside the 'migrationTools' docker container.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Update or revert SSL/TLS certificates and restart the container."
    )
    parser.add_argument("--cert", help="Name of new certificate file (inside /server/uploads)")
    parser.add_argument("--key", help="Name of new private key file (inside /server/uploads)")
    parser.add_argument("--revert", action="store_true", help="Revert to default certificate and key")

    args = parser.parse_args()

    cert_dest = os.path.join(CERT_DIR, DEFAULT_CERT_NAME)
    key_dest = os.path.join(KEY_DIR, DEFAULT_KEY_NAME)

    cert_backup = os.path.join(CERT_DIR, BACKUP_CERT_NAME)
    key_backup = os.path.join(KEY_DIR, BACKUP_KEY_NAME)

    try:
        if args.revert:
            print("Reverting to default certificate and key...")
            restore_default(cert_dest, key_dest, cert_backup, key_backup)
        else:
            if not args.cert or not args.key:
                print("ERROR: --cert and --key are required unless --revert is used")
                sys.exit(1)

            cert_src = os.path.join(UPLOAD_DIR, args.cert)
            key_src = os.path.join(UPLOAD_DIR, args.key)

            if not os.path.exists(cert_src):
                print(f"ERROR: Certificate file not found at {cert_src}")
                sys.exit(1)

            if not os.path.exists(key_src):
                print(f"ERROR: Key file not found at {key_src}")
                sys.exit(1)

            move_with_optional_backup(cert_src, cert_dest, cert_backup)
            move_with_optional_backup(key_src, key_dest, key_backup)

            print("Certificates updated successfully.")
        
        restart_docker_container()

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
