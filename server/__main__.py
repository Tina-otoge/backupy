import os

import uvicorn

uvicorn.run(
    "server.http:app",
    host="0.0.0.0",
    port=8000,
    reload=os.environ.get("ENV", "dev") == "dev",
    reload_dirs=["server"],
)
