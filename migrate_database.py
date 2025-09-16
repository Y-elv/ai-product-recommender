#!/usr/bin/env python3
"""
Database migration script to add missing columns to the products table
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/ai_recommender_db")

def migrate_database():
    """Add missing columns to the products table"""
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if products table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'products'
                );
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("Products table doesn't exist. Creating it...")
                # Create the table with all columns
                connection.execute(text("""
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
                """))
                print("✅ Products table created successfully!")
            else:
                print("Products table exists. Adding missing columns...")
                
                # Add missing columns one by one
                columns_to_add = [
                    ("description", "TEXT"),
                    ("stock", "INTEGER DEFAULT 0"),
                    ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                    ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                ]
                
                for column_name, column_type in columns_to_add:
                    try:
                        # Check if column exists
                        result = connection.execute(text(f"""
                            SELECT EXISTS (
                                SELECT FROM information_schema.columns 
                                WHERE table_schema = 'public' 
                                AND table_name = 'products' 
                                AND column_name = '{column_name}'
                            );
                        """))
                        column_exists = result.scalar()
                        
                        if not column_exists:
                            connection.execute(text(f"ALTER TABLE products ADD COLUMN {column_name} {column_type};"))
                            print(f"✅ Added column: {column_name}")
                        else:
                            print(f"⚠️  Column {column_name} already exists")
                            
                    except Exception as e:
                        print(f"❌ Error adding column {column_name}: {e}")
                
                # Update existing records to have current timestamp
                connection.execute(text("""
                    UPDATE products 
                    SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                    WHERE created_at IS NULL OR updated_at IS NULL;
                """))
                
                print("✅ Database migration completed successfully!")
        
        # Create product_images table
        with engine.connect() as connection:
            # Check if product_images table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'product_images'
                );
            """))
            images_table_exists = result.scalar()
            
            if not images_table_exists:
                print("Creating product_images table...")
                connection.execute(text("""
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
                """))
                print("✅ Product_images table created successfully!")
            else:
                print("⚠️  Product_images table already exists")
        
        print("\n🎉 Database migration completed! You can now run the FastAPI application.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
