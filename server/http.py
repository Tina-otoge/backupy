from pathlib import Path

from fastapi import FastAPI, Request

app = FastAPI()

library = Path("./files")


@app.post("/upload")
async def upload(request: Request, name: str):
    file_path = library / name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    total_uploaded = 0
    with file_path.open("wb") as f:
        async for chunk in request.stream():
            f.write(chunk)
            total_uploaded += len(chunk)
            print(f"Uploaded {total_uploaded} bytes")
    return {"message": "File uploaded successfully"}
