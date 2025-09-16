from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uvicorn

from .database import get_db, engine
from .models import Product, Base
from .recommender import recommender

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Product Recommender",
    description="A FastAPI application for AI-based product recommendations",
    version="1.0.0"
)

# Pydantic schemas
from pydantic import BaseModel

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    similarity_score: float = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    product_id: int
    recommendations: List[ProductResponse]

@app.on_event("startup")
async def startup_event():
    """Initialize the recommender when the app starts"""
    db = next(get_db())
    try:
        recommender.fit(db)
    finally:
        db.close()

@app.get("/")
async def root():
    """Root endpoint with a simple hello message"""
    return {
        "message": "Welcome to AI Product Recommender API",
        "version": "1.0.0",
        "endpoints": {
            "recommendations": "/recommend/{product_id}",
            "products": "/products",
            "docs": "/docs"
        }
    }

@app.get("/recommend/{product_id}")
async def get_recommendations(
    product_id: int, 
    top_n: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get AI-based product recommendations for a given product ID
    
    - **product_id**: The ID of the product to get recommendations for
    - **top_n**: Number of recommendations to return (default: 5)
    """
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get recommendations
    recommendations = recommender.get_recommendations(product_id, top_n)
    
    return RecommendationResponse(
        product_id=product_id,
        recommendations=recommendations
    )

@app.get("/products", response_model=List[ProductResponse])
async def get_products(db: Session = Depends(get_db)):
    """Get all products in the database"""
    products = db.query(Product).all()
    return products

@app.post("/products", response_model=ProductResponse)
async def create_product(
    name: str,
    category: str,
    price: float,
    db: Session = Depends(get_db)
):
    """Create a new product"""
    product = Product(name=name, category=category, price=price)
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Refit the recommender with new data
    recommender.fit(db)
    
    return product

@app.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    
    # Refit the recommender with updated data
    recommender.fit(db)
    
    return {"message": f"Product {product_id} deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
