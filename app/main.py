from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime

from .database import get_db, engine
from .models import Product, ProductImage, Base
from .recommender import recommender

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="AI Construction Product Recommender",
    description="A FastAPI application for AI-based construction product recommendations",
    version="1.0.0"
)

# Pydantic schemas
from pydantic import BaseModel

class ProductImageResponse(BaseModel):
    id: str
    url: str
    alt: str
    isDefault: bool
    createdAt: str
    updatedAt: str
    productId: str

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    product_id: str  # Original product ID from Node.js system
    name: str
    description: str
    price: float
    stock: int = 0
    category: str
    user_id: Optional[str] = None
    interaction_weight: Optional[float] = 1.0
    interaction_type: Optional[str] = None

class ProductResponse(BaseModel):
    id: str
    product_id: str
    name: str
    description: str
    price: float
    stock: int
    category: str
    user_id: Optional[str] = None
    interaction_weight: Optional[float] = None
    interaction_type: Optional[str] = None
    images: List[ProductImageResponse] = []
    similarity_score: float = None

    class Config:
        from_attributes = True

class PaginatedProductsResponse(BaseModel):
    success: bool = True
    data: List[ProductResponse]
    pagination: Dict[str, Any]

class RecommendationResponse(BaseModel):
    success: bool = True
    data: Dict[str, Any]


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
        "message": "Welcome to AI Construction Product Recommender API",
        "version": "1.0.0",
        "status": "healthy",
        "endpoints": {
            "recommendations": "/api/v1/recommend/{product_id}",
            "products": "/api/v1/products",
            "user_recommendations": "/api/v1/users/{user_id}/recommendations",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "message": "AI Recommender API is running",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/api/v1/recommend/{product_id}")
async def get_recommendations(
    product_id: str, 
    top_n: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get AI-based product recommendations for a given construction product ID
    
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
        data={
            "product_id": product_id,
            "recommendations": recommendations
        }
    )

@app.get("/api/v1/products", response_model=PaginatedProductsResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of products per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """Get paginated construction products with optional category filtering"""
    
    # Build query
    query = db.query(Product)
    
    # Apply category filter if provided
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()
    
    # Get images for each product
    product_responses = []
    for product in products:
        images = db.query(ProductImage).filter(ProductImage.product_id == product.id).all()
        
        # Convert images to response format
        image_responses = []
        for img in images:
            image_responses.append(ProductImageResponse(
                id=img.id,
                url=img.url,
                alt=img.alt,
                isDefault=bool(img.is_default),
                createdAt=img.created_at.isoformat() + "Z",
                updatedAt=img.updated_at.isoformat() + "Z",
                productId=img.product_id
            ))
        
        product_responses.append(ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            category=product.category,
            images=image_responses
        ))
    
    # Calculate pagination info
    total_pages = (total + limit - 1) // limit
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedProductsResponse(
        data=product_responses,
        pagination={
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total,
            "items_per_page": limit,
            "has_next": has_next,
            "has_prev": has_prev
        }
    )

@app.post("/api/v1/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new construction product with user interaction data"""
    
    # Set interaction weight based on interaction type
    weight_map = {
        'view': 1.0,
        'click': 2.0,
        'add_to_cart': 5.0,
        'purchase': 10.0
    }
    
    interaction_weight = weight_map.get(product.interaction_type, product.interaction_weight or 1.0)
    
    new_product = Product(
        product_id=product.product_id,
        name=product.name,
        description=product.description,
        category=product.category,
        price=product.price,
        stock=product.stock,
        user_id=product.user_id,
        interaction_weight=interaction_weight,
        interaction_type=product.interaction_type
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    # Refit the recommender with new data
    recommender.fit(db)
    
    return ProductResponse(
        id=new_product.id,
        product_id=new_product.product_id,
        name=new_product.name,
        description=new_product.description,
        price=new_product.price,
        stock=new_product.stock,
        category=new_product.category,
        user_id=new_product.user_id,
        interaction_weight=new_product.interaction_weight,
        interaction_type=new_product.interaction_type,
        images=[]
    )

@app.delete("/api/v1/products/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete a construction product by ID"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete associated images first
    db.query(ProductImage).filter(ProductImage.product_id == product_id).delete()
    
    # Delete the product
    db.delete(product)
    db.commit()
    
    # Refit the recommender with updated data
    recommender.fit(db)
    
    return {"success": True, "message": f"Product {product_id} deleted successfully"}

@app.get("/api/v1/users/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: str,
    top_n: int = 5,
    db: Session = Depends(get_db)
):
    """Get personalized recommendations for a specific user based on their product interactions"""
    
    # Get user's products with interaction data
    user_products = db.query(Product).filter(
        Product.user_id == user_id
    ).order_by(Product.interaction_weight.desc(), Product.created_at.desc()).limit(20).all()
    
    if not user_products:
        # If no user products, return popular products (highest interaction weight)
        popular_products = db.query(Product).filter(
            Product.interaction_weight.isnot(None)
        ).order_by(Product.interaction_weight.desc()).limit(top_n).all()
        
        if not popular_products:
            # Fallback to newest products
            popular_products = db.query(Product).order_by(Product.created_at.desc()).limit(top_n).all()
        
        return RecommendationResponse(
            data={
                "user_id": user_id,
                "type": "popular",
                "recommendations": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "category": product.category,
                        "price": product.price,
                        "stock": product.stock,
                        "interaction_weight": product.interaction_weight,
                        "interaction_type": product.interaction_type,
                        "similarity_score": 0.0
                    }
                    for product in popular_products
                ]
            }
        )
    
    # Get AI recommendations for each user product
    all_recommendations = []
    
    for product in user_products[:5]:  # Top 5 user products by weight
        try:
            recommendations = recommender.get_recommendations(product.id, top_n=3)
            # Boost similarity score based on user interaction weight
            for rec in recommendations:
                boost_factor = (product.interaction_weight or 1.0) * 0.1
                rec['similarity_score'] = min(1.0, rec['similarity_score'] + boost_factor)
                rec['interaction_weight'] = product.interaction_weight
                rec['interaction_type'] = product.interaction_type
            all_recommendations.extend(recommendations)
        except:
            continue
    
    # Remove duplicates and sort by similarity score
    unique_recommendations = []
    seen_ids = set()
    for rec in all_recommendations:
        if rec['id'] not in seen_ids:
            unique_recommendations.append(rec)
            seen_ids.add(rec['id'])
    
    # Sort by similarity score and take top N
    unique_recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
    final_recommendations = unique_recommendations[:top_n]
    
    return RecommendationResponse(
        data={
            "user_id": user_id,
            "type": "personalized",
            "recommendations": final_recommendations,
            "based_on_products": len(user_products)
        }
    )

@app.get("/api/v1/users/{user_id}/products")
async def get_user_products(
    user_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get user's product interaction history"""
    
    products = db.query(Product).filter(
        Product.user_id == user_id
    ).order_by(Product.created_at.desc()).limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "category": product.category,
                "price": product.price,
                "stock": product.stock,
                "interaction_type": product.interaction_type,
                "interaction_weight": product.interaction_weight,
                "created_at": product.created_at.isoformat() + "Z" if product.created_at else None
            }
            for product in products
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
