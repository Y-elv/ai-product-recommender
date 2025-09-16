# AI Product Recommender

A FastAPI application for AI-based product recommendations using PostgreSQL, SQLAlchemy, Pandas, and scikit-learn.

## Features

- **AI-powered recommendations** using cosine similarity and TF-IDF vectorization
- **PostgreSQL database** with SQLAlchemy ORM
- **RESTful API** with FastAPI
- **Product management** (CRUD operations)
- **Real-time recommendations** based on product categories and prices

## Project Structure

```
ai-recommender/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app with endpoints
│   ├── models.py         # SQLAlchemy Product model
│   ├── database.py       # Database connection
│   └── recommender.py    # AI recommendation logic
├── .env                  # Database URL (create this file)
├── requirements.txt      # Dependencies
└── README.md
```

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file:**

   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/ai_recommender_db
   ```

3. **Set up PostgreSQL database:**

   - Create a database named `ai_recommender_db`
   - Update the DATABASE_URL in .env with your credentials

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

- `GET /` - Welcome message and API info
- `GET /recommend/{product_id}` - Get AI recommendations for a product
- `GET /products` - Get all products
- `POST /products` - Create a new product
- `DELETE /products/{product_id}` - Delete a product

## Usage

1. **Add some products:**

   ```bash
   curl -X POST "http://localhost:8000/products" \
        -H "Content-Type: application/json" \
        -d '{"name": "Laptop", "category": "Electronics", "price": 999.99}'
   ```

2. **Get recommendations:**
   ```bash
   curl "http://localhost:8000/recommend/1?top_n=3"
   ```

## AI Recommendation Algorithm

The recommendation system uses:

- **TF-IDF vectorization** on product categories
- **Price normalization** for better similarity calculation
- **Cosine similarity** to find similar products
- **Feature combination** of category and normalized price

## Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.
