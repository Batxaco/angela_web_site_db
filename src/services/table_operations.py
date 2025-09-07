"""
Table operations service for MySQL Student Database Management System.

This module provides comprehensive table management operations including
listing tables, analyzing relationships, schema validation, and metadata extraction.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from services.db_connection import DatabaseService, DatabaseConnectionError

logger = logging.getLogger(__name__)


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    engine: str
    rows: int
    avg_row_length: int
    data_length: int
    index_length: int
    columns: int
    indexes: int
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    comment: Optional[str] = None


@dataclass
class ColumnInfo:
    """Information about a table column."""
    name: str
    data_type: str
    is_nullable: bool
    key_type: Optional[str] = None
    default_value: Optional[str] = None
    extra: Optional[str] = None
    comment: Optional[str] = None
    max_length: Optional[int] = None
    numeric_precision: Optional[int] = None
    numeric_scale: Optional[int] = None


@dataclass
class IndexInfo:
    """Information about a table index."""
    name: str
    columns: List[str]
    is_unique: bool
    index_type: str
    cardinality: int
    comment: Optional[str] = None


@dataclass
class ForeignKeyInfo:
    """Information about a foreign key relationship."""
    name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    on_delete: str
    on_update: str


@dataclass
class TableRelationship:
    """Information about table relationships."""
    table: str
    related_table: str
    relationship_type: str  # 'parent', 'child', 'referenced_by'
    foreign_key: ForeignKeyInfo


class TableOperationsService:
    """
    Service for table operations and metadata management.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize table operations service.

        Args:
            db_service: Database service instance
        """
        self.db_service = db_service

    def list_all_tables(self) -> List[TableInfo]:
        """
        Get comprehensive information about all tables in the database.

        Returns:
            List of TableInfo objects with detailed table information
        """
        try:
            query = """
                SELECT 
                    t.TABLE_NAME,
                    t.ENGINE,
                    t.TABLE_ROWS,
                    t.AVG_ROW_LENGTH,
                    t.DATA_LENGTH,
                    t.INDEX_LENGTH,
                    t.CREATE_TIME,
                    t.UPDATE_TIME,
                    t.TABLE_COMMENT,
                    COUNT(DISTINCT c.COLUMN_NAME) as column_count,
                    COUNT(DISTINCT s.INDEX_NAME) as index_count
                FROM information_schema.TABLES t
                LEFT JOIN information_schema.COLUMNS c 
                    ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
                    AND t.TABLE_NAME = c.TABLE_NAME
                LEFT JOIN information_schema.STATISTICS s 
                    ON t.TABLE_SCHEMA = s.TABLE_SCHEMA 
                    AND t.TABLE_NAME = s.TABLE_NAME
                WHERE t.TABLE_SCHEMA = DATABASE()
                    AND t.TABLE_TYPE = 'BASE TABLE'
                GROUP BY t.TABLE_NAME, t.ENGINE, t.TABLE_ROWS, t.AVG_ROW_LENGTH,
                         t.DATA_LENGTH, t.INDEX_LENGTH, t.CREATE_TIME, 
                         t.UPDATE_TIME, t.TABLE_COMMENT
                ORDER BY t.TABLE_NAME
            """

            results = self.db_service.execute_query(query)
            tables = []

            for row in results:
                tables.append(TableInfo(
                    name=row[0],
                    engine=row[1] or 'Unknown',
                    rows=row[2] or 0,
                    avg_row_length=row[3] or 0,
                    data_length=row[4] or 0,
                    index_length=row[5] or 0,
                    created=row[6],
                    updated=row[7],
                    comment=row[8],
                    columns=row[9] or 0,
                    indexes=row[10] or 0
                ))

            logger.info(f"Retrieved information for {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            raise DatabaseConnectionError(f"Failed to list tables: {e}")

    def get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """
        Get detailed column information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of ColumnInfo objects
        """
        try:
            query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    COLUMN_DEFAULT,
                    EXTRA,
                    COLUMN_COMMENT,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """

            results = self.db_service.execute_query(query, (table_name,))
            columns = []

            for row in results:
                columns.append(ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=row[2] == 'YES',
                    key_type=row[3] if row[3] else None,
                    default_value=row[4],
                    extra=row[5] if row[5] else None,
                    comment=row[6] if row[6] else None,
                    max_length=row[7],
                    numeric_precision=row[8],
                    numeric_scale=row[9]
                ))

            logger.debug(f"Retrieved {len(columns)} columns for table {table_name}")
            return columns

        except Exception as e:
            logger.error(f"Error getting columns for table {table_name}: {e}")
            raise DatabaseConnectionError(f"Failed to get columns for {table_name}: {e}")

    def get_table_indexes(self, table_name: str) -> List[IndexInfo]:
        """
        Get index information for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of IndexInfo objects
        """
        try:
            query = """
                SELECT 
                    INDEX_NAME,
                    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as columns,
                    MAX(NON_UNIQUE) as non_unique,
                    MAX(INDEX_TYPE) as index_type,
                    MAX(CARDINALITY) as cardinality,
                    MAX(INDEX_COMMENT) as comment
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
                GROUP BY INDEX_NAME
                ORDER BY INDEX_NAME
            """

            results = self.db_service.execute_query(query, (table_name,))
            indexes = []

            for row in results:
                indexes.append(IndexInfo(
                    name=row[0],
                    columns=row[1].split(',') if row[1] else [],
                    is_unique=row[2] == 0,  # NON_UNIQUE = 0 means unique
                    index_type=row[3] or 'BTREE',
                    cardinality=row[4] or 0,
                    comment=row[5] if row[5] else None
                ))

            logger.debug(f"Retrieved {len(indexes)} indexes for table {table_name}")
            return indexes

        except Exception as e:
            logger.error(f"Error getting indexes for table {table_name}: {e}")
            raise DatabaseConnectionError(f"Failed to get indexes for {table_name}: {e}")

    def get_foreign_keys(self, table_name: Optional[str] = None) -> List[ForeignKeyInfo]:
        """
        Get foreign key relationships for a specific table or all tables.

        Args:
            table_name: Name of the table (optional, gets all if None)

        Returns:
            List of ForeignKeyInfo objects
        """
        try:
            query = """
                SELECT 
                    kcu.CONSTRAINT_NAME,
                    kcu.TABLE_NAME,
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME,
                    rc.DELETE_RULE,
                    rc.UPDATE_RULE
                FROM information_schema.KEY_COLUMN_USAGE kcu
                JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                    ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                    AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
                WHERE kcu.TABLE_SCHEMA = DATABASE()
                    AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """

            params = ()
            if table_name:
                query += " AND kcu.TABLE_NAME = %s"
                params = (table_name,)

            query += " ORDER BY kcu.TABLE_NAME, kcu.CONSTRAINT_NAME"

            results = self.db_service.execute_query(query, params)
            foreign_keys = []

            for row in results:
                foreign_keys.append(ForeignKeyInfo(
                    name=row[0],
                    from_table=row[1],
                    from_column=row[2],
                    to_table=row[3],
                    to_column=row[4],
                    on_delete=row[5],
                    on_update=row[6]
                ))

            logger.debug(f"Retrieved {len(foreign_keys)} foreign keys")
            return foreign_keys

        except Exception as e:
            logger.error(f"Error getting foreign keys: {e}")
            raise DatabaseConnectionError(f"Failed to get foreign keys: {e}")

    def get_table_relationships(self, table_name: str) -> List[TableRelationship]:
        """
        Get all relationships for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of TableRelationship objects
        """
        try:
            relationships = []

            # Get relationships where this table is the child (has foreign keys)
            child_query = """
                SELECT 
                    kcu.CONSTRAINT_NAME,
                    kcu.TABLE_NAME,
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME,
                    rc.DELETE_RULE,
                    rc.UPDATE_RULE
                FROM information_schema.KEY_COLUMN_USAGE kcu
                JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                    ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                    AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
                WHERE kcu.TABLE_SCHEMA = DATABASE()
                    AND kcu.TABLE_NAME = %s
                    AND kcu.REFERENCED_TABLE_NAME IS NOT NULL
            """

            results = self.db_service.execute_query(child_query, (table_name,))
            for row in results:
                fk = ForeignKeyInfo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                relationships.append(TableRelationship(
                    table=table_name,
                    related_table=row[3],
                    relationship_type='parent',
                    foreign_key=fk
                ))

            # Get relationships where this table is the parent (referenced by others)
            parent_query = """
                SELECT 
                    kcu.CONSTRAINT_NAME,
                    kcu.TABLE_NAME,
                    kcu.COLUMN_NAME,
                    kcu.REFERENCED_TABLE_NAME,
                    kcu.REFERENCED_COLUMN_NAME,
                    rc.DELETE_RULE,
                    rc.UPDATE_RULE
                FROM information_schema.KEY_COLUMN_USAGE kcu
                JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                    ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
                    AND kcu.TABLE_SCHEMA = rc.CONSTRAINT_SCHEMA
                WHERE kcu.TABLE_SCHEMA = DATABASE()
                    AND kcu.REFERENCED_TABLE_NAME = %s
            """

            results = self.db_service.execute_query(parent_query, (table_name,))
            for row in results:
                fk = ForeignKeyInfo(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                relationships.append(TableRelationship(
                    table=table_name,
                    related_table=row[1],
                    relationship_type='child',
                    foreign_key=fk
                ))

            logger.debug(f"Retrieved {len(relationships)} relationships for table {table_name}")
            return relationships

        except Exception as e:
            logger.error(f"Error getting relationships for table {table_name}: {e}")
            raise DatabaseConnectionError(f"Failed to get relationships for {table_name}: {e}")

    def check_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if table exists, False otherwise
        """
        try:
            query = """
                SELECT COUNT(*)
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
                    AND TABLE_TYPE = 'BASE TABLE'
            """

            result = self.db_service.execute_query(query, (table_name,))
            exists = result[0][0] > 0

            logger.debug(f"Table {table_name} exists: {exists}")
            return exists

        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {e}")
            return False

    def get_table_size_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get detailed size information for a table.

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with size information
        """
        try:
            query = """
                SELECT 
                    TABLE_ROWS,
                    AVG_ROW_LENGTH,
                    DATA_LENGTH,
                    INDEX_LENGTH,
                    DATA_LENGTH + INDEX_LENGTH as total_size,
                    CREATE_TIME,
                    UPDATE_TIME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = %s
            """

            result = self.db_service.execute_query(query, (table_name,))
            if not result:
                return {}

            row = result[0]
            size_info = {
                'rows': row[0] or 0,
                'avg_row_length': row[1] or 0,
                'data_length': row[2] or 0,
                'index_length': row[3] or 0,
                'total_size': row[4] or 0,
                'data_size_mb': round((row[2] or 0) / 1024 / 1024, 2),
                'index_size_mb': round((row[3] or 0) / 1024 / 1024, 2),
                'total_size_mb': round((row[4] or 0) / 1024 / 1024, 2),
                'created': row[5],
                'updated': row[6]
            }

            logger.debug(f"Retrieved size info for table {table_name}")
            return size_info

        except Exception as e:
            logger.error(f"Error getting size info for table {table_name}: {e}")
            return {}

    def analyze_schema_integrity(self) -> Dict[str, Any]:
        """
        Analyze the integrity of the database schema.

        Returns:
            Dictionary with schema analysis results
        """
        try:
            analysis = {
                'tables': {},
                'foreign_keys': [],
                'orphaned_records': [],
                'missing_indexes': [],
                'issues': []
            }

            # Get all tables
            tables = self.list_all_tables()
            analysis['tables'] = {table.name: table for table in tables}

            # Get all foreign keys
            foreign_keys = self.get_foreign_keys()
            analysis['foreign_keys'] = foreign_keys

            # Check for potential issues
            self._check_missing_primary_keys(analysis)
            self._check_foreign_key_integrity(analysis)
            self._check_table_sizes(analysis)

            logger.info("Schema integrity analysis completed")
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing schema integrity: {e}")
            return {'error': str(e)}

    def _check_missing_primary_keys(self, analysis: Dict[str, Any]) -> None:
        """Check for tables without primary keys."""
        try:
            query = """
                SELECT t.TABLE_NAME
                FROM information_schema.TABLES t
                LEFT JOIN information_schema.COLUMNS c 
                    ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
                    AND t.TABLE_NAME = c.TABLE_NAME
                    AND c.COLUMN_KEY = 'PRI'
                WHERE t.TABLE_SCHEMA = DATABASE()
                    AND t.TABLE_TYPE = 'BASE TABLE'
                    AND c.COLUMN_NAME IS NULL
            """

            results = self.db_service.execute_query(query)
            if results:
                missing_pk_tables = [row[0] for row in results]
                analysis['issues'].append({
                    'type': 'missing_primary_keys',
                    'tables': missing_pk_tables,
                    'severity': 'warning'
                })

        except Exception as e:
            logger.warning(f"Error checking primary keys: {e}")

    def _check_foreign_key_integrity(self, analysis: Dict[str, Any]) -> None:
        """Check foreign key integrity."""
        try:
            # This is a simplified check - in practice you'd want more comprehensive validation
            broken_fks = []

            for fk in analysis['foreign_keys']:
                # Check if referenced table exists
                if not self.check_table_exists(fk.to_table):
                    broken_fks.append({
                        'foreign_key': fk.name,
                        'from_table': fk.from_table,
                        'issue': f"Referenced table '{fk.to_table}' does not exist"
                    })

            if broken_fks:
                analysis['issues'].append({
                    'type': 'broken_foreign_keys',
                    'foreign_keys': broken_fks,
                    'severity': 'error'
                })

        except Exception as e:
            logger.warning(f"Error checking foreign key integrity: {e}")

    def _check_table_sizes(self, analysis: Dict[str, Any]) -> None:
        """Check for unusually large tables."""
        try:
            large_tables = []

            for table_name, table_info in analysis['tables'].items():
                size_mb = (table_info.data_length + table_info.index_length) / 1024 / 1024

                if size_mb > 100:  # Tables larger than 100MB
                    large_tables.append({
                        'table': table_name,
                        'size_mb': round(size_mb, 2),
                        'rows': table_info.rows
                    })

            if large_tables:
                analysis['issues'].append({
                    'type': 'large_tables',
                    'tables': large_tables,
                    'severity': 'info'
                })

        except Exception as e:
            logger.warning(f"Error checking table sizes: {e}")

    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the database.

        Returns:
            Dictionary with database summary information
        """
        try:
            tables = self.list_all_tables()
            foreign_keys = self.get_foreign_keys()

            total_rows = sum(table.rows for table in tables)
            total_data_size = sum(table.data_length for table in tables)
            total_index_size = sum(table.index_length for table in tables)

            summary = {
                'database_info': self.db_service.get_connection_info(),
                'table_count': len(tables),
                'total_rows': total_rows,
                'total_data_size_mb': round(total_data_size / 1024 / 1024, 2),
                'total_index_size_mb': round(total_index_size / 1024 / 1024, 2),
                'total_size_mb': round((total_data_size + total_index_size) / 1024 / 1024, 2),
                'foreign_key_count': len(foreign_keys),
                'tables': [
                    {
                        'name': table.name,
                        'rows': table.rows,
                        'columns': table.columns,
                        'indexes': table.indexes,
                        'size_mb': round((table.data_length + table.index_length) / 1024 / 1024, 2),
                        'engine': table.engine
                    }
                    for table in sorted(tables, key=lambda t: t.name)
                ],
                'relationships': [
                    {
                        'from_table': fk.from_table,
                        'from_column': fk.from_column,
                        'to_table': fk.to_table,
                        'to_column': fk.to_column
                    }
                    for fk in foreign_keys
                ]
            }

            logger.info("Database summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"Error generating database summary: {e}")
            return {'error': str(e)}


def create_table_operations_service(db_service: DatabaseService) -> TableOperationsService:
    """
    Factory function to create table operations service.

    Args:
        db_service: Database service instance

    Returns:
        TableOperationsService instance
    """
    return TableOperationsService(db_service)