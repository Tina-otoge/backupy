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
parser.add_argument("file", type=str, help="File to upload")

args = parser.parse_args()

file_size = os.path.getsize(args.file)
file_hash = hashlib.md5()
file = Path(args.file)

with file.open("rb") as f:
    while chunk := f.read(HASH_CHUNK_SIZE):
        file_hash.update(chunk)

print(f"Uploading {args.file} ({file_size} bytes)")
with open(args.file, "rb") as f:
    response = requests.post(
        args.url + "/upload",
        data=f,
        params={"name": file.name, "hash": file_hash.hexdigest()},
        headers={"Content-Type": "multipart/form-data"},
        stream=True,
    )
    json.dump(response.json(), sys.stdout, indent=4)
    print()
    response.raise_for_status()
