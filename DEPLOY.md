# Deployment Guide for TrustLens

This guide covers deployment instructions for Azure App Service, Render, and Docker.

## Prerequisites

-   A GitHub repository with your code (for Azure/Render)
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local Docker)

---

## Option 1: Render (Free Tier - Recommended)

Render offers a free tier for web services that enables you to host this Flask app at no cost.

### Prerequisites
-   Your code must be pushed to GitHub.
-   You need a [Render.com](https://render.com) account.

### Step-by-Step Guide

1.  **Push to GitHub**:
    -   Commit and push all the new files (`Procfile`, `runtime.txt`, `requirements.txt`) to your GitHub repository.
    
2.  **Create Service on Render**:
    -   Click **"New +"** and select **"Web Service"**.
    -   Connect your GitHub repository (`trustlens-extension`).
    -   **Name**: `trustlens-backend` (or similar).
    -   **Region**: Choose the one closest to you (e.g., Singapore, Frankfurt).
    -   **Branch**: `main`.
    -   **Runtime**: Python 3.
    -   **Build Command**: `pip install -r requirements.txt`.
    -   **Start Command**: `gunicorn run:app`.
    -   **Instance Type**: Select **"Free"**.

3.  **Environment Variables**:
    -   Scroll down to **"Environment Variables"**.
    -   Add keys from your `.env` file one by one:
        -   `AZURE_OPENAI_ENDPOINT`
        -   `AZURE_OPENAI_API_KEY`
        -   `AZURE_OPENAI_DEPLOYMENT`
        -   `AZURE_OPENAI_API_VERSION`
        -   (Optional) `MONGODB_URI`, etc.
    -   *Note: Do NOT upload your `.env` file directly. You must set these manually in the dashboard for security.*

4.  **Deploy**:
    -   Click **"Create Web Service"**.
    -   Wait for the build to finish. You should see "Your service is live" and a URL like `https://trustlens-backend.onrender.com`.

### Important Note on Free Tier
-   Free instances **spin down** after 15 minutes of inactivity. The first request after a period of inactivity may take up to 50 seconds to respond. This is normal for the free tier.

---

## Option 2: Azure App Service (Paid/Free Trial)

---

## Option 3: Docker (Universal)

You can build and run the container locally or deploy the image to any container registry (Docker Hub, Azure Container Registry).

### Build locally

```bash
docker build -t trustlens-app .
```

### Run locally

```bash
# Run on port 5000, passing environment variables from .env file
docker run -p 5000:5000 --env-file .env trustlens-app
```

Visit `http://localhost:5000/api/health` to verify.

---

## Important Notes

-   **MongoDB**: If you are using MongoDB, ensure your database accepts connections from the deployed managed service's IP addresses (or allow `0.0.0.0/0` if secure).
-   **Security**: Never commit your `.env` file. Always set environment variables in the dashboard of your cloud provider.
