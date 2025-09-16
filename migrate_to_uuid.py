#!/usr/bin/env python3
"""
Database migration script to convert products table to use UUIDs
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate_to_uuid():
    """Convert products table to use UUIDs"""
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
        
        print("🔄 Starting migration to UUID...")
        
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
            print("📝 Creating products table with UUID...")
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
            print("✅ Products table created successfully!")
        else:
            print("📝 Products table exists. Checking structure...")
            
            # Check if id column is already VARCHAR (UUID)
            cursor.execute("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'products' 
                AND column_name = 'id';
            """)
            result = cursor.fetchone()
            
            if result and result[0] == 'character varying':
                print("✅ ID column is already VARCHAR (UUID compatible)")
            else:
                print("🔄 Converting ID column to VARCHAR for UUIDs...")
                
                # Add new UUID column
                cursor.execute("ALTER TABLE products ADD COLUMN id_new VARCHAR;")
                
                # Generate UUIDs for existing records
                cursor.execute("""
                    UPDATE products 
                    SET id_new = gen_random_uuid()::text;
                """)
                
                # Drop old id column and rename new one
                cursor.execute("ALTER TABLE products DROP COLUMN id;")
                cursor.execute("ALTER TABLE products RENAME COLUMN id_new TO id;")
                cursor.execute("ALTER TABLE products ADD PRIMARY KEY (id);")
                
                print("✅ ID column converted to UUID format")
            
            # Add missing columns if they don't exist
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
        
        # Create product_images table
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'product_images'
            );
        """)
        images_table_exists = cursor.fetchone()[0]
        
        if not images_table_exists:
            print("📝 Creating product_images table...")
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
            print("✅ Product_images table created successfully!")
        else:
            print("⚠️  Product_images table already exists")
        
        conn.commit()
        print("\n🎉 Database migration to UUID completed successfully!")
        print("✅ Your FastAPI application should now work with UUID-based products!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_to_uuid()
