"""
main.py
=======
Main entry point for the Student Database Management System.
Sets up configuration from credentials.json, tests connection, and lists tables.

Author: Assistant
Date: 2024
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
try:
    from connection import DBConnection
    from student_db_manager import StudentDatabaseManager, QueryExecutor
    from entities.queries import QueryLibrary

    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Error importing modules: {e}")
    print("Please ensure all module files are in the correct location:")
    print("  - connection.py")
    print("  - student_db_manager.py")
    print("  - entities/queries.py")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles database setup and configuration from credentials file."""

    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize database setup.

        Args:
            credentials_file: Path to credentials JSON file
        """
        self.credentials_file = credentials_file
        self.config = None
        self.db_connection = None
        self.manager = None

    def load_credentials(self) -> Dict[str, Any]:
        """
        Load credentials from JSON file.

        Returns:
            Dictionary with database credentials

        Raises:
            FileNotFoundError: If credentials file doesn't exist
            json.JSONDecodeError: If credentials file is invalid
        """
        credentials_path = Path(self.credentials_file)

        if not credentials_path.exists():
            logger.error(f"Credentials file not found: {self.credentials_file}")
            raise FileNotFoundError(
                f"Credentials file '{self.credentials_file}' not found. "
                f"Please create it with your database configuration."
            )

        try:
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
                logger.info(f"Loaded credentials from {self.credentials_file}")
                return credentials
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in credentials file: {e}")
            raise

    def setup_environment_from_credentials(self, credentials: Dict[str, Any]) -> None:
        """
        Set up environment variables from credentials.

        Args:
            credentials: Dictionary with database configuration
        """
        db_config = credentials.get('database', {})

        # Map credentials to environment variables
        env_mapping = {
            'type': 'DB_TYPE',
            'db_type': 'DB_TYPE',
            'host': 'DB_HOST',
            'port': 'DB_PORT',
            'database': 'DB_DATABASE',
            'db_path': 'DB_PATH',
            'username': 'DB_USERNAME',
            'password': 'DB_PASSWORD',
            'connection_timeout': 'DB_TIMEOUT',
            'pool_size': 'DB_POOL_SIZE',
            'echo': 'DB_ECHO'
        }

        for key, env_var in env_mapping.items():
            if key in db_config:
                value = str(db_config[key])
                os.environ[env_var] = value
                if key not in ['password']:  # Don't log passwords
                    logger.debug(f"Set {env_var} = {value}")

        # Set application environment if provided
        app_config = credentials.get('app', {})
        if 'environment' in app_config:
            os.environ['APP_ENV'] = app_config['environment']
            logger.info(f"Set APP_ENV = {app_config['environment']}")

    def get_connection_string(self, credentials: Dict[str, Any]) -> str:
        """
        Get the database connection string from credentials.

        Args:
            credentials: Dictionary with database configuration

        Returns:
            Connection string for the database
        """
        db_config = credentials.get('database', {})
        db_type = db_config.get('type', 'sqlite').lower()

        if db_type == 'sqlite':
            return db_config.get('db_path', db_config.get('database', 'student.db'))
        elif db_type == 'mysql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 3306)
            database = db_config.get('database', 'student_db')
            username = db_config.get('username', 'root')
            password = db_config.get('password', '')
            return f"mysql://{username}:{password}@{host}:{port}/{database}"
        elif db_type == 'postgresql':
            host = db_config.get('host', 'localhost')
            port = db_config.get('port', 5432)
            database = db_config.get('database', 'student_db')
            username = db_config.get('username', 'postgres')
            password = db_config.get('password', '')
            return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            return db_config.get('db_path', ':memory:')

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Load credentials
            credentials = self.load_credentials()
            self.config = credentials

            # Setup environment
            self.setup_environment_from_credentials(credentials)

            # Get connection string
            conn_string = self.get_connection_string(credentials)
            logger.info(f"Connecting to database: {conn_string}")

            # Create connection
            self.db_connection = DBConnection(db_path=conn_string)

            # Test connection
            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result:
                    logger.info("✓ Database connection successful")
                    return True
                else:
                    logger.error("✗ Database connection test failed")
                    return False

        except Exception as e:
            logger.error(f"✗ Connection failed: {e}")
            return False

    def list_tables(self) -> Dict[str, int]:
        """
        List all tables in the database with their record counts.

        Returns:
            Dictionary with table names and record counts
        """
        tables = {}

        try:
            if not self.db_connection:
                self.test_connection()

            with self.db_connection.get_connection() as conn:
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)

                table_names = cursor.fetchall()

                for (table_name,) in table_names:
                    # Get record count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    tables[table_name] = count

                logger.info(f"Found {len(tables)} tables in database")

        except Exception as e:
            logger.error(f"Error listing tables: {e}")

        return tables

    def check_schema_exists(self) -> bool:
        """
        Check if the database schema exists.

        Returns:
            True if schema exists, False otherwise
        """
        expected_tables = [
            'Students', 'Teachers', 'Courses', 'EvaluationComponents',
            'Evaluations', 'Grades', 'Tutorials', 'Bans'
        ]

        tables = self.list_tables()
        existing_tables = set(tables.keys())
        expected_set = set(expected_tables)

        missing_tables = expected_set - existing_tables

        if not missing_tables:
            logger.info("✓ All expected tables exist")
            return True
        else:
            logger.warning(f"Missing tables: {missing_tables}")
            return False

    def initialize_database(self, force: bool = False) -> bool:
        """
        Initialize the database schema if needed.

        Args:
            force: Force recreation of schema even if it exists

        Returns:
            True if successful
        """
        try:
            if not self.db_connection:
                self.test_connection()

            # Create manager
            conn_string = self.get_connection_string(self.config)
            self.manager = StudentDatabaseManager(db_path=conn_string)

            if force or not self.check_schema_exists():
                logger.info("Initializing database schema...")

                # Create schema
                if self.manager.create_schema():
                    logger.info("✓ Database schema created successfully")
                    return True
                else:
                    logger.error("✗ Failed to create database schema")
                    return False
            else:
                logger.info("Database schema already exists")
                return True

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

    def display_summary(self) -> None:
        """Display a summary of the database setup."""
        print("\n" + "=" * 70)
        print("DATABASE SETUP SUMMARY")
        print("=" * 70)

        # Configuration
        if self.config:
            db_config = self.config.get('database', {})
            print("\n📋 Configuration:")
            print(f"   Type: {db_config.get('type', 'sqlite')}")

            if db_config.get('type') == 'sqlite':
                print(f"   Path: {db_config.get('db_path', db_config.get('database'))}")
            else:
                print(f"   Host: {db_config.get('host', 'localhost')}")
                print(f"   Port: {db_config.get('port', 'N/A')}")
                print(f"   Database: {db_config.get('database', 'N/A')}")
                print(f"   Username: {db_config.get('username', 'N/A')}")

            print(f"   Timeout: {db_config.get('connection_timeout', 30)} seconds")

        # Connection status
        print("\n🔌 Connection Status:")
        if self.test_connection():
            print("   ✓ Connected successfully")
        else:
            print("   ✗ Connection failed")
            return

        # Tables
        print("\n📊 Database Tables:")
        tables = self.list_tables()

        if tables:
            total_records = 0
            for table_name, count in sorted(tables.items()):
                print(f"   {table_name:25} {count:6} records")
                total_records += count

            print(f"   {'─' * 33}")
            print(f"   {'Total':25} {total_records:6} records")
        else:
            print("   No tables found")

        # Schema check
        print("\n✅ Schema Validation:")
        if self.check_schema_exists():
            print("   All required tables present")
        else:
            print("   Some tables missing - run with --init to create schema")

        print("\n" + "=" * 70)


def create_sample_credentials_file():
    """Create a sample credentials.json file for reference."""

    sample_credentials = {
        "database": {
            "type": "sqlite",
            "db_path": "student_database.db",
            "database": "student_database.db",
            "connection_timeout": 30,
            "pool_size": 5,
            "echo": False
        },
        "app": {
            "environment": "development",
            "debug": False,
            "log_level": "INFO"
        }
    }

    # For MySQL example
    mysql_example = {
        "database": {
            "type": "mysql",
            "host": "localhost",
            "port": 3306,
            "database": "student_db",
            "username": "your_username",
            "password": "your_password",
            "connection_timeout": 30,
            "pool_size": 5,
            "echo": False
        },
        "app": {
            "environment": "production",
            "debug": False,
            "log_level": "INFO"
        }
    }

    if not Path('credentials.example.json').exists():
        with open('credentials.example.json', 'w') as f:
            json.dump(sample_credentials, f, indent=2)
        print("✓ Created credentials.example.json (SQLite example)")

    if not Path('credentials.mysql.example.json').exists():
        with open('credentials.mysql.example.json', 'w') as f:
            json.dump(mysql_example, f, indent=2)
        print("✓ Created credentials.mysql.example.json (MySQL example)")


def main():
    """Main entry point for the application."""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Student Database Management System Setup'
    )
    parser.add_argument(
        '--credentials',
        default='credentials.json',
        help='Path to credentials JSON file (default: credentials.json)'
    )
    parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize database schema'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force recreation of schema (WARNING: destroys existing data)'
    )
    parser.add_argument(
        '--sample-data',
        action='store_true',
        help='Insert sample data after initialization'
    )
    parser.add_argument(
        '--create-examples',
        action='store_true',
        help='Create example credentials files'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create example files if requested
    if args.create_examples:
        create_sample_credentials_file()
        return

    # Header
    print("\n" + "=" * 70)
    print("STUDENT DATABASE MANAGEMENT SYSTEM")
    print("Minimal Setup and Connection Test")
    print("=" * 70)

    # Setup database
    setup = DatabaseSetup(args.credentials)

    try:
        # Test connection
        print("\n🔧 Testing database connection...")
        if not setup.test_connection():
            print("\n❌ Failed to connect to database.")
            print("Please check your credentials.json file.")
            if not Path(args.credentials).exists():
                print(f"\n'{args.credentials}' not found.")
                print("Run with --create-examples to create sample files.")
            sys.exit(1)

        print("✅ Connection successful!")

        # Initialize schema if requested
        if args.init:
            print("\n🔧 Initializing database schema...")
            if setup.initialize_database(force=args.force):
                print("✅ Schema initialized successfully!")

                # Insert sample data if requested
                if args.sample_data:
                    print("\n🔧 Inserting sample data...")
                    if setup.manager and setup.manager.insert_sample_data():
                        print("✅ Sample data inserted successfully!")
                    else:
                        print("❌ Failed to insert sample data")
            else:
                print("❌ Failed to initialize schema")

        # Display summary
        setup.display_summary()

        # Additional information
        print("\n📝 Next Steps:")
        if not setup.check_schema_exists():
            print("   1. Run with --init to create database schema")
            print("   2. Run with --init --sample-data to include test data")
        else:
            print("   • Database is ready to use!")
            print("   • Run student_db_manager.py for full demo")
            print("   • Use --sample-data to add test data")

        print("\n💡 Examples:")
        print("   python main.py --init                    # Create schema")
        print("   python main.py --init --sample-data      # Create with test data")
        print("   python main.py --create-examples         # Create example files")
        print("   python main.py --verbose                 # Show detailed logs")

    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()