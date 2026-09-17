# Deployment Guide: AI Sales Call Assistant

This guide covers deploying the unified **React + FastAPI** application to production with **HTTPS** (mandatory for browser microphone access) and **WebSockets**.

---

## ⚠️ Important Requirement: HTTPS for Microphone Access
Modern browsers (`Chrome`, `Edge`, `Safari`, `Firefox`) block microphone access (`getUserMedia`) on insecure origins.
Your production URL **must use HTTPS** (e.g. `https://your-app.com` or `https://your-app.onrender.com`).
All cloud platforms below (Render, Railway, Cloud Run) provide free, automatic HTTPS/SSL certificates out of the box.

---

## 🚀 Option 1: Deploy on Render (Recommended & Easiest)

Render offers free Web Services with automatic HTTPS and WebSocket support.

### Steps:
1. **Push your code to GitHub**:
   ```sh
   git add .
   git commit -m "Add React UI, FastAPI server, Dockerfile"
   git push origin main
   ```
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Choose **Docker** as the Runtime (Render will automatically detect the [`Dockerfile`](file:///C:/Users/Vinit/Desktop/AI_sales%20Model/Dockerfile)).
5. Under **Environment Variables**, add:
   - `GROQ_API_KEY`: `your_groq_api_key_here`
   - `GROQ_MODEL`: `groq/compound-mini`
6. Click **Deploy Web Service**.
7. Your app will be live at `https://<your-service-name>.onrender.com`!

---

## 🚆 Option 2: Deploy on Railway (1-Click Docker Deploy)

Railway provides seamless Docker deployment with persistent logs and custom domains.

### Steps:
1. Go to [Railway.app](https://railway.app/) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository.
4. Go to the project **Variables** tab and set:
   - `GROQ_API_KEY`: `your_groq_api_key_here`
   - `GROQ_MODEL`: `groq/compound-mini`
5. Railway will automatically build using the multi-stage `Dockerfile` and expose the service.
6. Under **Settings** -> **Networking**, click **Generate Domain** (gives you `https://your-app.up.railway.app`).

---

## ☁️ Option 3: Deploy on Google Cloud Run

For scalable, serverless container hosting on Google Cloud:

### Steps:
```sh
# 1. Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and deploy directly from source
gcloud run deploy ai-sales-assistant \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GROQ_API_KEY=your_key,GROQ_MODEL=groq/compound-mini \
  --port 8000
```
Cloud Run will output your secure `https://ai-sales-assistant-...a.run.app` URL.

---

## 🖥️ Option 4: Deploy on an Ubuntu VPS (DigitalOcean / AWS EC2 / Linode)

If you have your own Linux server:

### 1. Install Docker & Docker Compose
```bash
sudo apt update && sudo apt install -y docker.io docker-compose
```

### 2. Build and Run Container
```bash
# Build the image
docker build -t ai-sales-assistant .

# Run with your Groq API key
docker run -d \
  --name sales-assistant \
  --restart always \
  -p 8000:8000 \
  -e GROQ_API_KEY="your_groq_api_key_here" \
  -e GROQ_MODEL="groq/compound-mini" \
  ai-sales-assistant
```

### 3. Setup Nginx with SSL (Let's Encrypt)
To enable microphone access, configure Nginx to proxy HTTPS and WebSockets to port 8000:

```nginx
server {
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then install SSL via Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 📦 Local Testing of Production Build

You can test the production build locally anytime before pushing:

```sh
# 1. Build React
cd frontend
npm run build
cd ..

# 2. Run backend
python run_server.py
```
Open `http://localhost:8000` in your browser.
