#!/usr/bin/env python3
"""
Script to drop and recreate the products table with UUID structure
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def reset_database():
    """Drop and recreate products table with UUID structure"""
    try:
        # Parse DATABASE_URL
        url_parts = DATABASE_URL.replace("postgresql://", "").split("/")
        db_name = url_parts[1].split("?")[0]  # Remove query parameters
        auth_parts = url_parts[0].split("@")
        user_pass = auth_parts[0].split(":")
        host_port = auth_parts[1].split(":")
        
        user = user_pass[0]
        password = user_pass[1]
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=db_name,
            user=user,
            password=password
        )
        
        cursor = conn.cursor()
        
        print("🗑️  Dropping existing products table...")
        
        # Drop existing tables (in correct order due to foreign keys)
        cursor.execute("DROP TABLE IF EXISTS product_images CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS products CASCADE;")
        
        print("✅ Existing tables dropped successfully!")
        
        print("📝 Creating new products table with UUID structure...")
        
        # Create products table with UUID
        cursor.execute("""
            CREATE TABLE products (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                price FLOAT NOT NULL,
                stock INTEGER DEFAULT 0,
                category VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        print("✅ Products table created with UUID structure!")
        
        print("📝 Creating product_images table...")
        
        # Create product_images table
        cursor.execute("""
            CREATE TABLE product_images (
                id VARCHAR PRIMARY KEY,
                url VARCHAR NOT NULL,
                alt VARCHAR,
                is_default INTEGER DEFAULT 0,
                product_id VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
        """)
        
        print("✅ Product_images table created!")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_images_product_id ON product_images(product_id);")
        
        print("✅ Indexes created for better performance!")
        
        conn.commit()
        
        print("\n🎉 Database reset completed successfully!")
        print("✅ Your FastAPI application is now ready to work with UUIDs!")
        print("✅ You can now run: uvicorn app.main:app --reload")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete all existing data in the products table!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() in ['yes', 'y']:
        reset_database()
    else:
        print("❌ Database reset cancelled.")
