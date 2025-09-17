#!/usr/bin/env python3
"""
Database migration script to add user interaction fields to products table
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate_products_interaction():
    """Add user interaction fields to products table"""
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
        
        print("🔄 Adding user interaction fields to products table...")
        
        # Check if products table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'products'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("❌ Products table doesn't exist. Please create it first.")
            return
        
        # Add new columns
        columns_to_add = [
            ("product_id", "VARCHAR"),
            ("user_id", "VARCHAR"),
            ("interaction_weight", "FLOAT DEFAULT 1.0"),
            ("interaction_type", "VARCHAR")
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
        
        # Create indexes for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_product_id ON products(product_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_interaction_weight ON products(interaction_weight);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_interaction_type ON products(interaction_type);")
            print("✅ Created indexes for new columns")
        except Exception as e:
            print(f"⚠️  Error creating indexes: {e}")
        
        conn.commit()
        print("\n🎉 Products table migration completed successfully!")
        print("✅ Your FastAPI application is now ready to use interaction-based recommendations!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_products_interaction()
