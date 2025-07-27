from decouple import config

DB_USER = config('DB_USER', '')
DB_PASSWORD = config('DB_PASSWORD', '')
DB_HOST = config('DB_HOST', '')
DB_PORT = config('DB_PORT', default=5432, cast=int)
DB_NAME = config('DB_NAME', '')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"