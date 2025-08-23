import uvicorn
import os
PORT = int(os.getenv("PORT"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)