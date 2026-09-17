# AI Sales Call Assistant: Real-Time Speech Transcription, Sentiment Analysis & CRM

An AI-powered sales call assistant featuring real-time speech transcription via **Whisper**, conversational sentiment & action suggestions via **Groq (Llama-3.1)**, **CRM intelligence**, and post-call executive summaries.

Now upgraded with a modern **React + Vite UI** backed by a high-performance **FastAPI server** with real-time **WebSocket audio streaming**, while preserving the original **Streamlit** interface.

---

## 🚀 Key Features

- **Modern React Dashboard**: Sleek, responsive, dark-themed UI built with Vite, React, and Lucide icons.
- **Native Browser Microphone Streaming**: Real-time 16 kHz mono PCM audio capture using HTML5 Web Audio API over WebSocket (no STUN/TURN/WebRTC server configuration needed).
- **Live Automatic Speech Transcription**: Fast local Whisper ASR transcription (`whisper-large-v3-turbo`).
- **Real-Time Sentiment & Action Suggestions**: Dynamic sentiment tracking (Positive, Neutral, Negative) and real-time guidance on what the sales rep should say next.
- **CRM Integration**: Instant customer profile lookup from `CRM_data.csv` by phone number, plus AI-generated product cross-sell recommendations.
- **Executive Post-Call Analytics**: Automatically generated post-call scorecard, customer intent, key topics, objections, resolutions, next steps, and full expandable transcript.
- **Google Sheets Integration**: Automatic logging of transcript, sentiment, and summary to Google Sheets.

---

## 📁 Project Structure

```
AI_sales Model/
│
├── frontend/             # Modern React + Vite UI
│   ├── src/
│   │   ├── components/   # Header, SidebarCRM, CallControls, LiveInsights, PostCallSummary
│   │   ├── services/     # Web Audio API streamer & REST/WebSocket client
│   │   ├── App.jsx       # Main Dashboard application
│   │   └── index.css     # Modern styling & theme
│   └── package.json
├── server.py             # FastAPI backend with WebSocket audio streaming & REST APIs
├── run_server.py         # Entry point for backend server
├── start_app.bat         # 1-Click Windows launcher for both Backend and React UI
├── start_backend.bat     # Launcher for backend server only
├── start_frontend.bat    # Launcher for React frontend only
├── app.py                # Legacy Streamlit web interface
├── audio.py              # Audio recording & silence detection utilities
├── whisper_model.py      # Whisper model loading and transcription
├── sentiment.py          # Sentiment analysis & summary via Groq API
├── sheet.py              # Google Sheets logging integration
├── crm_functions.py      # CRM data fetching and AI recommendations
├── main.py               # Main integration script & SalesCallPipeline
├── CRM_data.csv          # Sample customer database for CRM
├── requirements.txt      # Python dependencies
└── .env                  # Environment variables (GROQ_API_KEY)
```

---

## 🛠️ Setup Instructions

### 1. Python Environment

Ensure you have Python 3.10+ installed:

```sh
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Frontend Dependencies

Ensure you have Node.js (v18+) installed:

```sh
cd frontend
npm install
cd ..
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

---

## 💻 Running the Project

### Option A: Modern React UI (Recommended)

#### Quick 1-Click Launch (Windows):
Double-click `start_app.bat` to automatically launch both the backend and frontend.

#### Or Manual Terminal Launch:

**Terminal 1 (Backend):**
```sh
.venv\Scripts\activate
python run_server.py
```
*Runs FastAPI on `http://127.0.0.1:8000` (API documentation at `http://127.0.0.1:8000/docs`).*

**Terminal 2 (React Frontend):**
```sh
cd frontend
npm run dev
```
*Runs React development server on `http://localhost:5173`.*

---

### Option B: Original Streamlit UI

To run the original Streamlit application:

```sh
.venv\Scripts\activate
streamlit run app.py
```

---

## 📊 CRM Testing Numbers

For quick testing with `CRM_data.csv`, you can click the quick demo contact buttons in the React UI or enter:

- `+91-9876543210` (Rajesh Verma – Ergonomic Chair X)
- `+91-9876543211` (Priya Sharma – Bose Headset 700)
- `+91-9876543212` (Amit Joshi – Laptop Pro 15)
- `+91-9876543213` (Neha Gupta – Wireless Keyboard Z)
