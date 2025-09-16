#!/usr/bin/env python3
"""
Simple script to add missing columns to existing products table
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def add_columns():
    """Add missing columns to the products table"""
    try:
        # Parse DATABASE_URL
        # Format: postgresql://user:password@host:port/database
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
        
        # Add missing columns
        columns_to_add = [
            ("description", "TEXT"),
            ("stock", "INTEGER DEFAULT 0"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                # Check if column exists
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'products' 
                        AND column_name = '{column_name}'
                    );
                """)
                column_exists = cursor.fetchone()[0]
                
                if not column_exists:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {column_name} {column_type};")
                    print(f"✅ Added column: {column_name}")
                else:
                    print(f"⚠️  Column {column_name} already exists")
                    
            except Exception as e:
                print(f"❌ Error adding column {column_name}: {e}")
        
        # Update existing records to have current timestamp
        cursor.execute("""
            UPDATE products 
            SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
            WHERE created_at IS NULL OR updated_at IS NULL;
        """)
        
        conn.commit()
        print("✅ Database columns added successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_columns()
