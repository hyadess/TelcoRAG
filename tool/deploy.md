# Deploy TelcoRAG

The backend runs on **Vercel**, the UI on **Streamlit Community Cloud**,
feedback/chunk data on **Supabase**, vectors on **Pinecone**, and Gemini on
**Google Vertex AI**.

## 1. Prepare Supabase and retrieval data

Use Supabase's transaction-pooler URL (port `6543`) locally, then upload the
chunks and BM25 artifact from the repository root:

```dotenv
DATABASE_URL=postgresql+psycopg://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require
```

```bash
python -m scripts.sync_supabase_chunks --chunker baseline
```

Run ingestion first if the matching Pinecone vectors and local chunk files do
not exist. Re-run the sync command whenever chunks change.

## 2. Deploy the FastAPI backend to Vercel

Import the repository root into Vercel. The backend entrypoint is already set
to `tool.backend.main:app` in `pyproject.toml`. Add these environment variables:

```dotenv
DATABASE_URL=postgresql+psycopg://...
TELCORAG_CHUNK_STORE=database
TELCORAG_CHUNKER=baseline
TELCORAG_RETRIEVER=vector
TELCORAG_ADMIN_PASSWORD=CHANGE_ME
PINECONE_API_KEY=...

GOOGLE_CLOUD_PROJECT=...
GOOGLE_CLOUD_LOCATION=global
GCP_PROJECT_NUMBER=...
GCP_SERVICE_ACCOUNT_EMAIL=...
GCP_WORKLOAD_IDENTITY_POOL_ID=vercel
GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID=vercel
```

Also add any provider key required by `config/pipeline.yaml`. Do not set
`GOOGLE_APPLICATION_CREDENTIALS` on Vercel. As a fallback to OIDC, set the full
service-account JSON in the protected `GOOGLE_SERVICE_ACCOUNT_JSON` variable.

### Google Cloud OIDC/IAM

Follow the [Vercel GCP OIDC guide](https://vercel.com/docs/oidc/gcp) to create
the Workload Identity pool/provider. Then run the following as a GCP IAM admin:

```bash
PROJECT_ID="project-68bdadd8-02bf-47ef-843"
PROJECT_NUMBER="YOUR_GCP_PROJECT_NUMBER"
POOL_ID="vercel"
SERVICE_ACCOUNT="YOUR_SERVICE_ACCOUNT_EMAIL"
VERCEL_SUBJECT="owner:TEAM_SLUG:project:VERCEL_PROJECT_NAME:environment:production"

WIF_PRINCIPAL="principal://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/subject/${VERCEL_SUBJECT}"

gcloud services enable iamcredentials.googleapis.com sts.googleapis.com \
  aiplatform.googleapis.com --project="$PROJECT_ID"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="$WIF_PRINCIPAL" \
  --role="roles/serviceusage.serviceUsageConsumer"

gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT" \
  --project="$PROJECT_ID" \
  --member="$WIF_PRINCIPAL" \
  --role="roles/iam.workloadIdentityUser"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"
```

`VERCEL_SUBJECT` must exactly match Vercel's token subject, including the
environment (`production`, `preview`, or `development`). If Google reports a
quota-project permission error, the missing grant is usually
`roles/serviceusage.serviceUsageConsumer`. IAM changes can take a few minutes;
retry the request without redeploying. See [Google's quota-project documentation](https://docs.cloud.google.com/docs/quotas/set-quota-project).

Verify the backend after deployment:

```text
https://YOUR-BACKEND.vercel.app/health
https://YOUR-BACKEND.vercel.app/health/db
```

## 3. Deploy the Streamlit frontend

In Streamlit Community Cloud, select `tool/frontend/app.py` and add:

```toml
TELCORAG_BACKEND_URL = "https://YOUR-BACKEND.vercel.app"
TELCORAG_ADMIN_PASSWORD = "SAME_VALUE_AS_VERCEL"
```

Deploy, open the app, submit a test question/rating, and confirm the backend
health endpoints and Supabase rows.
