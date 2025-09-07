"""
Enhanced table dropping functionality for the MySQL Student Database Management System.
Fixed version that dynamically discovers tables and handles foreign keys properly.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TableDropManager:
    """
    Enhanced manager for safely dropping database tables with proper dependency handling.
    """

    def __init__(self, db_service, table_service):
        """
        Initialize the table drop manager.

        Args:
            db_service: Database service instance
            table_service: Table operations service instance
        """
        self.db_service = db_service
        self.table_service = table_service

    def drop_all_tables(self, confirm: bool = False, force: bool = False) -> Dict[str, Any]:
        """
        Drop all tables in the correct order.

        Args:
            confirm: Whether user has confirmed the operation
            force: Whether to disable foreign key checks (dangerous!)

        Returns:
            Dictionary with operation results
        """
        results = {
            'success': True,
            'tables_dropped': [],
            'tables_failed': [],
            'errors': [],
            'warnings': []
        }

        try:
            # Safety check
            if not confirm and not self._confirm_drop_operation():
                results['success'] = False
                results['errors'].append("Operation cancelled by user")
                return results

            # Get existing tables
            existing_tables = self._get_existing_tables()

            if not existing_tables:
                logger.info("No tables found to drop")
                results['warnings'].append("No tables found in database")
                return results

            logger.info(f"Found {len(existing_tables)} tables: {existing_tables}")

            if force:
                # Force mode: Disable foreign key checks and drop all tables
                logger.warning("Using FORCE MODE - disabling foreign key checks")
                results['warnings'].append("Foreign key checks disabled")
                return self._force_drop_all_tables(existing_tables, results)
            else:
                # Safe mode: Try to determine correct order
                return self._safe_drop_all_tables(existing_tables, results)

        except Exception as e:
            logger.error(f"Error during table drop operation: {e}")
            results['success'] = False
            results['errors'].append(str(e))

            # Always re-enable foreign key checks on error
            try:
                self.db_service.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch=False)
            except:
                pass

        return results

    def _force_drop_all_tables(self, tables: List[str], results: Dict[str, Any]) -> Dict[str, Any]:
        """Drop all tables with foreign key checks disabled."""
        try:
            # Disable foreign key checks
            self.db_service.execute_query("SET FOREIGN_KEY_CHECKS = 0", fetch=False)

            # Drop all tables
            for table_name in tables:
                if self._drop_single_table(table_name):
                    results['tables_dropped'].append(table_name)
                    logger.info(f"Successfully dropped table: {table_name}")
                else:
                    results['tables_failed'].append(table_name)
                    results['errors'].append(f"Failed to drop table: {table_name}")

            # Re-enable foreign key checks
            self.db_service.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch=False)
            logger.info("Re-enabled foreign key checks")

            results['success'] = len(results['tables_failed']) == 0

        except Exception as e:
            logger.error(f"Force drop failed: {e}")
            results['success'] = False
            results['errors'].append(f"Force drop failed: {e}")

            # Always re-enable foreign key checks
            try:
                self.db_service.execute_query("SET FOREIGN_KEY_CHECKS = 1", fetch=False)
            except:
                pass

        return results

    def _safe_drop_all_tables(self, tables: List[str], results: Dict[str, Any]) -> Dict[str, Any]:
        """Try to drop tables in safe order based on foreign key dependencies."""
        try:
            # Get foreign key dependencies
            dependencies = self._get_foreign_key_dependencies()

            # Calculate drop order
            drop_order = self._calculate_drop_order(tables, dependencies)

            logger.info(f"Calculated drop order: {drop_order}")

            # Drop tables in order
            for table_name in drop_order:
                if self._drop_single_table(table_name):
                    results['tables_dropped'].append(table_name)
                    logger.info(f"Successfully dropped table: {table_name}")
                else:
                    results['tables_failed'].append(table_name)
                    results['errors'].append(f"Failed to drop table: {table_name}")
                    # Continue with other tables even if one fails

            results['success'] = len(results['tables_failed']) == 0

            # If some tables failed, suggest force mode
            if results['tables_failed']:
                results['warnings'].append(
                    "Some tables failed to drop due to foreign key constraints. "
                    "Try using --force-drop to disable foreign key checks."
                )

        except Exception as e:
            logger.error(f"Safe drop failed: {e}")
            results['success'] = False
            results['errors'].append(f"Safe drop failed: {e}")

        return results

    def _get_foreign_key_dependencies(self) -> Dict[str, List[str]]:
        """Get foreign key dependencies for all tables."""
        dependencies = {}

        try:
            # Query to get all foreign key relationships
            query = """
                SELECT 
                    TABLE_NAME,
                    REFERENCED_TABLE_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = DATABASE()
                    AND REFERENCED_TABLE_NAME IS NOT NULL
            """

            result = self.db_service.execute_query(query)

            for row in result:
                child_table = row[0]
                parent_table = row[1]

                if child_table not in dependencies:
                    dependencies[child_table] = []

                if parent_table not in dependencies[child_table]:
                    dependencies[child_table].append(parent_table)

            logger.debug(f"Foreign key dependencies: {dependencies}")

        except Exception as e:
            logger.warning(f"Failed to get foreign key dependencies: {e}")

        return dependencies

    def _calculate_drop_order(self, tables: List[str], dependencies: Dict[str, List[str]]) -> List[str]:
        """Calculate the order to drop tables based on dependencies."""

        # Simple topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        drop_order = []

        def visit(table):
            if table in temp_visited:
                # Circular dependency detected, skip this ordering
                return

            if table in visited:
                return

            temp_visited.add(table)

            # Visit all tables that this table depends on (parents)
            for parent in dependencies.get(table, []):
                if parent in tables:  # Only consider tables we're actually dropping
                    visit(parent)

            temp_visited.remove(table)
            visited.add(table)

            # Add to drop order (children first, then parents)
            if table not in drop_order:
                drop_order.insert(0, table)

        # Visit all tables
        for table in tables:
            if table not in visited:
                visit(table)

        # Add any remaining tables that weren't in the dependency chain
        for table in tables:
            if table not in drop_order:
                drop_order.append(table)

        return drop_order

    def create_backup_before_drop(self, backup_dir: str = "backups") -> Optional[str]:
        """
        Create a backup of all tables before dropping them.

        Args:
            backup_dir: Directory to store backup files

        Returns:
            Path to backup directory or None if failed
        """
        try:
            import time
            from datetime import datetime

            # Create backup directory
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = backup_path / f"backup_{timestamp}"
            backup_subdir.mkdir()

            existing_tables = self._get_existing_tables()

            for table_name in existing_tables:
                try:
                    # Export table structure
                    structure_query = f"SHOW CREATE TABLE `{table_name}`"
                    structure_result = self.db_service.execute_query(structure_query)

                    if structure_result:
                        structure_file = backup_subdir / f"{table_name}_structure.sql"
                        with open(structure_file, 'w', encoding='utf-8') as f:
                            f.write(f"-- Table structure for {table_name}\n")
                            f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                            f.write(structure_result[0][1] + ";\n\n")

                    # Export table data
                    data_query = f"SELECT * FROM `{table_name}`"
                    data_result = self.db_service.execute_query(data_query)

                    if data_result:
                        # Get column names
                        columns_query = f"DESCRIBE `{table_name}`"
                        columns_result = self.db_service.execute_query(columns_query)
                        column_names = [row[0] for row in columns_result]

                        # Write CSV data
                        import csv
                        data_file = backup_subdir / f"{table_name}_data.csv"
                        with open(data_file, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow(column_names)  # Header
                            writer.writerows(data_result)  # Data

                    logger.info(f"Backed up table: {table_name}")

                except Exception as e:
                    logger.warning(f"Failed to backup table {table_name}: {e}")

            # Create backup info file
            info_file = backup_subdir / "backup_info.txt"
            with open(info_file, 'w', encoding='utf-8') as f:
                f.write(f"Backup created: {datetime.now()}\n")
                f.write(f"Tables backed up: {len(existing_tables)}\n")
                f.write(f"Table list: {', '.join(existing_tables)}\n")

            logger.info(f"Backup completed: {backup_subdir}")
            return str(backup_subdir)

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None

    def _confirm_drop_operation(self) -> bool:
        """Prompt user to confirm the destructive operation."""
        try:
            print("\n" + "="*60)
            print("WARNING: DESTRUCTIVE OPERATION")
            print("="*60)
            print("You are about to DROP database tables.")
            print("This operation will PERMANENTLY DELETE all data in the selected tables.")
            print("This action CANNOT be undone!")
            print("="*60)

            response = input("Type 'DELETE' to confirm this operation: ").strip()
            return response == 'DELETE'

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return False

    def _get_existing_tables(self) -> List[str]:
        """Get list of existing tables in the database."""
        try:
            query = """
                SELECT TABLE_NAME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """
            result = self.db_service.execute_query(query)
            return [row[0] for row in result] if result else []
        except Exception as e:
            logger.error(f"Failed to get existing tables: {e}")
            return []

    def _drop_single_table(self, table_name: str) -> bool:
        """Drop a single table."""
        try:
            # Use backticks to handle reserved words and special characters
            drop_query = f"DROP TABLE IF EXISTS `{table_name}`"
            self.db_service.execute_query(drop_query, fetch=False)
            return True
        except Exception as e:
            logger.error(f"Failed to drop table {table_name}: {e}")
            return False