# DSP App Integration Notes

## Environment files
- Backend: natural-query-processing-platform-96847-96856/dsp_backend/.env
  - Copy from .env.example and configure DB_FILE, JWT settings, DSP_INTERNAL_BASE, CORS.
- Frontend: natural-query-processing-platform-96847-96857/dsp_frontend/.env
  - Copy from .env.example and set REACT_APP_BACKEND_URL (leave empty if same-origin).

## OpenAPI
When backend API changes:
1) Regenerate spec using the included script:
   python -m src.api.generate_openapi
   (run from dsp_backend directory)
2) Updated spec is saved to dsp_backend/interfaces/openapi.json.
3) Commit the updated openapi.json if needed for client tooling or documentation.

## Notes
- Do not commit real secrets into .env files—only .env.example is committed.
- The DB container provides SQLite data; ensure DB_FILE in backend points to the correct path/volume.
