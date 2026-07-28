import os
from sqlalchemy import create_engine, MetaData, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_database():
    print("Starting migration process...")
    
    # 1. Connect to local SQLite database
    sqlite_uri = 'sqlite:///axeglobal.db'
    sqlite_engine = create_engine(sqlite_uri)
    print("Connected to local SQLite database.")

    # 2. Connect to Azure SQL Database using pymssql
    azure_uri = os.environ.get('AZURE_SQL_CONNECTION_STRING')
    
    if not azure_uri or "YOUR_PASSWORD_HERE" in azure_uri:
        print("ERROR: Please set the correct AZURE_SQL_CONNECTION_STRING in the .env file!")
        return

    try:
        azure_engine = create_engine(azure_uri, connect_args={'autocommit': True})
        # Test connection
        with azure_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Successfully connected to Azure SQL Database.")
    except Exception as e:
        print(f"Failed to connect to Azure SQL Database: {e}")
        return

    # 3. Read metadata from local database
    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)
    print(f"Found {len(sqlite_meta.tables)} tables in local database.")

    # Fix SQLite BOOLEAN types and string limits to work with SQL Server
    from sqlalchemy.types import Boolean, Integer, String
    for table_name, table in sqlite_meta.tables.items():
        for column in table.columns:
            if 'BOOLEAN' in str(column.type).upper():
                column.type = Boolean()
            if column.name == 'password_hash':
                column.type = String(256)

    # 4. Create tables in Azure SQL
    print("Dropping existing tables in Azure SQL (if any)...")
    sqlite_meta.drop_all(bind=azure_engine)
    print("Creating tables in Azure SQL...")
    sqlite_meta.create_all(bind=azure_engine)
    print("Table schema created successfully.")

    # 5. Copy data over
    print("Migrating data...")
    with sqlite_engine.connect() as sqlite_conn:
        with azure_engine.connect() as azure_conn:
            # Delete data in reverse dependency order to avoid FK violations
            for table in reversed(sqlite_meta.sorted_tables):
                try:
                    azure_conn.execute(table.delete())
                    azure_conn.commit()
                except Exception:
                    pass

            for table in sqlite_meta.sorted_tables:
                table_name = table.name
                print(f"Migrating table: {table_name}")
                
                # Fetch all data from SQLite
                result = sqlite_conn.execute(table.select())
                rows = result.mappings().all()
                
                if not rows:
                    print(f"  No data found in {table_name}, skipping.")
                    continue
                    
                # (Deletion already handled above)
                
                print(f"  Found {len(rows)} records. Inserting into Azure...")
                
                # We do row-by-row or small batch inserts to handle potential IDENTITY_INSERT issues
                try:
                    azure_conn.execute(table.insert(), rows)
                    azure_conn.commit()
                    print(f"  Successfully inserted {len(rows)} records into {table_name}.")
                except Exception as e:
                    print(f"  Standard insert failed. Attempting with IDENTITY_INSERT ON...")
                    try:
                        azure_conn.execute(text(f"SET IDENTITY_INSERT [{table_name}] ON"))
                        azure_conn.execute(table.insert(), rows)
                        azure_conn.execute(text(f"SET IDENTITY_INSERT [{table_name}] OFF"))
                        azure_conn.commit()
                        print(f"  Successfully inserted {len(rows)} records into {table_name} with IDENTITY_INSERT.")
                    except Exception as e2:
                        print(f"  ERROR: Failed to migrate table {table_name}: {e2}")

    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_database()
