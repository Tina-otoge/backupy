# backupy

Transparent backup solution for your personal storage. Written in modern Python.

## Rationale

Only 15GB of Google storage is free, I want to backup my photos and videos somewhere, but this limit is very easily reached. I have several servers at my
disposal. I want a solution that would allow me to ensure my local collection
is backed up somewhere.

The target use-case scenario is as-follow:

1. I have photos on my phone that I want to save on an external drive from time
   to time.
2. The external drive is connected to a machine that can either run Python or
   Docker, making it a possible host for a *backupy* server.
3. I connect my phone to a computer that can run Python, and use *backupy*'s
   `client-cli` script to upload my photos to the backup server.
4. Only files that have never been uploaded before are actually transferred.
5. I can manage my files on the backup server, sort them into different folders,
   rename them, etc, and I will still benefit from the server not accepting
   duplicates

## Features

- Minimal dependency server that only needs to be able to run Python
- Sort, rename, rearrange files on the server without creating duplicates when
  the next backup runs
    > This works by keeping track of the checksum of the uploaded files, so
    > duplicates are automatically ignored.
- Dead simple HTTP API to build your own integrations / clients
- Straightforward pure Python CLI tool to upload your files, that supports
  transferring a whole file tree without sending files that are already present
  on the server
- Support for directly putting your files into the backup server by regular transfer means (mounting, sftp, etc) without messing up the server state
- [TODO] Server can be easily mirrored to avoid data loss when a system
  inevitably fails
  - Technically this is currently the case, you should be able to restore a
    functionning backupy instance simply by importing a copy of the `var` and
    `files` folder, which should make mirroring easy.
  - However, when maintaining the mirror, there is no way to ensure you are
    correctly deleting on the mirror the files on the master. A `mirror` command
    will be implemented to do this.
- [TODO] Simple web frontend for uploading files, backup from anywhere!

## Usage

Run the server

```bash
python -m server
```

> This will run the HTTP server that exposes an API to upload files.

Upload a file

```bash
# curl
curl --data "@/my/file.ext" "https://server.ip/upload?name=some/location.ext&hash=123themd5ofthefile"

# client-cli
python -m client-cli https://server.ip /my/file.ext
```

> Trying to upload a file that is already on the server will not work if any
> file with the same hash is already there

Update the hash table to account for files directly added to the library without
using the API

```bash
curl -X POST https://server.ip/sync
```

> This will report on the number of new files detected, renamed or removed

> TODO: Add a server command to trigger this without an HTTP call  
> ie: `python -m server sync`

## Installation

### Server (pure Python)

```bash
# Optional, prepare a virtual env to store the dependencies
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r server/requirements.txt

# Run the server
python -m server
```

### Client (pure Python)

```bash
# Optional, prepare a virtual env to store the dependencies
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r client-cli/requirements.txt

# Run client commands
python -m client-cli --help
python -m client-cli https://server.ip ~/Photos
```
