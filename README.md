# Digitally Agency — Production-Ready AI Marketing Platform

A high-performance, modular digital agency landing page and AI toolbox. Featuring **HTMX-driven modularity**, **live market data**, **serverless AI diagnostics**, and **automated PDF reporting**.

---

## 🛠 Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTMX · Alpine.js · Tailwind CSS · Chart.js |
| **Backend** | Python · Flask · Groq API (Llama 3) |
| **Data** | MongoDB Atlas · yfinance · Open-Meteo (Keyless) |
| **Reporting** | WeasyPrint (Automated PDF generation) |
| **Deployment** | Vercel (Edge-ready serverless functions) |

---

## ✨ Key Features

### 📉 Smart Ticker & Real-Time Environment
- **Live Market Data**: Real-time quotes for Big Tech (MSFT, NVDA, AAPL, etc.) via `yfinance`.
- **Keyless Weather**: Integrated with **Open-Meteo** for zero-config, localized weather data.
- **Dynamic Theming**: The interface background and "orb" shift colors based on current weather conditions in your city.

### 🔥 AI Website Roaster (Upgraded)
- **Deep Analysis**: Powered by **Llama 3 on Groq** for sub-second audit results.
- **Visual Reports**: Interactive **Radar Charts** using Chart.js (SEO, Speed, Mobile, Accessibility).
- **PDF Export**: Generate professional, branded PDF audit reports with a single click.
- **Persistence**: All roasts are stored in MongoDB for later retrieval.

### 💬 AI Strategist FAB
- Persistent AI chat agent that understands the context of your website audit.
- Markdown-supported responses with a polished, cyber-agency UI.

### 📋 Lead Capture & CRM
- Integrated lead submission form that stores data directly to MongoDB.
- Production-hardened with security headers and data validation.

---

## 🚀 Deployment (Vercel)

This project is optimized for **Vercel** serverless deployment.

### 1. Project Structure
```text
digitally/
├── backend/
│   ├── app.py           # Flask Serverless Function
│   └── requirements.txt  # Python Dependencies
├── frontend/
│   ├── components/      # HTMX HTML Modules
│   ├── js/              # Modular JS (roaster, chat, ticker)
│   └── css/             # Global Styles
└── vercel.json          # Deployment Config
```

### 2. Environment Variables
Set these in your Vercel Dashboard:
- `GROQ_API_KEY`: Get from [Groq Console](https://console.groq.com)
- `MONGO_URI`: Your MongoDB Atlas connection string
- `PORT`: 5000 (standard)

---

## 💻 Local Development

1. **Clone & Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. **Run**:
   ```bash
   python app.py
   ```
   *The Flask backend serves the frontend automatically at http://localhost:5000*

---

## 🔒 Security & Production
- **Production Hardened**: Includes `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy`.
- **Graceful Fallbacks**: The system automatically degrades if WeasyPrint (PDF) or MongoDB is unavailable.
- **Modular Frontend**: Components are loaded on demand via HTMX for lightning-fast initial paints.
