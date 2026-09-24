# PrimeERP — GitHub + Docker + Render + OpenAI

## Architecture

- GitHub: source control and CI/CD.
- Docker: reproducible backend runtime.
- Render: production hosting for API, frontend, and PostgreSQL.
- OpenAI API: optional AI capability for PrimeERP. The API key is never committed to Git.

## Render deployment

The repository root contains `render.yaml`.

1. In Render, choose **New → Blueprint**.
2. Connect `ahmedgamalelnoby-prog/PrimeERP`.
3. Select branch `feature/render-github-docker-openai-20260924` for the first validation deployment.
4. Review the two services and PostgreSQL database.
5. Enter the `OPENAI_API_KEY` secret when Render prompts for it.
6. Deploy the Blueprint.
7. After the first successful deployment, switch the Blueprint branch to `main` when the integration is merged.

The API health endpoint is `/health`.

## Important

- Do not commit `.env`, API keys, database passwords, or JWT secrets.
- Render injects `DATABASE_URL` from the managed PostgreSQL resource.
- Render generates `SECRET_KEY`.
- Frontend `VITE_API_URL` is wired to the API's public Render URL.
- Backend CORS is wired to the frontend's public Render URL.
- The API container runs Alembic migrations before starting Uvicorn.
- `OPENAI_API_KEY` is provisioned as a Render secret placeholder; application-level AI endpoints should use it only from runtime environment variables.

## Local development

This integration does not replace the existing local Docker workflow. Continue using the local environment for development and use GitHub/Render for the deployment pipeline.
