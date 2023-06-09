import hashlib
import json
import os
import sys
from argparse import ArgumentParser
from pathlib import Path

import requests

HASH_CHUNK_SIZE = 4096

parser = ArgumentParser()
parser.add_argument("url", type=str, help="URL to upload to")
parser.add_argument("path", type=str, help="File to upload")
parser.add_argument("--token", type=str, help="Authentication token")

args = parser.parse_args()

path = Path(args.path)


def main():
    if path.is_file():
        upload_file(path, name=path.name)
        return

    if not path.is_dir():
        print(f"{path} is not a file or directory")
        return 1

    stats = {}
    for file in path.glob("**/*"):
        if file.is_file():
            action = upload_file(file, name=file.relative_to(path))
            stats.setdefault(action, 0)
            stats[action] += 1
    print("Batch upload stats:")
    json.dump(stats, sys.stdout, indent=4)
    print()


def get_hash(file: Path):
    file_hash = hashlib.md5()
    with file.open("rb") as f:
        while chunk := f.read(HASH_CHUNK_SIZE):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def upload_file(file: Path, name: str = None):
    file_size = os.path.getsize(file)
    print(f"Uploading {file} ({file_size} bytes)")
    file_hash = get_hash(file)
    with file.open("rb") as f:
        response = requests.post(
            args.url + "/upload",
            data=f,
            params={"name": name, "hash": file_hash},
            headers={"Authorization": f"Bearer {args.token}"},
            stream=True,
        )
        json.dump(response.json(), sys.stdout, indent=4)
        print()
        response.raise_for_status()
    return response.json().get("action")


sys.exit(main())
