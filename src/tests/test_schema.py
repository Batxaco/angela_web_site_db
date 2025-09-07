"""
Unit tests for schema validation and table operations.

This module contains comprehensive tests for database schema validation,
table operations, and data integrity checks.
"""

import unittest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

from config.config import DatabaseConfig
from services.db_connection import DatabaseService
from services.table_operations import (
    TableOperationsService, TableInfo, ColumnInfo, IndexInfo,
    ForeignKeyInfo, TableRelationship
)
from entity.creation_queries import (
    CREATE_TABLE_QUERIES, get_table_creation_query,
    get_creation_queries_by_order, validate_table_dependencies
)


class TestSchemaQueries(unittest.TestCase):
    """Test cases for schema creation queries."""

    def test_get_table_creation_query_valid(self) -> None:
        """Test getting valid table creation query."""
        query = get_table_creation_query('Students')
        self.assertIn('CREATE TABLE IF NOT EXISTS Students', query)
        self.assertIn('StudentID INT PRIMARY KEY AUTO_INCREMENT', query)
        self.assertIn('FirstName VARCHAR(100) NOT NULL', query)

    def test_get_table_creation_query_invalid(self) -> None:
        """Test getting invalid table creation query."""
        with self.assertRaises(KeyError):
            get_table_creation_query('NonexistentTable')

    def test_get_creation_queries_by_order(self) -> None:
        """Test getting creation queries in dependency order."""
        queries = get_creation_queries_by_order()
        table_names = [table for table, _ in queries]

        # Check that Students comes before tables that reference it
        students_index = table_names.index('Students')
        evaluations_index = table_names.index('Evaluations')
        grades_index = table_names.index('Grades')

        self.assertLess(students_index, evaluations_index)
        self.assertLess(students_index, grades_index)

        # Check that Teachers comes before Courses
        teachers_index = table_names.index('Teachers')
        courses_index = table_names.index('Courses')
        self.assertLess(teachers_index, courses_index)

    def test_get_creation_queries_filtered(self) -> None:
        """Test getting filtered creation queries."""
        selected_tables = ['Students', 'Teachers', 'Courses']
        queries = get_creation_queries_by_order(selected_tables)

        self.assertEqual(len(queries), 3)
        table_names = [table for table, _ in queries]
        self.assertEqual(table_names, ['Students', 'Teachers', 'Courses'])

    def test_validate_table_dependencies(self) -> None:
        """Test table dependency validation."""
        dependencies = validate_table_dependencies()

        # Check basic dependencies
        self.assertEqual(dependencies['Students'], [])
        self.assertEqual(dependencies['Teachers'], [])
        self.assertIn('Teachers', dependencies['Courses'])
        self.assertIn('Students', dependencies['Evaluations'])
        self.assertIn('Courses', dependencies['Evaluations'])

    def test_all_required_tables_present(self) -> None:
        """Test that all required tables have creation queries."""
        expected_tables = {
            'Students', 'Teachers', 'Courses', 'EvaluationComponents',
            'Evaluations', 'Grades', 'Tutorials', 'Bans'
        }

        actual_tables = set(CREATE_TABLE_QUERIES.keys())
        self.assertEqual(expected_tables, actual_tables)

    def test_query_syntax_validation(self) -> None:
        """Test basic SQL syntax validation for creation queries."""
        for table_name, query in CREATE_TABLE_QUERIES.items():
            # Basic syntax checks
            self.assertIn('CREATE TABLE IF NOT EXISTS', query)
            self.assertIn(f'{table_name}', query)
            self.assertIn('ENGINE=InnoDB', query)
            self.assertIn('DEFAULT CHARSET=utf8mb4', query)

            # Check for primary key
            self.assertTrue(
                'PRIMARY KEY' in query or 'AUTO_INCREMENT' in query,
                f"Table {table_name} missing primary key"
            )


class TestTableInfo(unittest.TestCase):
    """Test cases for TableInfo dataclass."""

    def test_table_info_creation(self) -> None:
        """Test TableInfo object creation."""
        table_info = TableInfo(
            name='Students',
            engine='InnoDB',
            rows=100,
            avg_row_length=512,
            data_length=51200,
            index_length=16384,
            columns=8,
            indexes=3
        )

        self.assertEqual(table_info.name, 'Students')
        self.assertEqual(table_info.engine, 'InnoDB')
        self.assertEqual(table_info.rows, 100)
        self.assertEqual(table_info.columns, 8)


class TestColumnInfo(unittest.TestCase):
    """Test cases for ColumnInfo dataclass."""

    def test_column_info_creation(self) -> None:
        """Test ColumnInfo object creation."""
        column_info = ColumnInfo(
            name='StudentID',
            data_type='int',
            is_nullable=False,
            key_type='PRI',
            extra='auto_increment'
        )

        self.assertEqual(column_info.name, 'StudentID')
        self.assertEqual(column_info.data_type, 'int')
        self.assertFalse(column_info.is_nullable)
        self.assertEqual(column_info.key_type, 'PRI')


class TestTableOperationsService(unittest.TestCase):
    """Test cases for TableOperationsService class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_db_service = Mock(spec=DatabaseService)
        self.service = TableOperationsService(self.mock_db_service)

    def test_list_all_tables(self) -> None:
        """Test listing all tables."""
        # Mock database response
        mock_results = [
            ('Students', 'InnoDB', 50, 1024, 51200, 16384, None, None, 'Student data', 8, 3),
            ('Teachers', 'InnoDB', 10, 512, 5120, 8192, None, None, 'Teacher data', 6, 2)
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        tables = self.service.list_all_tables()

        self.assertEqual(len(tables), 2)
        self.assertEqual(tables[0].name, 'Students')
        self.assertEqual(tables[0].rows, 50)
        self.assertEqual(tables[1].name, 'Teachers')
        self.assertEqual(tables[1].rows, 10)

    def test_get_table_columns(self) -> None:
        """Test getting table columns."""
        mock_results = [
            ('StudentID', 'int', 'NO', 'PRI', None, 'auto_increment', '', None, None, None),
            ('FirstName', 'varchar(100)', 'NO', '', None, '', 'Student first name', 100, None, None),
            ('Email', 'varchar(255)', 'NO', 'UNI', None, '', 'Student email', 255, None, None)
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        columns = self.service.get_table_columns('Students')

        self.assertEqual(len(columns), 3)
        self.assertEqual(columns[0].name, 'StudentID')
        self.assertEqual(columns[0].key_type, 'PRI')
        self.assertFalse(columns[0].is_nullable)

        self.assertEqual(columns[1].name, 'FirstName')
        self.assertEqual(columns[1].data_type, 'varchar(100)')

        self.assertEqual(columns[2].name, 'Email')
        self.assertEqual(columns[2].key_type, 'UNI')

    def test_get_table_indexes(self) -> None:
        """Test getting table indexes."""
        mock_results = [
            ('PRIMARY', 'StudentID', 0, 'BTREE', 50, ''),
            ('idx_email', 'Email', 1, 'BTREE', 50, 'Email index'),
            ('idx_name', 'FirstName,LastName', 1, 'BTREE', 45, 'Name index')
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        indexes = self.service.get_table_indexes('Students')

        self.assertEqual(len(indexes), 3)

        # Primary key index
        self.assertEqual(indexes[0].name, 'PRIMARY')
        self.assertTrue(indexes[0].is_unique)
        self.assertEqual(indexes[0].columns, ['StudentID'])

        # Email index
        self.assertEqual(indexes[1].name, 'idx_email')
        self.assertFalse(indexes[1].is_unique)

        # Composite name index
        self.assertEqual(indexes[2].name, 'idx_name')
        self.assertEqual(indexes[2].columns, ['FirstName', 'LastName'])

    def test_get_foreign_keys(self) -> None:
        """Test getting foreign key relationships."""
        mock_results = [
            ('fk_courses_teacher', 'Courses', 'TeacherID', 'Teachers', 'TeacherID', 'RESTRICT', 'CASCADE'),
            ('fk_evaluations_student', 'Evaluations', 'StudentID', 'Students', 'StudentID', 'CASCADE', 'CASCADE'),
            ('fk_evaluations_course', 'Evaluations', 'CourseID', 'Courses', 'CourseID', 'CASCADE', 'CASCADE')
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        foreign_keys = self.service.get_foreign_keys()

        self.assertEqual(len(foreign_keys), 3)

        # Course-Teacher relationship
        self.assertEqual(foreign_keys[0].from_table, 'Courses')
        self.assertEqual(foreign_keys[0].from_column, 'TeacherID')
        self.assertEqual(foreign_keys[0].to_table, 'Teachers')
        self.assertEqual(foreign_keys[0].to_column, 'TeacherID')
        self.assertEqual(foreign_keys[0].on_delete, 'RESTRICT')

        # Evaluation-Student relationship
        self.assertEqual(foreign_keys[1].from_table, 'Evaluations')
        self.assertEqual(foreign_keys[1].to_table, 'Students')
        self.assertEqual(foreign_keys[1].on_delete, 'CASCADE')

    def test_get_foreign_keys_filtered(self) -> None:
        """Test getting foreign keys for specific table."""
        mock_results = [
            ('fk_evaluations_student', 'Evaluations', 'StudentID', 'Students', 'StudentID', 'CASCADE', 'CASCADE'),
            ('fk_evaluations_course', 'Evaluations', 'CourseID', 'Courses', 'CourseID', 'CASCADE', 'CASCADE')
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        foreign_keys = self.service.get_foreign_keys('Evaluations')

        self.assertEqual(len(foreign_keys), 2)
        self.mock_db_service.execute_query.assert_called_once()

        # Check that the query was called with table filter
        call_args = self.mock_db_service.execute_query.call_args
        self.assertIn('Evaluations', call_args[0][1])

    def test_check_table_exists_true(self) -> None:
        """Test checking existing table."""
        self.mock_db_service.execute_query.return_value = [(1,)]

        exists = self.service.check_table_exists('Students')

        self.assertTrue(exists)
        self.mock_db_service.execute_query.assert_called_once()

    def test_check_table_exists_false(self) -> None:
        """Test checking non-existing table."""
        self.mock_db_service.execute_query.return_value = [(0,)]

        exists = self.service.check_table_exists('NonExistentTable')

        self.assertFalse(exists)

    def test_get_table_size_info(self) -> None:
        """Test getting table size information."""
        mock_results = [
            (100, 1024, 102400, 20480, 122880, '2023-01-01 10:00:00', '2023-12-01 15:30:00')
        ]

        self.mock_db_service.execute_query.return_value = mock_results

        size_info = self.service.get_table_size_info('Students')

        self.assertEqual(size_info['rows'], 100)
        self.assertEqual(size_info['data_length'], 102400)
        self.assertEqual(size_info['index_length'], 20480)
        self.assertEqual(size_info['total_size'], 122880)
        self.assertAlmostEqual(size_info['total_size_mb'], 0.12, places=2)

    def test_get_table_relationships(self) -> None:
        """Test getting table relationships."""
        # Mock child relationships (where Students is referenced)
        child_mock_results = []

        # Mock parent relationships (where Students references others)
        parent_mock_results = [
            ('fk_grades_student', 'Grades', 'StudentID', 'Students', 'StudentID', 'CASCADE', 'CASCADE'),
            ('fk_evaluations_student', 'Evaluations', 'StudentID', 'Students', 'StudentID', 'CASCADE', 'CASCADE')
        ]

        self.mock_db_service.execute_query.side_effect = [child_mock_results, parent_mock_results]

        relationships = self.service.get_table_relationships('Students')