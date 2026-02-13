"""
Migration script: Add folders support to existing Tag Tracker database.

Run this ONCE if you already have data in your database.
If starting fresh, this is not needed - the app creates tables automatically.

Usage:
    python migrate_add_folders.py
"""
import os
import sys

def migrate():
    database_url = os.environ.get('DATABASE_URL', '')
    
    if database_url:
        # PostgreSQL (Heroku)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Create folders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS folders (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add folder_id column to tags if it doesn't exist
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='tags' AND column_name='folder_id'
                    ) THEN
                        ALTER TABLE tags ADD COLUMN folder_id INTEGER REFERENCES folders(id);
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='tags' AND column_name='price'
                    ) THEN
                        ALTER TABLE tags ADD COLUMN price VARCHAR(20);
                    END IF;
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='tags' AND column_name='source'
                    ) THEN
                        ALTER TABLE tags ADD COLUMN source VARCHAR(50);
                    END IF;
                END $$;
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            print("PostgreSQL migration completed successfully!")
            
        except ImportError:
            print("psycopg2 not installed. Run: pip install psycopg2-binary")
            sys.exit(1)
    else:
        # SQLite (local)
        import sqlite3
        
        db_path = os.path.join(os.path.dirname(__file__), 'instance', 'tag_tracker.db')
        if not os.path.exists(db_path):
            print(f"No database found at {db_path}. Starting fresh - no migration needed.")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if folder_id column exists in tags
        cursor.execute("PRAGMA table_info(tags)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'folder_id' not in columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN folder_id INTEGER REFERENCES folders(id)")
            print("Added folder_id column to tags table.")
        else:
            print("folder_id column already exists.")
        
        if 'price' not in columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN price VARCHAR(20)")
            print("Added price column to tags table.")
        else:
            print("price column already exists.")
        
        if 'source' not in columns:
            cursor.execute("ALTER TABLE tags ADD COLUMN source VARCHAR(50)")
            print("Added source column to tags table.")
        else:
            print("source column already exists.")
        
        conn.commit()
        conn.close()
        print("SQLite migration completed successfully!")

if __name__ == '__main__':
    migrate()
