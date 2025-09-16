import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from .models import Product
from typing import List, Dict, Any
import re

class ConstructionProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.similarity_matrix = None
        self.products_df = None
        self.product_ids = None
        
        # Construction-specific categories for better recommendations
        self.construction_categories = {
            'cement': ['cement', 'concrete', 'mortar', 'grout'],
            'steel': ['steel', 'rebar', 'beam', 'column', 'rod'],
            'lumber': ['wood', 'lumber', 'timber', 'board', 'plank'],
            'electrical': ['wire', 'cable', 'switch', 'outlet', 'fixture'],
            'plumbing': ['pipe', 'valve', 'fitting', 'faucet', 'toilet'],
            'roofing': ['shingle', 'tile', 'gutter', 'drain', 'roof'],
            'flooring': ['tile', 'carpet', 'hardwood', 'laminate', 'vinyl'],
            'tools': ['hammer', 'drill', 'saw', 'level', 'tool'],
            'safety': ['helmet', 'glove', 'goggle', 'vest', 'boot']
        }
    
    def _extract_construction_features(self, name: str, description: str, category: str) -> str:
        """Extract construction-specific features from product data"""
        # Combine name, description, and category
        text = f"{name} {description} {category}".lower()
        
        # Add category-specific keywords
        for main_cat, keywords in self.construction_categories.items():
            if any(keyword in text for keyword in keywords):
                text += f" {main_cat}"
        
        # Extract material keywords
        materials = ['concrete', 'steel', 'wood', 'plastic', 'metal', 'ceramic', 'glass', 'rubber']
        for material in materials:
            if material in text:
                text += f" {material}"
        
        # Extract size/measurement keywords
        size_patterns = [r'\d+\s*(inch|ft|feet|meter|cm|mm)', r'\d+x\d+', r'\d+\s*lb', r'\d+\s*kg']
        for pattern in size_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                text += f" {match}"
        
        return text
    
    def fit(self, db: Session):
        """Fit the recommendation model with construction products from database"""
        # Fetch all products from database
        products = db.query(Product).all()
        
        if not products:
            return
        
        # Convert to DataFrame
        self.products_df = pd.DataFrame([
            {
                'id': product.id,
                'name': product.name,
                'description': product.description or '',
                'category': product.category,
                'price': product.price,
                'stock': product.stock
            }
            for product in products
        ])
        
        # Create enhanced feature vectors for construction products
        features = []
        for _, product in self.products_df.iterrows():
            feature_text = self._extract_construction_features(
                product['name'], 
                product['description'], 
                product['category']
            )
            features.append(feature_text)
        
        # Normalize price for better similarity calculation
        max_price = self.products_df['price'].max()
        min_price = self.products_df['price'].min()
        price_range = max_price - min_price if max_price != min_price else 1
        normalized_price = (self.products_df['price'] - min_price) / price_range
        
        # Add price tier information
        price_tier = pd.cut(normalized_price, bins=5, labels=['budget', 'economy', 'mid', 'premium', 'luxury'])
        
        # Combine features with price tier
        enhanced_features = []
        for i, feature in enumerate(features):
            enhanced_feature = f"{feature} {price_tier.iloc[i]}"
            enhanced_features.append(enhanced_feature)
        
        # Create TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(enhanced_features)
        
        # Calculate cosine similarity matrix
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        self.product_ids = self.products_df['id'].tolist()
    
    def get_recommendations(self, product_id: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get top N similar construction products for a given product ID"""
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
                        'id': str(product['id']),
                        'name': product['name'],
                        'description': product['description'],
                        'category': product['category'],
                        'price': float(product['price']),
                        'stock': int(product['stock']),
                        'similarity_score': float(similarity_scores[idx])
                    })
            
            return recommendations
            
        except (ValueError, IndexError):
            return []

# Global recommender instance
recommender = ConstructionProductRecommender()
