import os
from sqlalchemy import create_engine, MetaData, text
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    print("Starting data migration process...")
    sqlite_uri = 'sqlite:///axeglobal.db'
    sqlite_engine = create_engine(sqlite_uri)
    azure_uri = os.environ.get('AZURE_SQL_CONNECTION_STRING')
    azure_engine = create_engine(azure_uri, connect_args={'autocommit': True})

    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)

    with azure_engine.connect() as azure_conn:
        # 1. Disable all foreign key constraints in Azure SQL to avoid dependency issues
        print("Disabling all foreign key constraints...")
        for table_name in sqlite_meta.tables.keys():
            try:
                azure_conn.execute(text(f"ALTER TABLE [{table_name}] NOCHECK CONSTRAINT all"))
            except Exception:
                pass

        # 2. Fix the user table password_hash length limitation
        print("Increasing password_hash column length to 256...")
        try:
            azure_conn.execute(text("ALTER TABLE [user] ALTER COLUMN password_hash VARCHAR(256)"))
        except Exception as e:
            print("  (Warning: Could not alter column, might already be done or table missing)")

        # 3. Migrate data
        print("Copying data...")
        with sqlite_engine.connect() as sqlite_conn:
            for table_name, table in sqlite_meta.tables.items():
                print(f"Migrating table: {table_name}")
                
                # Delete existing data
                try:
                    azure_conn.execute(text(f"DELETE FROM [{table_name}]"))
                except Exception:
                    pass

                # Fetch from SQLite
                result = sqlite_conn.execute(table.select())
                rows = result.mappings().all()
                if not rows:
                    print(f"  No data found in {table_name}, skipping.")
                    continue
                
                print(f"  Inserting {len(rows)} rows...")
                try:
                    # Enable identity insert and do the insert
                    azure_conn.execute(text(f"SET IDENTITY_INSERT [{table_name}] ON"))
                    azure_conn.execute(table.insert(), rows)
                    azure_conn.execute(text(f"SET IDENTITY_INSERT [{table_name}] OFF"))
                    print(f"  Success!")
                except Exception as e:
                    print(f"  ERROR inserting into {table_name}: {e}")

        # 4. Re-enable all foreign key constraints
        print("Re-enabling all foreign key constraints...")
        for table_name in sqlite_meta.tables.keys():
            try:
                azure_conn.execute(text(f"ALTER TABLE [{table_name}] WITH CHECK CHECK CONSTRAINT all"))
            except Exception as e:
                print(f"  Warning during re-enabling constraints for {table_name}: {e}")

    print("\nMigration completed successfully!")

if __name__ == "__main__":
    migrate_database()
