# PocketGenius: AI-Powered Personal Finance Assistant

PocketGenius is an AI-powered personal finance assistant designed to help users:

- **Categorize and analyze financial transactions**  
- **Assess portfolio performance** (ROI, volatility, Sharpe ratio)  
- **Generate tailored recommendations** (including GPT-based insights)  
- **Provide quick single-symbol analysis and macroeconomic outlook**  

This project combines **FastAPI**, **OpenAI GPT**, **Redis caching**, **yfinance** market data, and a **React frontend** to deliver an interactive financial analysis tool.


---


### 🌐 Live Demo  
👉 **[PocketGenius App](https://pocket-genius.vercel.app/)**  

---


## 📌 Features

✅ **Transaction Analysis:** Upload CSVs, categorize expenses, and get GPT-based budgeting suggestions.  
✅ **Portfolio Analysis:** Compute investment metrics and receive AI-powered investment recommendations.  
✅ **Single-Symbol Lookup:** Fetch stock fundamentals, ROI vs purchase, and AI investment advice.  
✅ **Sector Breakdown:** Get an overview of your portfolio’s sector diversification.  
✅ **Macro-Outlook:** AI-generated insights into the current macroeconomic environment.  

---

 
## 🛠 Tech Stack

- **Backend:**  FastAPI, OpenAI GPT, Redis, yfinance, Uvicorn

- **Frontend:** React, Vite, TailwindCSS

- **Database & Caching:** Redis Cache

- **Deployment:** Render (backend), Vercel (frontend)


---

## ⚡ Scalability & Architecture  

PocketGenius is designed for **high performance and scalability**, leveraging **FastAPI’s asynchronous capabilities** to handle concurrent requests efficiently.  

### 🚀 Scalability Features

1. **FastAPI for High-Performance Asynchronous Processing**  
   - FastAPI is asynchronous by design, allowing PocketGenius to handle multiple requests concurrently without blocking execution, making it ideal for high-traffic applications.  

2. **Redis Caching for Optimized Data Retrieval**  
   - Using Redis as a caching layer significantly reduces response times by storing frequently accessed financial data, decreasing reliance on repeated API calls (e.g., stock market data from yfinance).  

3. **Efficient API Design with Modular Microservices Approach**  
   - The backend is structured with modular services (e.g., transaction analysis, portfolio evaluation, and market insights), making it easier to scale individual components without affecting the entire system.  

4. **Cloud Deployment with Load Balancing Capabilities**  
   - Designed for cloud deployment (e.g., Render, AWS, or Vercel), allowing horizontal scaling through auto-scaling (if it is moved to paid plan) instances when traffic increases.  

5. **Database and Caching Separation**  
   - Separating volatile financial data (cached in Redis) from persistent user data ensures efficient memory usage and improved request handling.  

---


## 🚀 Installation & Setup

### 1️⃣ Clone the Repository
```
git clone https://github.com/yourusername/pocketGenius.git
cd pocketGenius
```

### 1️⃣ Clone the Repository

```
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use: .\venv\Scripts\activate
pip install -r requirements.txt
```

#### Create a .env file in backend/ with your OpenAI API key:

```

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_EXPIRATION_MINUTES=15
```


#### Start the backend:

```
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```


### 3️⃣ Frontend Setup

```
cd frontend
npm install
npm start
```


Now, open http://localhost:3000 to view the frontend.


---


## 🚀 Endpoints

### 1️⃣ Welcome Message  
#### **GET** `/`
- **Description:** Returns a simple welcome message.
- **Response:**  
  ```json
  {
    "message": "Welcome to FinGenius API. Go to /docs for interactive API docs."
  }
  ```

### 2️⃣ Upload Transactions
#### **POST** /upload-transactions
-	**Description:** Upload a CSV file containing transactions to analyze.
-	**Request Body:**
```json
{
  "file": "CSV file containing transactions"
}
```
- **Response:**  
```json
{
  "transactions": [
    {
      "description": "Coffee",
      "amount": 5.99,
      "date": "2024-02-01",
      "category": "Food & Beverage",
      "budget_recommendation": "Limit coffee expenses to $30/month",
      "savings_potential": "$10 savings possible"
    }
  ]
}
```


### 3️⃣ Analyze Portfolio

#### POST /analyze-portfolio
-	**Description:** Analyze a user’s investment portfolio.
-	**Request Body:**
```json
{
  "items": [
    { "symbol": "AAPL", "quantity": 10, "purchase_price": 150 }
  ]
}
```

- **Response:**  
```json
{
  "total_investment": 1500,
  "roi_percent": 10.5,
  "sharpe_ratio": 1.2,
  "gpt_advice": "Your portfolio has a moderate risk level."
}
```

### 4️⃣ Analyze Portfolio with Risk Tolerance

POST /analyze-portfolio-advanced
-	**Description:** Analyze portfolio with risk tolerance customization.
-	**Query Parameters:**
-	risk_tolerance: "conservative" | "moderate" | "aggressive"
-	**Request Example:**
```json
{
  "items": [
    { "symbol": "GOOGL", "quantity": 5, "purchase_price": 2800 }
  ]
}
```
- **Response:**  
```json
{
  "total_investment": 14000,
  "roi_percent": 15.2,
  "risk_analysis": "Aggressive strategy recommended."
}
```

### 5️⃣ Portfolio Sector Breakdown

#### POST /portfolio-sector-breakdown
-	**Description:** Returns sector distribution of investments.
-	**Request Example:**
```json
{
  "items": [
    { "symbol": "TSLA", "quantity": 8, "purchase_price": 700 },
    { "symbol": "AAPL", "quantity": 5, "purchase_price": 150 }
  ]
}
```
- **Response:**  
```json
{
  "sector_breakdown": {
    "Technology": 75.2,
    "Automotive": 24.8
  }
}
```


### 6️⃣ Analyze Single Stock Symbol

#### POST /analyze-symbol
-	**Description:** Fetch details of a single stock.
-	**Request Body:**
```json
{
  "symbol": "AAPL",
  "purchase_price": 150,
  "quantity": 10,
  "risk_tolerance": "moderate"
}
```
-	**Response:**
```json
{
  "symbol": "AAPL",
  "quantity": 10,
  "invested_amount": 1500,
  "current_price": 160,
  "current_value": 1600,
  "roi_percent": 6.67,
  "local_recommendation": "Hold",
  "ai_recommendation": "Consider holding AAPL based on moderate risk.",
  "fundamentals": {
    "sector": "Technology",
    "PE_ratio": 24.5
  }
}
```

### 7️⃣ Analyze Portfolio with Custom Macroeconomic Inputs

#### POST /analyze-portfolio-custom
-	**Description:** Let users override risk-free rate & macro factors.
-	**Request Body:**
```json
{
  "portfolio": {
    "items": [
      { "symbol": "MSFT", "quantity": 10, "purchase_price": 320 }
    ]
  },
  "risk_free_rate": 2.0,
  "macro_inflation": 3.5,
  "macro_interest_rate": 5.0,
  "risk_tolerance": "aggressive"
}
```
-	**Response:**
```json
{
  "total_investment": 3200,
  "roi_percent": 8.5,
  "macro_analysis": {
    "inflation": 3.5,
    "interest_rate": 5.0,
    "gdp_growth": 2.1
  }
}
```

### 8️⃣ Get Macroeconomic Outlook

#### GET /macro-outlook
-	**Description:** Fetch basic macroeconomic data & GPT-generated insights.
-	**Response:**
```json
{
  "macro_data": {
    "interest_rate": 5.0,
    "inflation": 3.2,
    "gdp_growth": 2.1
  },
  "macro_outlook": "The economic outlook suggests a stable recovery with moderate inflation risks."
}
```
