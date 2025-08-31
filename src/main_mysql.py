"""
main_mysql.py
=============
Main entry point for MySQL database connection.
Handles remote MySQL database setup and connection testing.

Author: Assistant
Date: 2024
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import warnings

# Try to import MySQL connector
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError

    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("⚠️  MySQL connector not installed.")
    print("Install it with: pip install mysql-connector-python")

# Try to import pymysql as alternative
try:
    import pymysql

    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

# Import pandas for data handling
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  Pandas not installed.")
    print("Install it with: pip install pandas")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mysql_connection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore')


class MySQLDatabaseManager:
    """Manages MySQL database connections and operations."""

    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize MySQL database manager.

        Args:
            credentials_file: Path to credentials JSON file
        """
        self.credentials_file = credentials_file
        self.connection = None
        self.config = None

    def load_credentials(self) -> Dict[str, Any]:
        """Load credentials from JSON file."""
        if not Path(self.credentials_file).exists():
            raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")

        with open(self.credentials_file, 'r') as f:
            credentials = json.load(f)

        self.config = credentials.get('database', {})

        # Fix the type if it's incorrectly set
        if self.config.get('host') and self.config.get('username'):
            self.config['type'] = 'mysql'

        logger.info(f"Loaded credentials for {self.config.get('type', 'unknown')} database")
        return credentials

    def get_mysql_config(self) -> Dict[str, Any]:
        """Get MySQL connection configuration."""
        if not self.config:
            self.load_credentials()

        mysql_config = {
            'host': self.config.get('host', 'localhost'),
            'port': self.config.get('port', 3306),
            'database': self.config.get('database'),
            'user': self.config.get('username'),
            'password': self.config.get('password'),
            'connection_timeout': self.config.get('connection_timeout', 30),
            'autocommit': True
        }

        return mysql_config

    def test_connection(self) -> bool:
        """Test MySQL database connection."""
        print("\n🔌 Testing MySQL Connection...")
        print("=" * 50)

        try:
            config = self.get_mysql_config()

            # Display connection info (without password)
            print(f"Host: {config['host']}")
            print(f"Port: {config['port']}")
            print(f"Database: {config['database']}")
            print(f"User: {config['user']}")
            print("-" * 50)

            if MYSQL_AVAILABLE:
                # Try mysql-connector-python
                self.connection = mysql.connector.connect(**config)

                if self.connection.is_connected():
                    cursor = self.connection.cursor()
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    print(f"✅ Connected to MySQL Server")
                    print(f"   Version: {version}")
                    print(f"   Database: {config['database']}")
                    cursor.close()
                    return True

            elif PYMYSQL_AVAILABLE:
                # Try pymysql
                connection_params = {
                    'host': config['host'],
                    'port': int(config['port']),
                    'database': config['database'],
                    'user': config['user'],
                    'password': config['password'],
                    'connect_timeout': config['connection_timeout']
                }
                self.connection = pymysql.connect(**connection_params)

                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    print(f"✅ Connected to MySQL Server (via PyMySQL)")
                    print(f"   Version: {version}")
                    print(f"   Database: {config['database']}")
                return True
            else:
                print("❌ No MySQL driver available")
                print("Install one of these:")
                print("   pip install mysql-connector-python")
                print("   pip install pymysql")
                return False

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            logger.error(f"MySQL connection failed: {e}")
            return False

    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables in the MySQL database."""
        tables = []

        try:
            if not self.connection:
                if not self.test_connection():
                    return tables

            if MYSQL_AVAILABLE and hasattr(self.connection, 'cursor'):
                cursor = self.connection.cursor()
            elif PYMYSQL_AVAILABLE:
                cursor = self.connection.cursor()
            else:
                return tables

            # Get all tables
            cursor.execute("SHOW TABLES")
            table_names = cursor.fetchall()

            for (table_name,) in table_names:
                # Get table info
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                count = cursor.fetchone()[0]

                cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
                columns = cursor.fetchall()

                tables.append({
                    'name': table_name,
                    'records': count,
                    'columns': len(columns)
                })

            cursor.close()

        except Exception as e:
            logger.error(f"Error listing tables: {e}")

        return tables

    def check_student_schema(self) -> Dict[str, bool]:
        """Check if student database schema exists."""
        expected_tables = [
            'Students', 'Teachers', 'Courses', 'EvaluationComponents',
            'Evaluations', 'Grades', 'Tutorials', 'Bans'
        ]

        tables = self.list_tables()
        existing_tables = [t['name'] for t in tables]

        schema_status = {}
        for table in expected_tables:
            schema_status[table] = table in existing_tables

        return schema_status

    def create_student_schema(self) -> bool:
        """Create the student database schema for MySQL."""
        print("\n📝 Creating Student Database Schema...")
        print("=" * 50)

        try:
            if not self.connection:
                if not self.test_connection():
                    return False

            if MYSQL_AVAILABLE:
                cursor = self.connection.cursor()
            elif PYMYSQL_AVAILABLE:
                cursor = self.connection.cursor()
            else:
                return False

            # MySQL-compatible schema
            schema_queries = [
                # Students table
                """
                CREATE TABLE IF NOT EXISTS Students (
                    StudentID INT PRIMARY KEY AUTO_INCREMENT,
                    FirstName VARCHAR(100) NOT NULL,
                    LastName VARCHAR(100) NOT NULL,
                    Email VARCHAR(255) NOT NULL UNIQUE,
                    DateOfBirth DATE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Teachers table
                """
                CREATE TABLE IF NOT EXISTS Teachers (
                    TeacherID INT PRIMARY KEY AUTO_INCREMENT,
                    FirstName VARCHAR(100) NOT NULL,
                    LastName VARCHAR(100) NOT NULL,
                    Email VARCHAR(255) NOT NULL UNIQUE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Courses table
                """
                CREATE TABLE IF NOT EXISTS Courses (
                    CourseID INT PRIMARY KEY AUTO_INCREMENT,
                    CourseName VARCHAR(255) NOT NULL,
                    CourseCode VARCHAR(50) NOT NULL UNIQUE,
                    TeacherID INT NOT NULL,
                    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
                        ON DELETE RESTRICT ON UPDATE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # EvaluationComponents table
                """
                CREATE TABLE IF NOT EXISTS EvaluationComponents (
                    ComponentID INT PRIMARY KEY AUTO_INCREMENT,
                    CourseID INT NOT NULL,
                    ParentComponentID INT,
                    ComponentLevel VARCHAR(50) NOT NULL,
                    ComponentName VARCHAR(255) NOT NULL,
                    ComponentCode VARCHAR(50),
                    Description TEXT,
                    IsLeaf BOOLEAN DEFAULT FALSE,
                    OrderIndex INT DEFAULT 0,
                    ComponentPath VARCHAR(500),
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (ParentComponentID) REFERENCES EvaluationComponents(ComponentID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    INDEX idx_parent (ParentComponentID),
                    INDEX idx_course (CourseID)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Evaluations table
                """
                CREATE TABLE IF NOT EXISTS Evaluations (
                    EvaluationID INT PRIMARY KEY AUTO_INCREMENT,
                    CourseID INT NOT NULL,
                    StudentID INT NOT NULL,
                    EvaluationComponentID INT NOT NULL,
                    Score DECIMAL(5,2),
                    MaxScore DECIMAL(5,2) DEFAULT 100,
                    Weight DECIMAL(5,2) DEFAULT 1.0,
                    DateAssigned DATE NOT NULL,
                    DateCompleted DATE,
                    Notes TEXT,
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (EvaluationComponentID) REFERENCES EvaluationComponents(ComponentID)
                        ON DELETE RESTRICT ON UPDATE CASCADE,
                    INDEX idx_student (StudentID),
                    INDEX idx_course (CourseID)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Grades table
                """
                CREATE TABLE IF NOT EXISTS Grades (
                    GradeID INT PRIMARY KEY AUTO_INCREMENT,
                    StudentID INT NOT NULL,
                    CourseID INT NOT NULL,
                    FinalGrade DECIMAL(5,2) NOT NULL,
                    DateAssigned DATE NOT NULL,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    UNIQUE KEY unique_student_course (StudentID, CourseID),
                    INDEX idx_student (StudentID),
                    INDEX idx_course (CourseID)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Tutorials table
                """
                CREATE TABLE IF NOT EXISTS Tutorials (
                    TutorialID INT PRIMARY KEY AUTO_INCREMENT,
                    StudentID INT NOT NULL,
                    Date DATE NOT NULL,
                    Topic VARCHAR(255) NOT NULL,
                    Notes TEXT,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    INDEX idx_student (StudentID),
                    INDEX idx_date (Date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """,

                # Bans table
                """
                CREATE TABLE IF NOT EXISTS Bans (
                    BanID INT PRIMARY KEY AUTO_INCREMENT,
                    StudentID INT NOT NULL,
                    BanType VARCHAR(100) NOT NULL,
                    StartDate DATE NOT NULL,
                    EndDate DATE,
                    Reason TEXT NOT NULL,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    INDEX idx_student (StudentID),
                    INDEX idx_dates (StartDate, EndDate)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            ]

            # Execute each query
            for i, query in enumerate(schema_queries, 1):
                try:
                    cursor.execute(query)
                    table_name = query.split('EXISTS')[1].split('(')[0].strip()
                    print(f"   ✅ Created table: {table_name}")
                except Exception as e:
                    print(f"   ❌ Error creating table: {e}")
                    logger.error(f"Error creating table: {e}")

            cursor.close()

            if MYSQL_AVAILABLE:
                self.connection.commit()

            print("\n✅ Schema creation completed")
            return True

        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            logger.error(f"Schema creation failed: {e}")
            return False

    def insert_sample_data(self) -> bool:
        """Insert sample data into MySQL database."""
        print("\n📊 Inserting Sample Data...")
        print("=" * 50)

        try:
            if not self.connection:
                if not self.test_connection():
                    return False

            if MYSQL_AVAILABLE:
                cursor = self.connection.cursor()
            elif PYMYSQL_AVAILABLE:
                cursor = self.connection.cursor()
            else:
                return False

            # Sample data
            sample_queries = [
                # Students
                """
                INSERT INTO Students (FirstName, LastName, Email, DateOfBirth) VALUES
                ('John', 'Doe', 'john.doe@email.com', '2000-05-15'),
                ('Jane', 'Smith', 'jane.smith@email.com', '2001-03-22'),
                ('Bob', 'Johnson', 'bob.johnson@email.com', '2000-11-08')
                """,

                # Teachers
                """
                INSERT INTO Teachers (FirstName, LastName, Email) VALUES
                ('Dr. Sarah', 'Williams', 'sarah.williams@school.edu'),
                ('Prof. Michael', 'Brown', 'michael.brown@school.edu')
                """,

                # Courses
                """
                INSERT INTO Courses (CourseName, CourseCode, TeacherID) VALUES
                ('Introduction to Programming', 'CS101', 1),
                ('Database Systems', 'CS201', 2),
                ('Web Development', 'CS301', 1)
                """
            ]

            for query in sample_queries:
                try:
                    cursor.execute(query)
                    print(f"   ✅ Data inserted successfully")
                except Exception as e:
                    if "Duplicate entry" in str(e):
                        print(f"   ⚠️  Data already exists")
                    else:
                        print(f"   ❌ Error: {e}")

            cursor.close()

            if MYSQL_AVAILABLE:
                self.connection.commit()

            print("\n✅ Sample data insertion completed")
            return True

        except Exception as e:
            print(f"❌ Sample data insertion failed: {e}")
            logger.error(f"Sample data insertion failed: {e}")
            return False

    def display_summary(self) -> None:
        """Display database summary."""
        print("\n" + "=" * 70)
        print("MYSQL DATABASE SUMMARY")
        print("=" * 70)

        # Configuration
        if self.config:
            print("\n📋 Configuration:")
            print(f"   Type: MySQL")
            print(f"   Host: {self.config.get('host')}")
            print(f"   Port: {self.config.get('port')}")
            print(f"   Database: {self.config.get('database')}")
            print(f"   User: {self.config.get('username')}")

        # Tables
        print("\n📊 Database Tables:")
        tables = self.list_tables()

        if tables:
            total_records = 0
            for table in sorted(tables, key=lambda x: x['name']):
                print(f"   {table['name']:30} {table['records']:6} records, {table['columns']:3} columns")
                total_records += table['records']

            print(f"   {'─' * 50}")
            print(f"   {'Total':30} {total_records:6} records")
        else:
            print("   No tables found or connection failed")

        # Schema check
        print("\n✅ Student Schema Status:")
        schema_status = self.check_student_schema()
        all_present = True

        for table, exists in sorted(schema_status.items()):
            status = "✓" if exists else "✗"
            print(f"   {status} {table}")
            if not exists:
                all_present = False

        if not all_present:
            print("\n⚠️  Some tables are missing")
            print("   Run with --init to create missing tables")

        print("\n" + "=" * 70)

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            if MYSQL_AVAILABLE and hasattr(self.connection, 'close'):
                self.connection.close()
            elif PYMYSQL_AVAILABLE:
                self.connection.close()
            print("🔌 Connection closed")


def update_credentials_for_mysql():
    """Update credentials.json for MySQL."""
    print("\n📝 Updating credentials.json for MySQL...")

    credentials_file = 'credentials.json'

    if Path(credentials_file).exists():
        with open(credentials_file, 'r') as f:
            credentials = json.load(f)

        # Fix the type
        if 'database' in credentials:
            credentials['database']['type'] = 'mysql'

            # Remove SQLite-specific fields
            if 'db_path' in credentials['database']:
                del credentials['database']['db_path']

        # Save updated credentials
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)

        print("✅ Updated credentials.json to use MySQL")
        return True

    return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='MySQL Student Database Management')
    parser.add_argument('--init', action='store_true', help='Initialize database schema')
    parser.add_argument('--sample-data', action='store_true', help='Insert sample data')
    parser.add_argument('--fix-config', action='store_true', help='Fix credentials.json for MySQL')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("MYSQL STUDENT DATABASE MANAGEMENT SYSTEM")
    print("=" * 70)

    # Fix configuration if requested
    if args.fix_config:
        update_credentials_for_mysql()

    # Check for MySQL drivers
    if not MYSQL_AVAILABLE and not PYMYSQL_AVAILABLE:
        print("\n❌ No MySQL driver installed!")
        print("\nInstall one of these:")
        print("   pip install mysql-connector-python")
        print("   pip install pymysql")
        print("\nThen run this script again.")
        sys.exit(1)

    # Create manager
    manager = MySQLDatabaseManager()

    try:
        # Load credentials
        manager.load_credentials()

        # Test connection
        if not manager.test_connection():
            print("\n❌ Could not connect to MySQL database")
            print("\nCheck your credentials.json file:")
            print("1. Ensure 'type' is set to 'mysql'")
            print("2. Verify host, port, database, username, and password")
            sys.exit(1)

        # Initialize schema if requested
        if args.init:
            manager.create_student_schema()

            if args.sample_data:
                manager.insert_sample_data()

        # Display summary
        manager.display_summary()

        # Close connection
        manager.close()

        # Next steps
        if not args.init:
            print("\n💡 Next Steps:")
            print("   python main_mysql.py --init              # Create schema")
            print("   python main_mysql.py --init --sample-data # With sample data")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()