"""
Main entry point for MySQL Student Database Management System.

This module orchestrates the configuration, database operations, and services
to provide a complete database management solution with comprehensive
error handling and logging.
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import time

# Import configuration and utilities
from config.config import load_config, setup_logging, DatabaseConfig
from utils.credentials import create_sample_credentials_file, CredentialsManager
from services.table_drop_service import TableDropManager

# Import services
from services.db_connection import (
    create_database_service, DatabaseService,
    DatabaseConnectionError, check_driver_availability
)
from services.table_operations import TableOperationsService

# Import CSV operations
from services.csv_loader import CSVLoader
from services.csv_operations import CSVOperationsManager

# Import entity operations
from entity.creation_queries import (
    get_creation_queries_by_order, get_drop_queries_by_order,
    CREATE_VIEWS, CREATE_PROCEDURES
)
from entity.insert_queries import get_insert_query, get_insert_order
from entity.update_queries import get_update_query, get_maintenance_queries

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Main database manager that orchestrates all database operations.
    """

    def __init__(self, config: DatabaseConfig, credentials_file: str = 'credentials.json'):
        """
        Initialize database manager.

        Args:
            config: Database configuration
            credentials_file: Path to credentials file
        """
        self.config = config
        self.credentials_file = credentials_file
        self.db_service: Optional[DatabaseService] = None
        self.table_service: Optional[TableOperationsService] = None
        self.csv_operations: Optional[CSVOperationsManager] = None
        self._operation_stats = {
            'tables_created': 0,
            'tables_dropped': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'csv_files_loaded': 0,
            'errors': 0
        }

    def initialize(self) -> bool:
        """
        Initialize database services and connections.

        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing database manager...")

            # Check driver availability
            drivers = check_driver_availability()
            if not drivers['any_available']:
                logger.error("No MySQL drivers available. Please install mysql-connector-python or PyMySQL")
                return False

            logger.info(f"Available drivers: {[k for k, v in drivers.items() if v and k != 'any_available']}")

            # Create database service
            self.db_service = create_database_service(self.credentials_file, self.config)

            # Create table operations service
            self.table_service = TableOperationsService(self.db_service)

            # Create CSV operations manager
            self.csv_operations = CSVOperationsManager(self.db_service, self.table_service)

            logger.info("Database manager initialized successfully")
            return True

        except DatabaseConnectionError as e:
            logger.error(f"Database connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    def load_csv_file(self, table_name: str, csv_file: Optional[str] = None,
                      batch_size: int = 100, skip_duplicates: bool = True,
                      dry_run: bool = False) -> bool:
        """
        Load data from CSV file into specified table.

        Args:
            table_name: Target table name
            csv_file: Path to CSV file (optional, will use default path if not provided)
            batch_size: Number of records to process in each batch
            skip_duplicates: Whether to skip duplicate records
            dry_run: If True, validate data but don't insert

        Returns:
            True if CSV loading successful
        """
        try:
            logger.info(f"Loading CSV data into table: {table_name}")

            # Determine CSV file path
            if csv_file is None:
                csv_file = self.config.get_csv_file_path(table_name)
                if csv_file is None:
                    logger.error(f"No CSV file configured for table: {table_name}")
                    return False

            # Validate CSV file exists
            csv_path = Path(csv_file)
            if not csv_path.exists():
                logger.error(f"CSV file not found: {csv_file}")
                return False

            # Check if target table exists
            if not self.table_service.check_table_exists(table_name):
                logger.error(f"Target table '{table_name}' does not exist")
                return False

            # Get initial record count
            initial_count = self._get_table_row_count(table_name)
            logger.info(f"Table {table_name} currently has {initial_count} records")

            # Perform CSV import
            results = self.csv_operations.import_csv_file(
                csv_file=str(csv_file),
                table_name=table_name,
                batch_size=batch_size,
                skip_duplicates=skip_duplicates,
                dry_run=dry_run
            )

            # Update operation statistics
            if results['success']:
                self._operation_stats['csv_files_loaded'] += 1
                if not dry_run:
                    records_added = results.get('records_added', 0)
                    self._operation_stats['records_inserted'] += records_added
                    logger.info(f"Successfully loaded {records_added} records from CSV into {table_name}")
                else:
                    logger.info(f"CSV validation completed for {table_name}")
            else:
                self._operation_stats['errors'] += 1
                logger.error(f"CSV loading failed for {table_name}: {results.get('error', 'Unknown error')}")

            # Display detailed results
            self._display_csv_results(results, table_name, dry_run)

            return results['success']

        except Exception as e:
            logger.error(f"CSV loading failed for table {table_name}: {e}")
            self._operation_stats['errors'] += 1
            return False

    def bulk_load_csv_files(self, table_names: Optional[List[str]] = None,
                           batch_size: int = 100, skip_duplicates: bool = True,
                           dry_run: bool = False) -> bool:
        """
        Load multiple CSV files in bulk.

        Args:
            table_names: List of table names to load (optional, loads all configured if None)
            batch_size: Number of records to process in each batch
            skip_duplicates: Whether to skip duplicate records
            dry_run: If True, validate data but don't insert

        Returns:
            True if all CSV files loaded successfully
        """
        try:
            logger.info("Starting bulk CSV loading operation")

            # Get tables to load
            if table_names is None:
                table_names = self.config.get_available_csv_tables()

            if not table_names:
                logger.warning("No CSV files configured for loading")
                return True

            # Prepare bulk import configuration
            import_config = {
                'batch_size': batch_size,
                'skip_duplicates': skip_duplicates,
                'dry_run': dry_run,
                'files': []
            }

            # Add file configurations
            for table_name in table_names:
                csv_file = self.config.get_csv_file_path(table_name)
                if csv_file and Path(csv_file).exists():
                    import_config['files'].append({
                        'csv_file': csv_file,
                        'table_name': table_name
                    })
                else:
                    logger.warning(f"CSV file not found for table {table_name}: {csv_file}")

            if not import_config['files']:
                logger.error("No valid CSV files found for bulk import")
                return False

            # Perform bulk import
            results = self.csv_operations.bulk_import_csv_files(import_config)

            # Update statistics
            self._operation_stats['csv_files_loaded'] += results.get('successful_imports', 0)
            self._operation_stats['errors'] += results.get('failed_imports', 0)

            # Display results
            logger.info(f"Bulk CSV import completed: {results.get('summary', 'No summary available')}")

            return results['success']

        except Exception as e:
            logger.error(f"Bulk CSV loading failed: {e}")
            return False

    def validate_csv_files(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate CSV files without importing data.

        Args:
            table_names: List of table names to validate (optional, validates all if None)

        Returns:
            Dictionary with validation results
        """
        try:
            logger.info("Validating CSV files...")

            if table_names is None:
                table_names = self.config.get_available_csv_tables()

            validation_results = {
                'total_files': 0,
                'valid_files': 0,
                'invalid_files': 0,
                'file_results': {}
            }

            for table_name in table_names:
                csv_file = self.config.get_csv_file_path(table_name)
                if csv_file and Path(csv_file).exists():
                    validation_results['total_files'] += 1

                    result = self.csv_operations.validate_csv_file(csv_file, table_name)
                    validation_results['file_results'][table_name] = result

                    if result['success']:
                        validation_results['valid_files'] += 1
                    else:
                        validation_results['invalid_files'] += 1

            logger.info(f"CSV validation completed: {validation_results['valid_files']}/{validation_results['total_files']} files valid")
            return validation_results

        except Exception as e:
            logger.error(f"CSV validation failed: {e}")
            return {'error': str(e)}

    def _display_csv_results(self, results: Dict[str, Any], table_name: str, dry_run: bool) -> None:
        """Display CSV operation results."""
        print(f"\n{'='*60}")
        print(f"CSV {'Validation' if dry_run else 'Import'} Results - {table_name}")
        print(f"{'='*60}")

        if results['success']:
            print(f"Status: SUCCESS")
            if 'import_statistics' in results:
                stats = results['import_statistics']
                print(f"Total rows processed: {stats.get('total_rows', 0)}")
                print(f"Valid rows: {stats.get('valid_rows', 0)}")
                print(f"Invalid rows: {stats.get('invalid_rows', 0)}")
                if not dry_run:
                    print(f"Records inserted: {stats.get('inserted_rows', 0)}")
                    print(f"Records failed: {stats.get('failed_rows', 0)}")
        else:
            print(f"Status: FAILED")
            print(f"Error: {results.get('error', 'Unknown error')}")

        if results.get('errors'):
            print(f"\nErrors ({len(results['errors'])}):")
            for i, error in enumerate(results['errors'][:5], 1):  # Show first 5 errors
                print(f"  {i}. {error}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors']) - 5} more errors")

        print(f"{'='*60}")

    def create_schema(self, selected_tables: Optional[List[str]] = None) -> bool:
        """
        Create database schema with specified tables.

        Args:
            selected_tables: Optional list of specific tables to create

        Returns:
            True if schema creation successful
        """
        try:
            logger.info("Creating database schema...")

            # Get tables to create
            if selected_tables:
                tables_to_create = selected_tables
            else:
                tables_to_create = self.config.get_table_list()

            # Drop existing tables if configured
            if self.config.drop_existing:
                logger.info("Dropping existing tables...")
                self._drop_tables(tables_to_create)

            # Get creation queries in dependency order
            creation_queries = get_creation_queries_by_order(tables_to_create)

            logger.info(f"Creating {len(creation_queries)} tables...")

            for table_name, query in creation_queries:
                try:
                    logger.debug(f"Creating table: {table_name}")
                    self.db_service.execute_query(query, fetch=False)
                    self._operation_stats['tables_created'] += 1
                    logger.info(f"Created table: {table_name}")

                except Exception as e:
                    logger.error(f"Failed to create table {table_name}: {e}")
                    self._operation_stats['errors'] += 1

                    if not self.config.update_existing:
                        raise

            # Create views if configured
            if hasattr(self.config, 'create_views') and self.config.create_views:
                self._create_views()

            # Create stored procedures if configured
            if hasattr(self.config, 'create_procedures') and self.config.create_procedures:
                self._create_procedures()

            logger.info(f"Schema creation completed. Created {self._operation_stats['tables_created']} tables")
            return True

        except Exception as e:
            logger.error(f"Schema creation failed: {e}")
            return False

    def _drop_tables(self, table_names: List[str]) -> None:
        """Drop specified tables in reverse dependency order."""
        drop_queries = get_drop_queries_by_order(table_names)

        for table_name, query in drop_queries:
            try:
                if self.table_service.check_table_exists(table_name):
                    logger.debug(f"Dropping table: {table_name}")
                    self.db_service.execute_query(query, fetch=False)
                    self._operation_stats['tables_dropped'] += 1
                    logger.info(f"Dropped table: {table_name}")
            except Exception as e:
                logger.warning(f"Failed to drop table {table_name}: {e}")

    def drop_all_tables_enhanced(self, confirm: bool = False,
                                 force: bool = False, create_backup: bool = True) -> bool:
        """Enhanced method to drop all tables with safety features."""
        try:
            drop_manager = TableDropManager(self.db_service, self.table_service)

            # Create backup if requested
            backup_path = None
            if create_backup:
                print("Creating backup before dropping tables...")
                backup_path = drop_manager.create_backup_before_drop()
                if backup_path:
                    print(f"Backup created: {backup_path}")

            # Perform drop operation
            results = drop_manager.drop_all_tables(confirm=confirm, force=force)

            # Display results and update stats
            # ... (rest of the implementation from the artifact)

            return results['success']

        except Exception as e:
            logger.error(f"Enhanced drop operation failed: {e}")
            return False

    def _create_views(self) -> None:
        """Create database views."""
        logger.info("Creating database views...")

        for view_name, query in CREATE_VIEWS.items():
            try:
                self.db_service.execute_query(query, fetch=False)
                logger.info(f"Created view: {view_name}")
            except Exception as e:
                logger.error(f"Failed to create view {view_name}: {e}")

    def _create_procedures(self) -> None:
        """Create stored procedures."""
        logger.info("Creating stored procedures...")

        for proc_name, query in CREATE_PROCEDURES.items():
            try:
                # First, drop the procedure if it exists
                drop_query = f"DROP PROCEDURE IF EXISTS {proc_name}"
                self.db_service.execute_query(drop_query, fetch=False)

                # Then create the procedure (remove any DROP statements from the query)
                create_query = query
                if "DROP PROCEDURE" in create_query:
                    # Split and take only the CREATE part
                    parts = create_query.split("CREATE PROCEDURE")
                    if len(parts) > 1:
                        create_query = "CREATE PROCEDURE" + parts[1]

                self.db_service.execute_query(create_query, fetch=False)
                logger.info(f"Created procedure: {proc_name}")

            except Exception as e:
                logger.error(f"Failed to create procedure {proc_name}: {e}")

    def insert_sample_data(self) -> bool:
        """
        Insert sample data into database tables.

        Returns:
            True if data insertion successful
        """
        try:
            logger.info("Inserting sample data...")

            # Get insertion order
            insert_order = get_insert_order()

            # Filter based on existing tables and configuration
            tables_to_populate = []
            for table in insert_order:
                if self.table_service.check_table_exists(table):
                    if not self.config.selected_tables or table in self.config.selected_tables:
                        tables_to_populate.append(table)

            logger.info(f"Inserting data into {len(tables_to_populate)} tables...")

            for table_name in tables_to_populate:
                try:
                    # Check if table already has data
                    existing_count = self._get_table_row_count(table_name)

                    if existing_count > 0 and not self.config.update_existing:
                        logger.info(f"Table {table_name} already has {existing_count} records, skipping")
                        continue

                    # Get and execute insert query
                    insert_query = get_insert_query(table_name)

                    logger.debug(f"Inserting data into: {table_name}")
                    self.db_service.execute_query(insert_query, fetch=False)

                    # Get new count
                    new_count = self._get_table_row_count(table_name)
                    records_added = new_count - existing_count

                    self._operation_stats['records_inserted'] += records_added
                    logger.info(f"Inserted {records_added} records into {table_name}")

                except Exception as e:
                    logger.error(f"Failed to insert data into {table_name}: {e}")
                    self._operation_stats['errors'] += 1

                    if not self.config.update_existing:
                        raise

            logger.info(f"Sample data insertion completed. Inserted {self._operation_stats['records_inserted']} records")
            return True

        except Exception as e:
            logger.error(f"Sample data insertion failed: {e}")
            return False

    def _get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            result = self.db_service.execute_query(f"SELECT COUNT(*) FROM `{table_name}`")
            return result[0][0] if result else 0
        except Exception:
            return 0

    def run_maintenance_operations(self) -> bool:
        """
        Run database maintenance operations.

        Returns:
            True if maintenance operations successful
        """
        try:
            logger.info("Running database maintenance operations...")

            maintenance_queries = get_maintenance_queries()

            for operation_name, query in maintenance_queries.items():
                try:
                    logger.debug(f"Running maintenance operation: {operation_name}")
                    self.db_service.execute_query(query, fetch=False)
                    logger.info(f"Completed maintenance: {operation_name}")

                except Exception as e:
                    logger.error(f"Maintenance operation failed {operation_name}: {e}")
                    self._operation_stats['errors'] += 1

            logger.info("Database maintenance completed")
            return True

        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive database report.

        Returns:
            Dictionary with database report information
        """
        try:
            logger.info("Generating database report...")

            # Get database summary
            summary = self.table_service.get_database_summary()

            # Get schema integrity analysis
            integrity = self.table_service.analyze_schema_integrity()

            # Combine with operation stats
            report = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'database_summary': summary,
                'schema_integrity': integrity,
                'operation_statistics': self._operation_stats.copy(),
                'configuration': {
                    'create_schema': self.config.create_schema,
                    'insert_sample_data': self.config.insert_sample_data,
                    'update_existing': self.config.update_existing,
                    'selected_tables': self.config.selected_tables
                }
            }

            logger.info("Database report generated successfully")
            return report

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return {'error': str(e)}

    def display_status(self) -> None:
        """Display current database status."""
        try:
            print("\n" + "=" * 80)
            print("MYSQL STUDENT DATABASE MANAGEMENT SYSTEM")
            print("=" * 80)

            # Connection info
            if self.db_service:
                conn_info = self.db_service.get_connection_info()
                print(f"\nDatabase Connection:")
                print(f"   Driver: {conn_info.get('driver', 'Unknown')}")
                print(f"   Host: {conn_info.get('host', 'Unknown')}")
                print(f"   Database: {conn_info.get('database', 'Unknown')}")
                print(f"   Server Version: {conn_info.get('server_version', 'Unknown')}")

            # Table summary
            if self.table_service:
                summary = self.table_service.get_database_summary()
                print(f"\nDatabase Summary:")
                print(f"   Tables: {summary.get('table_count', 0)}")
                print(f"   Total Records: {summary.get('total_rows', 0):,}")
                print(f"   Total Size: {summary.get('total_size_mb', 0):.2f} MB")
                print(f"   Foreign Keys: {summary.get('foreign_key_count', 0)}")

                # Table details
                if summary.get('tables'):
                    print(f"\nTable Details:")
                    print(f"   {'Table':<25} {'Records':<10} {'Size (MB)':<10} {'Engine':<8}")
                    print(f"   {'-' * 60}")

                    for table in summary['tables']:
                        print(f"   {table['name']:<25} {table['rows']:<10,} "
                              f"{table['size_mb']:<10.2f} {table['engine']:<8}")

            # Operation statistics
            print(f"\nOperation Statistics:")
            print(f"   Tables Created: {self._operation_stats['tables_created']}")
            print(f"   Tables Dropped: {self._operation_stats['tables_dropped']}")
            print(f"   Records Inserted: {self._operation_stats['records_inserted']:,}")
            print(f"   Records Updated: {self._operation_stats['records_updated']:,}")
            print(f"   CSV Files Loaded: {self._operation_stats['csv_files_loaded']}")
            print(f"   Errors: {self._operation_stats['errors']}")

            # CSV file status
            csv_tables = self.config.get_available_csv_tables()
            if csv_tables:
                print(f"\nConfigured CSV Files:")
                for table_name in csv_tables:
                    csv_file = self.config.get_csv_file_path(table_name)
                    exists = Path(csv_file).exists() if csv_file else False
                    status = "EXISTS" if exists else "MISSING"
                    print(f"   {table_name:<20} -> {csv_file} [{status}]")

            print("\n" + "=" * 80)

        except Exception as e:
            logger.error(f"Error displaying status: {e}")
            print(f"Error displaying status: {e}")

    def close(self) -> None:
        """Close all database connections and cleanup."""
        if self.db_service:
            self.db_service.close()
        logger.info("Database manager closed")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description='MySQL Student Database Management System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --init                           # Create schema only
  %(prog)s --init --sample-data            # Create schema and insert sample data
  %(prog)s --tables Students Teachers      # Create only specific tables
  %(prog)s --drop --init                   # Drop existing and recreate
  %(prog)s --load-csv --table-name Students # Load CSV data into Students table
  %(prog)s --load-csv --table-name Students --csv-file /path/to/custom.csv
  %(prog)s --bulk-load-csv                 # Load all configured CSV files
  %(prog)s --validate-csv                  # Validate all CSV files
  %(prog)s --maintenance                   # Run maintenance operations
  %(prog)s --report                        # Generate database report
  %(prog)s --create-credentials            # Create sample credentials file
        """
    )

    # Operation flags
    parser.add_argument('--init', action='store_true',
                       help='Initialize database schema')
    parser.add_argument('--sample-data', action='store_true',
                       help='Insert sample data into tables')
    parser.add_argument('--drop', action='store_true',
                       help='Drop existing tables before creation')
    parser.add_argument('--maintenance', action='store_true',
                       help='Run database maintenance operations')
    parser.add_argument('--report', action='store_true',
                       help='Generate comprehensive database report')
    parser.add_argument('--status', action='store_true',
                       help='Display current database status')

    # CSV operations
    parser.add_argument('--load-csv', action='store_true',
                       help='Load data from CSV file into database table')
    parser.add_argument('--table-name', type=str, metavar='TABLE',
                       help='Target table name for CSV operations')
    parser.add_argument('--csv-file', type=str, metavar='FILE',
                       help='Path to CSV file (optional, uses configured path if not provided)')
    parser.add_argument('--bulk-load-csv', action='store_true',
                       help='Load all configured CSV files in bulk')
    parser.add_argument('--validate-csv', action='store_true',
                       help='Validate CSV files without importing data')
    parser.add_argument('--batch-size', type=int, default=100, metavar='N',
                       help='Number of records to process in each batch (default: 100)')
    parser.add_argument('--allow-duplicates', action='store_true',
                       help='Allow duplicate records during CSV import')
    parser.add_argument('--dry-run', action='store_true',
                       help='Validate CSV data but do not insert into database')

    # Configuration options
    parser.add_argument('--config', type=str, metavar='FILE',
                       help='Path to configuration file')
    parser.add_argument('--credentials', type=str, default='credentials.json',
                       metavar='FILE', help='Path to credentials file')
    parser.add_argument('--tables', nargs='+', metavar='TABLE',
                       help='Specific tables to operate on')
    parser.add_argument('--exclude', nargs='+', metavar='TABLE',
                       help='Tables to exclude from operations')

    # Utility options
    parser.add_argument('--create-credentials', action='store_true',
                       help='Create sample credentials file')
    parser.add_argument('--check-drivers', action='store_true',
                       help='Check MySQL driver availability')
    parser.add_argument('--test-connection', action='store_true',
                       help='Test database connection only')

    # Logging options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level')
    parser.add_argument('--log-file', type=str, metavar='FILE',
                       help='Log file path')

    # Output options
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress console output')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    # Enhanced drop operations
    parser.add_argument('--drop-all', action='store_true',
                        help='Drop all tables with safety checks')
    parser.add_argument('--force-drop', action='store_true',
                        help='Force drop (disables foreign key checks)')
    parser.add_argument('--no-backup', action='store_true',
                        help='Skip backup creation before dropping')

    return parser


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        from entity.creation_queries import get_schema_info
        info = get_schema_info()
        print(f"Total tables: {info['total_tables']}")
        print(f"MySQL 5.7 compatible: {info['mysql57_compatibility']}")
    except ImportError:
        logger.warning("Could not import schema info")

    try:

        # Handle utility operations first
        if args.create_credentials:
            create_sample_credentials_file(args.credentials)
            return 0

        if args.check_drivers:
            drivers = check_driver_availability()
            print("\nMySQL Driver Availability:")
            print(f"   mysql-connector-python: {'Available' if drivers['mysql-connector-python'] else 'Not available'}")
            print(f"   PyMySQL: {'Available' if drivers['pymysql'] else 'Not available'}")

            if not drivers['any_available']:
                print("\nNo MySQL drivers installed!")
                print("   Install one of the following:")
                print("   pip install mysql-connector-python")
                print("   pip install pymysql")
                return 1

            return 0

        # Validate CSV-specific arguments
        if args.load_csv and not args.table_name:
            print("Error: --table-name is required when using --load-csv")
            return 1

        # Load configuration
        config = load_config(args.config)

        # Override config with command line arguments
        if args.tables:
            config._config_data.setdefault('tables', {})['selected_tables'] = args.tables
            config._config_data['tables']['create_all'] = False

        if args.exclude:
            config._config_data.setdefault('tables', {})['exclude_tables'] = args.exclude

        if args.drop:
            config._config_data.setdefault('operations', {})['drop_existing'] = True

        if args.log_level:
            config._config_data.setdefault('logging', {})['level'] = args.log_level

        if args.log_file:
            config._config_data.setdefault('logging', {})['file'] = args.log_file

        # Setup logging with updated config
        setup_logging()

        # Check if credentials file exists
        if not Path(args.credentials).exists() and not args.test_connection:
            logger.error(f"Credentials file not found: {args.credentials}")
            print(f"Credentials file not found: {args.credentials}")
            print(f"Run with --create-credentials to create a sample file")
            return 1

        # Initialize database manager
        manager = DatabaseManager(config, args.credentials)

        if not manager.initialize():
            logger.error("Failed to initialize database manager")
            print("Failed to initialize database manager")
            return 1

        # Handle test connection
        if args.test_connection:
            print("Testing database connection...")
            if manager.db_service.test_connection():
                print("Database connection successful")
                conn_info = manager.db_service.get_connection_info()
                print(f"   Host: {conn_info.get('host')}")
                print(f"   Database: {conn_info.get('database')}")
                print(f"   Driver: {conn_info.get('driver')}")
                return 0
            else:
                print("Database connection failed")
                return 1

        # Execute operations based on arguments
        success = True

        # Drop all tables
        if args.drop_all:
            success = manager.drop_all_tables_enhanced(
                confirm=not args.quiet,
                force=args.force_drop,
                create_backup=not args.no_backup
            )

        # CSV operations
        if args.load_csv:
            print(f"Loading CSV data into table: {args.table_name}")
            success = manager.load_csv_file(
                table_name=args.table_name,
                csv_file=args.csv_file,
                batch_size=args.batch_size,
                skip_duplicates=not args.allow_duplicates,
                dry_run=args.dry_run
            )

        elif args.bulk_load_csv:
            print("Loading all configured CSV files...")
            success = manager.bulk_load_csv_files(
                table_names=args.tables,
                batch_size=args.batch_size,
                skip_duplicates=not args.allow_duplicates,
                dry_run=args.dry_run
            )

        elif args.validate_csv:
            print("Validating CSV files...")
            validation_results = manager.validate_csv_files(args.tables)
            if 'error' in validation_results:
                print(f"CSV validation failed: {validation_results['error']}")
                success = False
            else:
                print(f"Validation completed: {validation_results['valid_files']}/{validation_results['total_files']} files valid")
                for table_name, result in validation_results['file_results'].items():
                    status = "VALID" if result['success'] else "INVALID"
                    print(f"  {table_name}: {status}")
                    if not result['success'] and result.get('errors'):
                        for error in result['errors'][:3]:  # Show first 3 errors
                            print(f"    - {error}")

        # Schema creation
        elif args.init:
            if not manager.create_schema(args.tables):
                success = False

        # Sample data insertion
        if args.sample_data and success:
            if not manager.insert_sample_data():
                success = False

        # Maintenance operations
        if args.maintenance and success:
            if not manager.run_maintenance_operations():
                success = False

        # Generate report
        if args.report:
            report = manager.generate_report()
            if 'error' in report:
                print(f"Report generation failed: {report['error']}")
                success = False
            else:
                # Save report to file
                import json
                report_file = f"database_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                print(f"Database report saved to: {report_file}")

        # Display status (default if no other operations)
        if args.status or not any([args.init, args.sample_data, args.maintenance, args.report,
                                   args.load_csv, args.bulk_load_csv, args.validate_csv]):
            manager.display_status()

        # Show next steps if appropriate
        if not any([args.init, args.sample_data, args.maintenance, args.report, args.status,
                    args.load_csv, args.bulk_load_csv, args.validate_csv]):
            print("\nNext Steps:")
            if not args.init:
                print("   python main.py --init              # Create database schema")
                print("   python main.py --init --sample-data # Create schema with sample data")

            # Show CSV operations
            csv_tables = manager.config.get_available_csv_tables()
            if csv_tables:
                print("\nCSV Operations:")
                print("   python main.py --load-csv --table-name Students")
                print("   python main.py --bulk-load-csv")
                print("   python main.py --validate-csv")

            print("\nOther Operations:")
            print("   python main.py --status            # Show database status")
            print("   python main.py --report            # Generate comprehensive report")
            print("   python main.py --maintenance       # Run maintenance operations")

        # Cleanup
        manager.close()

        if success:
            logger.info("All operations completed successfully")
            return 0
        else:
            logger.error("Some operations failed")
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        logger.info("Operation cancelled by user")
        return 1

    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"Unexpected error: {e}")
        return 1


def run_interactive_mode() -> int:
    """
    Run interactive mode for guided database operations.

    Returns:
        Exit code
    """
    try:
        print("\n" + "=" * 60)
        print("MySQL Student Database - Interactive Mode")
        print("=" * 60)

        # Check drivers first
        drivers = check_driver_availability()
        if not drivers['any_available']:
            print("No MySQL drivers installed!")
            print("Install one with: pip install mysql-connector-python")
            return 1

        # Check for credentials
        credentials_file = 'credentials.json'
        if not Path(credentials_file).exists():
            print(f"\nCredentials file not found: {credentials_file}")
            create_new = input("Create sample credentials file? (y/n): ").lower().strip()

            if create_new == 'y':
                create_sample_credentials_file(credentials_file)
                print(f"Sample credentials created: {credentials_file}")
                print("Please update with your actual database credentials and run again.")
                return 0
            else:
                return 1

        # Load configuration
        config = load_config()
        setup_logging()

        # Initialize manager
        manager = DatabaseManager(config, credentials_file)

        print("\nConnecting to database...")
        if not manager.initialize():
            print("Failed to connect to database")
            return 1

        print("Connected successfully!")

        # Interactive menu
        while True:
            print("\n" + "-" * 50)
            print("Available Operations:")
            print("1. Create/Update Schema")
            print("2. Insert Sample Data")
            print("3. Load CSV File")
            print("4. Bulk Load All CSV Files")
            print("5. Validate CSV Files")
            print("6. Run Maintenance")
            print("7. Generate Report")
            print("8. Show Status")
            print("9. Test Connection")
            print("0. Exit")
            print("-" * 50)

            choice = input("Select operation (0-9): ").strip()

            if choice == '0':
                break
            elif choice == '1':
                print("\nCreating/Updating Schema...")
                if manager.create_schema():
                    print("Schema operations completed")
                else:
                    print("Schema operations failed")
            elif choice == '2':
                print("\nInserting Sample Data...")
                if manager.insert_sample_data():
                    print("Sample data insertion completed")
                else:
                    print("Sample data insertion failed")
            elif choice == '3':
                # Load specific CSV file
                csv_tables = manager.config.get_available_csv_tables()
                if csv_tables:
                    print("\nAvailable tables for CSV import:")
                    for i, table in enumerate(csv_tables, 1):
                        print(f"  {i}. {table}")

                    try:
                        table_choice = int(input("Select table number: ")) - 1
                        if 0 <= table_choice < len(csv_tables):
                            table_name = csv_tables[table_choice]
                            dry_run = input("Dry run? (y/n): ").lower().strip() == 'y'

                            print(f"\nLoading CSV data into {table_name}...")
                            if manager.load_csv_file(table_name, dry_run=dry_run):
                                print(f"CSV loading completed for {table_name}")
                            else:
                                print(f"CSV loading failed for {table_name}")
                        else:
                            print("Invalid selection")
                    except ValueError:
                        print("Invalid input")
                else:
                    print("No CSV files configured")
            elif choice == '4':
                dry_run = input("Dry run? (y/n): ").lower().strip() == 'y'
                print("\nBulk loading all CSV files...")
                if manager.bulk_load_csv_files(dry_run=dry_run):
                    print("Bulk CSV loading completed")
                else:
                    print("Bulk CSV loading failed")
            elif choice == '5':
                print("\nValidating CSV files...")
                results = manager.validate_csv_files()
                if 'error' not in results:
                    print(f"Validation completed: {results['valid_files']}/{results['total_files']} files valid")
                else:
                    print("CSV validation failed")
            elif choice == '6':
                print("\nRunning Maintenance...")
                if manager.run_maintenance_operations():
                    print("Maintenance completed")
                else:
                    print("Maintenance failed")
            elif choice == '7':
                print("\nGenerating Report...")
                report = manager.generate_report()
                if 'error' not in report:
                    report_file = f"interactive_report_{time.strftime('%Y%m%d_%H%M%S')}.json"
                    import json
                    with open(report_file, 'w') as f:
                        json.dump(report, f, indent=2, default=str)
                    print(f"Report saved to: {report_file}")
                else:
                    print("Report generation failed")
            elif choice == '8':
                manager.display_status()
            elif choice == '9':
                if manager.db_service.test_connection():
                    print("Database connection is working")
                else:
                    print("Database connection failed")
            else:
                print("Invalid choice. Please select 0-9.")

        manager.close()
        print("\nGoodbye!")
        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        print(f"Error in interactive mode: {e}")
        return 1


def validate_environment() -> bool:
    """
    Validate the environment and dependencies.

    Returns:
        True if environment is valid
    """
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("Python 3.8+ required")
            return False

        # Check for required directories
        required_dirs = ['config', 'entity', 'services', 'utils', 'tests']
        missing_dirs = []

        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                missing_dirs.append(dir_name)

        if missing_dirs:
            print(f"Missing required directories: {missing_dirs}")
            return False

        # Check MySQL drivers
        drivers = check_driver_availability()
        if not drivers['any_available']:
            print("No MySQL drivers installed")
            print("   Run: pip install mysql-connector-python")
            return False

        return True

    except Exception as e:
        print(f"Environment validation failed: {e}")
        return False


def display_help() -> None:
    """Display comprehensive help information."""
    print("""
MySQL Student Database Management System
========================================

This system provides comprehensive management of a MySQL-based student database
with support for schema creation, data management, CSV import, and maintenance operations.

QUICK START:
-----------
1. Install dependencies: pip install -r requirements.txt
2. Create credentials:    python main.py --create-credentials
3. Edit credentials.json with your MySQL details
4. Initialize database:   python main.py --init --sample-data

CSV OPERATIONS:
--------------
# Load single CSV file
python main.py --load-csv --table-name Students

# Load with custom CSV file
python main.py --load-csv --table-name Students --csv-file /path/to/students.csv

# Bulk load all configured CSV files
python main.py --bulk-load-csv

# Validate CSV files without importing
python main.py --validate-csv

# Dry run to test import without inserting data
python main.py --load-csv --table-name Students --dry-run

USAGE MODES:
-----------
Interactive Mode (recommended for beginners):
    python main.py

Command Line Mode:
    python main.py [options]

COMMON OPERATIONS:
-----------------
# Create database schema
python main.py --init

# Create schema with sample data
python main.py --init --sample-data

# Create specific tables only
python main.py --init --tables Students Teachers Courses

# Drop existing tables and recreate
python main.py --drop --init --sample-data

# Check database status
python main.py --status

# Generate comprehensive report
python main.py --report

# Run maintenance operations
python main.py --maintenance

# Test database connection
python main.py --test-connection

CSV FILE CONFIGURATION:
----------------------
Configure CSV file paths in config.py:
- Students table -> students.csv
- Teachers table -> teachers.csv
- Courses table -> courses.csv
etc.

CONFIGURATION:
-------------
The system can be configured via:
- Environment variables (DB_HOST, DB_PORT, etc.)
- Configuration files (JSON/YAML)
- Command line arguments

For detailed documentation, visit: https://github.com/your-repo/mysql-student-db
""")


def create_project_structure() -> bool:
    """
    Create the basic project structure if it doesn't exist.

    Returns:
        True if structure created successfully
    """
    try:
        directories = [
            'config', 'entity', 'services', 'utils', 'tests', 'logs', 'csv_files'
        ]

        files_to_create = {
            'config/__init__.py': '',
            'entity/__init__.py': '',
            'services/__init__.py': '',
            'utils/__init__.py': '',
            'tests/__init__.py': '',
            'csv_files/README.md': '''# CSV Files Directory

Place your CSV files here for import into the database.

Expected files:
- students.csv
- teachers.csv
- courses.csv
- levels.csv
- evaluation_groups.csv
- evaluation_components.csv
- student_scores.csv

See the documentation for the required column formats for each file.
''',
            '.env.example': '''# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=student_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_CONNECTION_TIMEOUT=30

# CSV Files Path
CSV_FILES_PATH=csv_files

# Operation Flags
CREATE_SCHEMA=true
INSERT_SAMPLE_DATA=false
UPDATE_EXISTING=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=mysql_database.log
''',
            '.gitignore': '''# Credentials and sensitive files
credentials.json
credentials.yaml
.env

# Log files
*.log
logs/

# CSV files (optional - remove if you want to track them)
csv_files/*.csv

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
*.sqlite3

# Reports
*_report_*.json
*_report_*.html
'''
        }

        # Create directories
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)

        # Create files
        for file_path, content in files_to_create.items():
            path = Path(file_path)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content)

        print("Project structure created successfully")
        return True

    except Exception as e:
        print(f"Failed to create project structure: {e}")
        return False


if __name__ == '__main__':
    # Handle special cases first
    if len(sys.argv) > 1:
        if '--help' in sys.argv or '-h' in sys.argv:
            display_help()
            sys.exit(0)
        elif '--setup-project' in sys.argv:
            if create_project_structure():
                print("Project structure created. You can now run the application.")
            sys.exit(0)

    # Validate environment
    if not validate_environment():
        print("\nTry running: python main.py --setup-project")
        sys.exit(1)

    # Run main application
    try:
        if len(sys.argv) == 1:
            # No arguments - run interactive mode
            exit_code = run_interactive_mode()
        else:
            # Command line arguments provided
            exit_code = main()

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
        sys.exit(1)