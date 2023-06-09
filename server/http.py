import functools
import hashlib
import inspect
import time
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from . import db
from .config import REQUIRES_AUTH

app = FastAPI()

library = Path("./files")
HASH_CHUNK_SIZE = 4096


def _auth(authorization: Annotated[str, Header()]):
    if REQUIRES_AUTH and not authorization:
        raise HTTPException(401, "Missing token")
    if authorization:
        prefix = "Bearer "
        if not authorization.startswith(prefix):
            raise HTTPException(401, "Invalid token")
        authorization = authorization[len(prefix) :]
        with db.session() as s:
            token = db.Token.from_token(s, authorization)
            if not token:
                raise HTTPException(401, "Invalid token")
            print(
                f"User {token.user.name} authenticated using token {token.id}"
            )


auth = Depends(_auth)


@app.post("/upload", dependencies=[auth])
async def upload(
    # Reading from request instead of UploadFile to support streaming
    request: Request,
    name: str,
    hash: str,
):
    print("Uploading file", name, hash)
    with db.session() as s:
        if s.get(db.File, hash):
            return {"message": "File already exists (hash)", "action": "skip"}
    relative_path = Path(name)
    file_path = library / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        return {
            "message": "This path is already occupied by a different file",
            "action": "error",
        }
    total_uploaded = 0
    file_hash = hashlib.md5()
    with file_path.open("wb") as f:
        async for chunk in request.stream():
            f.write(chunk)
            file_hash.update(chunk)
            total_uploaded += len(chunk)
            print(f"Uploaded {total_uploaded} bytes")
    if file_hash.hexdigest() != hash:
        file_path.unlink()
        msg = f"Hash mismatch: {file_hash.hexdigest()} != {hash}, file deleted"
        print(msg)
        return {"message": msg, "action": "error"}
    with db.session() as s:
        s.add(db.File(hash=hash, path=str(relative_path)))
    return {"message": "File uploaded successfully", "action": "upload"}


def get_hash(file: Path):
    file_hash = hashlib.md5()
    with file.open("rb") as f:
        while chunk := f.read(HASH_CHUNK_SIZE):
            file_hash.update(chunk)
    return file_hash.hexdigest()


@app.post("/sync", dependencies=[auth])
async def sync():
    start = time.time()
    library.mkdir(exist_ok=True)
    tmp_library = library.with_suffix(".sync")
    library.rename(tmp_library)
    added_files = 0
    matched_files = 0
    deleted_files = 0
    renamed_files = 0
    for file in tmp_library.glob("**/*"):
        if not file.is_file():
            continue
        relative_path = file.relative_to(tmp_library)
        path = str(relative_path)
        hash = get_hash(file)
        with db.session() as s:
            file = s.get(db.File, hash)
            if file:
                if file.path != path:
                    print(f"File {path} moved to {file.path}")
                    file.path = path
                    renamed_files += 1
                else:
                    matched_files += 1
            else:
                file = db.File(hash=hash, path=path)
                s.add(file)
                added_files += 1
    with db.session() as s:
        for file in s.query(db.File):
            if not tmp_library.joinpath(file.path).exists():
                s.delete(file)
                deleted_files += 1
    tmp_library.rename(library)
    end = time.time()
    return {
        "message": "Sync successful",
        "stats": {
            "added_files": added_files,
            "deleted_files": deleted_files,
            "matched_files": matched_files,
            "renamed_files": renamed_files,
            "duration": end - start,
        },
    }
