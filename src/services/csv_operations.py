"""
CSV Operations Orchestrator for MySQL Student Database Management System.

This module coordinates CSV import operations, integrates with the main application
architecture, and provides command-line interface for CSV operations.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import time

from db_connection import DatabaseService
from csv_loader import CSVLoader, create_csv_loader
from table_operations import TableOperationsService

logger = logging.getLogger(__name__)


class CSVOperationsManager:
    """
    Manager class that orchestrates CSV operations and integrates with the main application.
    """

    def __init__(self, db_service: DatabaseService, table_service: TableOperationsService):
        """
        Initialize CSV operations manager.

        Args:
            db_service: Database service instance
            table_service: Table operations service instance
        """
        self.db_service = db_service
        self.table_service = table_service
        self.csv_loader = create_csv_loader(db_service)
        self._operation_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_records_processed': 0,
            'total_records_inserted': 0,
            'errors': []
        }

    def import_csv_file(self, csv_file: str, table_name: str,
                        batch_size: int = 100, skip_duplicates: bool = True,
                        dry_run: bool = False, backup_table: bool = True) -> Dict[str, Any]:
        """
        Import data from CSV file with comprehensive error handling and validation.

        Args:
            csv_file: Path to CSV file
            table_name: Target table name
            batch_size: Number of records to process in each batch
            skip_duplicates: Whether to skip duplicate records
            dry_run: If True, validate data but don't insert
            backup_table: Whether to backup table before import

        Returns:
            Dictionary with operation results and statistics
        """
        operation_start = time.time()

        try:
            logger.info(f"Starting CSV import operation: {csv_file} -> {table_name}")

            # Validate inputs
            self._validate_import_inputs(csv_file, table_name)

            # Check table exists and get current record count
            if not self.table_service.check_table_exists(table_name):
                raise ValueError(f"Target table '{table_name}' does not exist")

            initial_count = self._get_table_record_count(table_name)
            logger.info(f"Table {table_name} currently has {initial_count} records")

            # Create backup if requested
            backup_file = None
            if backup_table and not dry_run:
                backup_file = self._create_table_backup(table_name)

            # Perform the CSV import
            import_results = self.csv_loader.load_csv(
                csv_file=csv_file,
                table_name=table_name,
                batch_size=batch_size,
                skip_duplicates=skip_duplicates,
                dry_run=dry_run
            )

            # Update operation statistics
            self._update_operation_stats(import_results)

            # Get final record count
            final_count = self._get_table_record_count(table_name) if not dry_run else initial_count
            records_added = final_count - initial_count if not dry_run else 0

            operation_time = time.time() - operation_start

            # Compile comprehensive results
            results = {
                'success': import_results['success'],
                'operation_type': 'dry_run' if dry_run else 'import',
                'csv_file': csv_file,
                'table_name': table_name,
                'initial_record_count': initial_count,
                'final_record_count': final_count,
                'records_added': records_added,
                'operation_time': operation_time,
                'backup_file': backup_file,
                'import_statistics': import_results['statistics'],
                'import_summary': import_results['summary'],
                'errors': import_results['statistics']['errors']
            }

            if import_results['success']:
                logger.info(f"CSV import completed successfully in {operation_time:.2f} seconds")
                self._operation_stats['successful_operations'] += 1
            else:
                logger.error("CSV import completed with errors")
                self._operation_stats['failed_operations'] += 1

            return results

        except Exception as e:
            error_msg = f"CSV import operation failed: {e}"
            logger.error(error_msg)
            self._operation_stats['failed_operations'] += 1
            self._operation_stats['errors'].append(error_msg)

            return {
                'success': False,
                'error': error_msg,
                'operation_time': time.time() - operation_start,
                'csv_file': csv_file,
                'table_name': table_name
            }

    def bulk_import_csv_files(self, import_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import multiple CSV files based on configuration.

        Args:
            import_config: Configuration dictionary with file mappings

        Returns:
            Dictionary with bulk import results
        """
        try:
            logger.info("Starting bulk CSV import operation")

            total_files = len(import_config.get('files', []))
            successful_imports = 0
            failed_imports = 0
            all_results = []

            for file_config in import_config.get('files', []):
                csv_file = file_config['csv_file']
                table_name = file_config['table_name']

                # Use per-file settings or defaults
                batch_size = file_config.get('batch_size', import_config.get('batch_size', 100))
                skip_duplicates = file_config.get('skip_duplicates', import_config.get('skip_duplicates', True))
                dry_run = file_config.get('dry_run', import_config.get('dry_run', False))

                logger.info(f"Processing file {successful_imports + failed_imports + 1}/{total_files}: {csv_file}")

                result = self.import_csv_file(
                    csv_file=csv_file,
                    table_name=table_name,
                    batch_size=batch_size,
                    skip_duplicates=skip_duplicates,
                    dry_run=dry_run
                )

                all_results.append(result)

                if result['success']:
                    successful_imports += 1
                else:
                    failed_imports += 1

            bulk_results = {
                'success': failed_imports == 0,
                'total_files': total_files,
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'individual_results': all_results,
                'summary': f"Bulk import: {successful_imports}/{total_files} files imported successfully"
            }

            logger.info(bulk_results['summary'])
            return bulk_results

        except Exception as e:
            error_msg = f"Bulk CSV import failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'total_files': 0,
                'successful_imports': 0,
                'failed_imports': 0
            }

    def generate_sample_csv_files(self, output_directory: str, tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate sample CSV files for supported tables.

        Args:
            output_directory: Directory to create sample CSV files
            tables: Optional list of specific tables, or None for all supported tables

        Returns:
            Dictionary with generation results
        """
        try:
            output_dir = Path(output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)

            target_tables = tables or self.csv_loader.get_supported_tables()
            generated_files = []
            failed_files = []

            for table_name in target_tables:
                try:
                    output_file = output_dir / f"{table_name.lower()}_sample.csv"

                    if self.csv_loader.generate_sample_csv(table_name, str(output_file)):
                        generated_files.append(str(output_file))
                        logger.info(f"Generated sample CSV: {output_file}")
                    else:
                        failed_files.append(table_name)

                except Exception as e:
                    logger.error(f"Failed to generate sample CSV for {table_name}: {e}")
                    failed_files.append(table_name)

            results = {
                'success': len(failed_files) == 0,
                'output_directory': str(output_dir),
                'generated_files': generated_files,
                'failed_tables': failed_files,
                'summary': f"Generated {len(generated_files)} sample CSV files"
            }

            logger.info(results['summary'])
            return results

        except Exception as e:
            error_msg = f"Sample CSV generation failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'generated_files': [],
                'failed_tables': []
            }

    def validate_csv_file(self, csv_file: str, table_name: str) -> Dict[str, Any]:
        """
        Validate CSV file without importing data.

        Args:
            csv_file: Path to CSV file
            table_name: Target table name

        Returns:
            Dictionary with validation results
        """
        try:
            logger.info(f"Validating CSV file: {csv_file} for table: {table_name}")

            # Perform dry run to validate
            validation_results = self.csv_loader.load_csv(
                csv_file=csv_file,
                table_name=table_name,
                dry_run=True
            )

            return {
                'success': validation_results['success'],
                'valid': validation_results['statistics']['valid_rows'],
                'invalid': validation_results['statistics']['invalid_rows'],
                'total': validation_results['statistics']['total_rows'],
                'errors': validation_results['statistics']['errors'],
                'summary': validation_results['summary']
            }

        except Exception as e:
            error_msg = f"CSV validation failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'valid': 0,
                'invalid': 0,
                'total': 0
            }

    def get_table_schema_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get schema information for CSV import.

        Args:
            table_name: Table name

        Returns:
            Dictionary with schema information
        """
        try:
            if table_name not in self.csv_loader.get_supported_tables():
                return {
                    'supported': False,
                    'error': f"Table '{table_name}' not supported for CSV import"
                }

            schema = self.csv_loader.get_table_schema(table_name)

            return {
                'supported': True,
                'table_name': table_name,
                'schema': schema,
                'csv_requirements': {
                    'required_columns': schema['required_columns'],
                    'optional_columns': schema['optional_columns'],
                    'total_columns': len(schema['all_columns']),
                    'supports_duplicate_check': schema['supports_duplicate_check']
                }
            }

        except Exception as e:
            return {
                'supported': False,
                'error': f"Failed to get schema info: {e}"
            }

    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive operation statistics."""
        return {
            'session_statistics': self._operation_stats.copy(),
            'supported_tables': self.csv_loader.get_supported_tables(),
            'total_supported_tables': len(self.csv_loader.get_supported_tables())
        }

    def export_table_to_csv(self, table_name: str, output_file: str,
                            limit: Optional[int] = None, where_clause: str = None) -> Dict[str, Any]:
        """
        Export table data to CSV file.

        Args:
            table_name: Source table name
            output_file: Output CSV file path
            limit: Optional limit on number of records
            where_clause: Optional WHERE clause for filtering

        Returns:
            Dictionary with export results
        """
        try:
            logger.info(f"Exporting table {table_name} to CSV: {output_file}")

            # Check table exists
            if not self.table_service.check_table_exists(table_name):
                raise ValueError(f"Table '{table_name}' does not exist")

            # Build query
            query = f"SELECT * FROM {table_name}"
            if where_clause:
                query += f" WHERE {where_clause}"
            if limit:
                query += f" LIMIT {limit}"

            # Execute query
            results = self.db_service.execute_query(query)

            if not results:
                return {
                    'success': True,
                    'records_exported': 0,
                    'output_file': output_file,
                    'message': 'No data to export'
                }

            # Get column names
            column_query = f"DESCRIBE {table_name}"
            column_results = self.db_service.execute_query(column_query)
            column_names = [row[0] for row in column_results]

            # Write to CSV
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(column_names)  # Header
                writer.writerows(results)

            logger.info(f"Exported {len(results)} records to {output_file}")

            return {
                'success': True,
                'records_exported': len(results),
                'output_file': output_file,
                'columns': column_names
            }

        except Exception as e:
            error_msg = f"Table export failed: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'records_exported': 0
            }

    def create_import_configuration(self, config_file: str, file_mappings: List[Dict[str, str]]) -> bool:
        """
        Create import configuration file for bulk operations.

        Args:
            config_file: Path to configuration file
            file_mappings: List of file to table mappings

        Returns:
            True if configuration created successfully
        """
        try:
            config = {
                'version': '1.0',
                'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                'batch_size': 100,
                'skip_duplicates': True,
                'dry_run': False,
                'files': file_mappings
            }

            with open(config_file, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=2)

            logger.info(f"Created import configuration: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create configuration: {e}")
            return False

    # Private helper methods
    def _validate_import_inputs(self, csv_file: str, table_name: str) -> None:
        """Validate import operation inputs."""
        csv_path = Path(csv_file)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        if not csv_path.suffix.lower() == '.csv':
            raise ValueError(f"File must have .csv extension: {csv_file}")

        if table_name not in self.csv_loader.get_supported_tables():
            supported = ', '.join(self.csv_loader.get_supported_tables())
            raise ValueError(f"Table '{table_name}' not supported. Supported tables: {supported}")

    def _get_table_record_count(self, table_name: str) -> int:
        """Get current record count for a table."""
        try:
            result = self.db_service.execute_query(f"SELECT COUNT(*) FROM {table_name}")
            return result[0][0] if result else 0
        except Exception:
            return 0

    def _create_table_backup(self, table_name: str) -> Optional[str]:
        """Create backup of table before import."""
        try:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            backup_table = f"{table_name}_backup_{timestamp}"

            backup_query = f"CREATE TABLE {backup_table} AS SELECT * FROM {table_name}"
            self.db_service.execute_query(backup_query, fetch=False)

            logger.info(f"Created backup table: {backup_table}")
            return backup_table

        except Exception as e:
            logger.warning(f"Failed to create backup for {table_name}: {e}")
            return None

    def _update_operation_stats(self, import_results: Dict[str, Any]) -> None:
        """Update operation statistics."""
        stats = import_results['statistics']
        self._operation_stats['total_operations'] += 1
        self._operation_stats['total_records_processed'] += stats['total_rows']
        self._operation_stats['total_records_inserted'] += stats['inserted_rows']

        if import_results['success']:
            self._operation_stats['successful_operations'] += 1
        else:
            self._operation_stats['failed_operations'] += 1
            self._operation_stats['errors'].extend(stats['errors'])


def create_csv_operations_manager(db_service: DatabaseService,
                                  table_service: TableOperationsService) -> CSVOperationsManager:
    """
    Factory function to create CSV operations manager.

    Args:
        db_service: Database service instance
        table_service: Table operations service instance

    Returns:
        Configured CSVOperationsManager instance
    """
    return CSVOperationsManager(db_service, table_service)