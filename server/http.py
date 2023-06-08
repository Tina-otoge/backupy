import hashlib
import time
from pathlib import Path

from fastapi import FastAPI, Request

from . import db

app = FastAPI()

library = Path("./files")
HASH_CHUNK_SIZE = 4096


@app.post("/upload")
async def upload(request: Request, name: str, hash: str):
    with db.session() as s:
        if s.get(db.File, hash):
            return {"message": "File already exists", "action": "skip"}
    relative_path = Path(name)
    file_path = library / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
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


@app.post("/sync")
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
