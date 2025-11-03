# DSP Backend – Development Notes

## Environment
Create a .env file based on .env.example in this folder to configure:
- DB_FILE: SQLite database path
- JWT_*: JWT settings
- DSP_INTERNAL_BASE and DSP_TIMEOUT_SEC
- CORS_ALLOW_ORIGINS

Defaults are development-friendly and allow running without a .env file:
- DB_FILE defaults to dsp_db/dsp.db (container-local)
- JWT defaults: JWT_SECRET=dev-only-change-me, JWT_ALG=HS256, JWT_EXPIRES_MIN=120
- DSP_INTERNAL_BASE=http://10.45.30.64, DSP_TIMEOUT_SEC=30
- CORS_ALLOW_ORIGINS=http://localhost:3000

Rancher/Docker notes:
- The app should be started binding to 0.0.0.0 (uvicorn config/startup should do this).
- DB_FILE path is container-local; mount a volume to persist data across restarts.

## OpenAPI generation
When you change API routes, models, or metadata, regenerate the OpenAPI spec used by other components:

1) Ensure dependencies are installed (see requirements.txt).
2) From the repository root or the backend workspace root, run the generator:

   - From backend root (natural-query-processing-platform-96847-96856/dsp_backend):
     python -m src.api.generate_openapi

   - Or from repo root:
     python natural-query-processing-platform-96847-96856/dsp_backend/src/api/generate_openapi.py

3) The spec will be written to:
   natural-query-processing-platform-96847-96856/dsp_backend/interfaces/openapi.json

Notes:
- The generator imports the FastAPI app from src/api/main.py and calls app.openapi().
- No server startup is required to regenerate the schema.
