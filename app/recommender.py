import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from .models import Product
from typing import List, Dict, Any

class ProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.similarity_matrix = None
        self.products_df = None
        self.product_ids = None
    
    def fit(self, db: Session):
        """Fit the recommendation model with products from database"""
        # Fetch all products from database
        products = db.query(Product).all()
        
        if not products:
            return
        
        # Convert to DataFrame
        self.products_df = pd.DataFrame([
            {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'price': product.price
            }
            for product in products
        ])
        
        # Create feature vectors combining category and price
        # Normalize price to 0-1 range for better similarity calculation
        max_price = self.products_df['price'].max()
        min_price = self.products_df['price'].min()
        price_range = max_price - min_price if max_price != min_price else 1
        
        normalized_price = (self.products_df['price'] - min_price) / price_range
        
        # Combine category and normalized price as text features
        features = self.products_df['category'] + ' ' + normalized_price.astype(str)
        
        # Create TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(features)
        
        # Calculate cosine similarity matrix
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        self.product_ids = self.products_df['id'].tolist()
    
    def get_recommendations(self, product_id: int, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top N similar products for a given product ID"""
        if self.similarity_matrix is None or self.product_ids is None:
            return []
        
        try:
            # Find the index of the product
            product_index = self.product_ids.index(product_id)
            
            # Get similarity scores for this product
            similarity_scores = self.similarity_matrix[product_index]
            
            # Get indices of most similar products (excluding the product itself)
            similar_indices = np.argsort(similarity_scores)[::-1][1:top_n+1]
            
            # Get product details for recommendations
            recommendations = []
            for idx in similar_indices:
                if idx < len(self.products_df):
                    product = self.products_df.iloc[idx]
                    recommendations.append({
                        'id': int(product['id']),
                        'name': product['name'],
                        'category': product['category'],
                        'price': float(product['price']),
                        'similarity_score': float(similarity_scores[idx])
                    })
            
            return recommendations
            
        except (ValueError, IndexError):
            return []

# Global recommender instance
recommender = ProductRecommender()
