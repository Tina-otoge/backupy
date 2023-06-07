import os
from argparse import ArgumentParser
from pathlib import Path

import requests

parser = ArgumentParser()
parser.add_argument("url", type=str, help="URL to upload to")
parser.add_argument("file", type=str, help="File to upload")

args = parser.parse_args()

file_size = os.path.getsize(args.file)
file = Path(args.file)

print(f"Uploading {args.file} ({file_size} bytes)")
with open(args.file, "rb") as f:
    response = requests.post(
        args.url + "/upload",
        data=f,
        params={"name": file.name},
        headers={"Content-Type": "multipart/form-data"},
        stream=True,
    )
    response.raise_for_status()
