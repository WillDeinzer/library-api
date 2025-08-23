import uvicorn
import os
import logging
PORT = int(os.getenv("PORT"))
logging.info(f"Railway PORT={PORT}")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT)