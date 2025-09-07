"""
CSV Data Loader for MySQL Student Database Management System.

This module provides flexible CSV import functionality for database tables
with validation, error handling, and extensible table configurations.
"""

import csv
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime
import re

from services.db_connection import DatabaseService

logger = logging.getLogger(__name__)


class CSVValidationError(Exception):
    """Custom exception for CSV validation errors."""
    pass


class CSVLoader:
    """
    Flexible CSV loader that can import data into multiple database tables
    with configurable validation and transformation rules.
    """

    def __init__(self, db_service: DatabaseService):
        """
        Initialize CSV loader with database service.

        Args:
            db_service: Database service instance for executing queries
        """
        self.db_service = db_service
        self._table_configs = self._initialize_table_configs()
        self._validation_stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'inserted_rows': 0,
            'failed_rows': 0,
            'errors': []
        }

    def _initialize_table_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize table configurations for CSV import.

        Returns:
            Dictionary mapping table names to their import configurations
        """
        return {
            'Students': {
                'required_columns': [
                    'FirstName', 'LastName', 'Email', 'DateOfBirth',
                    'PhoneNumber', 'Address', 'EnrollmentDate', 'Status'
                ],
                'optional_columns': [],
                'column_validators': {
                    'Email': self._validate_email,
                    'DateOfBirth': self._validate_date,
                    'EnrollmentDate': self._validate_date,
                    'Status': lambda x: x in ['Active', 'Inactive', 'Suspended', 'Graduated'],
                    'PhoneNumber': self._validate_phone
                },
                'column_transformers': {
                    'FirstName': str.strip,
                    'LastName': str.strip,
                    'Email': str.lower,
                    'Status': str.strip
                },
                'insert_query': """
                    INSERT INTO Students (
                        FirstName, LastName, Email, DateOfBirth, PhoneNumber, 
                        Address, EnrollmentDate, Status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': True,
                'duplicate_check_columns': ['Email'],
                'duplicate_query': "SELECT COUNT(*) FROM Students WHERE Email = %s"
            },

            'Courses': {
                'required_columns': [
                    'CourseLevel', 'CourseGroup', 'TeacherID', 'CourseName',
                    'CourseCode', 'Credits', 'Semester', 'AcademicYear', 'MaxStudents'
                ],
                'optional_columns': ['Description', 'Status'],
                'column_validators': {
                    'TeacherID': self._validate_integer,
                    'Credits': self._validate_integer,
                    'MaxStudents': self._validate_integer,
                    'CourseCode': self._validate_course_code
                },
                'column_transformers': {
                    'CourseName': str.strip,
                    'CourseCode': str.upper,
                    'CourseLevel': str.strip,
                    'CourseGroup': str.upper
                },
                'insert_query': """
                    INSERT INTO Courses (
                        CourseLevel, CourseGroup, TeacherID, CourseName, CourseCode, 
                        Description, Credits, Semester, AcademicYear, MaxStudents, Status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': True,
                'duplicate_check_columns': ['CourseCode'],
                'duplicate_query': "SELECT COUNT(*) FROM Courses WHERE CourseCode = %s"
            },

            'Levels': {
                'required_columns': [
                    'CourseID', 'LevelName', 'Weight', 'MaxScore', 'OrderIndex'
                ],
                'optional_columns': ['LevelCode', 'Description', 'IsActive'],
                'column_validators': {
                    'CourseID': self._validate_integer,
                    'Weight': self._validate_decimal,
                    'MaxScore': self._validate_decimal,
                    'OrderIndex': self._validate_integer
                },
                'column_transformers': {
                    'LevelName': str.strip,
                    'LevelCode': str.upper if 'LevelCode' in locals() else str.strip
                },
                'insert_query': """
                    INSERT INTO Levels (
                        CourseID, LevelName, LevelCode, Description, Weight, 
                        MaxScore, OrderIndex, IsActive
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': True,
                'duplicate_check_columns': ['CourseID', 'LevelCode'],
                'duplicate_query': "SELECT COUNT(*) FROM Levels WHERE CourseID = %s AND LevelCode = %s"
            },

            'EvaluationGroups': {
                'required_columns': [
                    'LevelID', 'GroupName', 'Weight', 'MaxScore', 'OrderIndex'
                ],
                'optional_columns': ['GroupCode', 'Description', 'IsActive'],
                'column_validators': {
                    'LevelID': self._validate_integer,
                    'Weight': self._validate_decimal,
                    'MaxScore': self._validate_decimal,
                    'OrderIndex': self._validate_integer
                },
                'column_transformers': {
                    'GroupName': str.strip,
                    'GroupCode': str.upper if 'GroupCode' in locals() else str.strip
                },
                'insert_query': """
                    INSERT INTO EvaluationGroups (
                        LevelID, GroupName, GroupCode, Description, Weight, 
                        MaxScore, OrderIndex, IsActive
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': True,
                'duplicate_check_columns': ['LevelID', 'GroupCode'],
                'duplicate_query': "SELECT COUNT(*) FROM EvaluationGroups WHERE LevelID = %s AND GroupCode = %s"
            },

            'EvaluationComponents': {
                'required_columns': [
                    'CourseID', 'GroupID', 'ComponentName', 'Weight', 'MaxScore', 'OrderIndex'
                ],
                'optional_columns': ['ComponentCode', 'Description', 'DueDate', 'IsActive'],
                'column_validators': {
                    'CourseID': self._validate_integer,
                    'GroupID': self._validate_integer,
                    'Weight': self._validate_decimal,
                    'MaxScore': self._validate_decimal,
                    'OrderIndex': self._validate_integer,
                    'DueDate': self._validate_date
                },
                'column_transformers': {
                    'ComponentName': str.strip,
                    'ComponentCode': str.upper if 'ComponentCode' in locals() else str.strip
                },
                'insert_query': """
                    INSERT INTO EvaluationComponents (
                        CourseID, GroupID, ComponentName, ComponentCode, Description, Weight, 
                        MaxScore, OrderIndex, DueDate, IsActive
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': True,
                'duplicate_check_columns': ['GroupID', 'ComponentCode'],
                'duplicate_query': "SELECT COUNT(*) FROM EvaluationComponents WHERE GroupID = %s AND ComponentCode = %s"
            },

            'StudentScores': {
                'required_columns': [
                    'StudentID', 'CourseID', 'Score', 'MaxPossibleScore', 'Status'
                ],
                'optional_columns': [
                    'LevelID', 'GroupID', 'ComponentID', 'DateCompleted',
                    'Notes', 'Feedback', 'RecordedBy'
                ],
                'column_validators': {
                    'StudentID': self._validate_integer,
                    'CourseID': self._validate_integer,
                    'LevelID': self._validate_optional_integer,
                    'GroupID': self._validate_optional_integer,
                    'ComponentID': self._validate_optional_integer,
                    'Score': self._validate_decimal,
                    'MaxPossibleScore': self._validate_decimal,
                    'DateCompleted': self._validate_date,
                    'RecordedBy': self._validate_optional_integer,
                    'Status': lambda x: x in ['Not Started', 'In Progress', 'Completed', 'Late', 'Exempt']
                },
                'column_transformers': {
                    'Status': str.strip
                },
                'insert_query': """
                    INSERT INTO StudentScores (
                        StudentID, CourseID, LevelID, GroupID, ComponentID, Score, MaxPossibleScore, 
                        DateCompleted, Status, Notes, Feedback, RecordedBy
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                'check_duplicates': False,
                'custom_validation': self._validate_polymorphic_score
            },

            'Teachers': {
                'required_columns': [
                    'FirstName', 'LastName', 'Email', 'PhoneNumber', 'Department', 'HireDate', 'Status'
                ],
                'optional_columns': [],
                'column_validators': {
                    'Email': self._validate_email,
                    'HireDate': self._validate_date,
                    'Status': lambda x: x in ['Active', 'Inactive', 'On Leave'],
                    'PhoneNumber': self._validate_phone
                },
                'column_transformers': {
                    'FirstName': str.strip,
                    'LastName': str.strip,
                    'Email': str.lower,
                    'Department': str.strip,
                    'Status': str.strip
                },
                'insert_query': """
                INSERT INTO Teachers (
                    FirstName, LastName, Email, PhoneNumber, Department, 
                    HireDate, Status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                'check_duplicates': True,
                'duplicate_check_columns': ['Email'],
                'duplicate_query': "SELECT COUNT(*) FROM Teachers WHERE Email = %s"
            },

            'Enrollments': {
                'required_columns': [
                    'StudentID', 'CourseID', 'EnrollmentDate', 'Status'
                ],
                'optional_columns': ['Grade'],
                'column_validators': {
                    'StudentID': self._validate_integer,
                    'CourseID': self._validate_integer,
                    'EnrollmentDate': self._validate_date,
                    'Status': lambda x: x in ['Active', 'Dropped', 'Completed', 'Withdrawn'],
                    'Grade': self._validate_optional_grade
                },
                'column_transformers': {
                    'Status': str.strip
                },
                'insert_query': """
                INSERT INTO Enrollments (
                    StudentID, CourseID, EnrollmentDate, Status, Grade
                ) VALUES (%s, %s, %s, %s, %s)
            """,
                'check_duplicates': True,
                'duplicate_check_columns': ['StudentID', 'CourseID'],
                'duplicate_query': "SELECT COUNT(*) FROM Enrollments WHERE StudentID = %s AND CourseID = %s"
            },
        }

    def load_csv(self, csv_file: str, table_name: str,
                 batch_size: int = 100, skip_duplicates: bool = True,
                 dry_run: bool = False) -> Dict[str, Any]:
        """
        Load data from CSV file into specified table.

        Args:
            csv_file: Path to CSV file
            table_name: Target table name
            batch_size: Number of records to process in each batch
            skip_duplicates: Whether to skip duplicate records
            dry_run: If True, validate data but don't insert

        Returns:
            Dictionary with import statistics and results
        """
        try:
            # Reset statistics
            self._reset_stats()

            # Validate inputs
            csv_path = Path(csv_file)
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_file}")

            if table_name not in self._table_configs:
                raise ValueError(f"Table '{table_name}' not configured for CSV import")

            config = self._table_configs[table_name]

            logger.info(f"Starting CSV import: {csv_file} -> {table_name}")
            logger.info(f"Batch size: {batch_size}, Skip duplicates: {skip_duplicates}, Dry run: {dry_run}")

            # Read and validate CSV
            rows = self._read_csv(csv_file, config)
            self._validation_stats['total_rows'] = len(rows)

            if not rows:
                logger.warning("No data rows found in CSV file")
                return self._get_results()

            # Process in batches
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                batch_num = (i // batch_size) + 1

                logger.info(f"Processing batch {batch_num}: {len(batch)} records")

                if not dry_run:
                    self._process_batch(batch, config, table_name, skip_duplicates)
                else:
                    # For dry run, just validate
                    for row in batch:
                        if self._validate_row(row, config, table_name):
                            self._validation_stats['valid_rows'] += 1
                        else:
                            self._validation_stats['invalid_rows'] += 1

            results = self._get_results()

            if dry_run:
                logger.info(f"Dry run completed: {results['summary']}")
            else:
                logger.info(f"CSV import completed: {results['summary']}")

            return results

        except Exception as e:
            logger.error(f"CSV import failed: {e}")
            self._validation_stats['errors'].append(str(e))
            return self._get_results()

    def _read_csv(self, csv_file: str, config: Dict[str, Any]) -> List[Dict[str, str]]:
        """Read CSV file and perform basic validation."""
        rows = []

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Validate headers
            csv_columns = set(reader.fieldnames or [])
            required_columns = set(config['required_columns'])

            missing_columns = required_columns - csv_columns
            if missing_columns:
                raise CSVValidationError(f"Missing required columns: {missing_columns}")

            # Read all rows
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                try:
                    # Clean empty string values to None for optional fields
                    cleaned_row = {}
                    for key, value in row.items():
                        if value == '' or value is None:
                            cleaned_row[key] = None
                        else:
                            cleaned_row[key] = value.strip() if isinstance(value, str) else value

                    cleaned_row['_row_number'] = row_num
                    rows.append(cleaned_row)

                except Exception as e:
                    error_msg = f"Error reading row {row_num}: {e}"
                    logger.warning(error_msg)
                    self._validation_stats['errors'].append(error_msg)

        logger.info(f"Read {len(rows)} rows from CSV file")
        return rows

    def _process_batch(self, batch: List[Dict[str, str]], config: Dict[str, Any],
                       table_name: str, skip_duplicates: bool) -> None:
        """Process a batch of rows."""
        for row in batch:
            try:
                if self._validate_row(row, config, table_name):
                    if skip_duplicates and self._is_duplicate(row, config):
                        logger.debug(f"Skipping duplicate row {row.get('_row_number', '?')}")
                        continue

                    if self._insert_row(row, config, table_name):
                        self._validation_stats['inserted_rows'] += 1
                    else:
                        self._validation_stats['failed_rows'] += 1
                else:
                    self._validation_stats['invalid_rows'] += 1

            except Exception as e:
                error_msg = f"Error processing row {row.get('_row_number', '?')}: {e}"
                logger.error(error_msg)
                self._validation_stats['errors'].append(error_msg)
                self._validation_stats['failed_rows'] += 1

    def _validate_row(self, row: Dict[str, str], config: Dict[str, Any], table_name: str) -> bool:
        """Validate a single row of data."""
        try:
            # Check required columns
            for col in config['required_columns']:
                if not row.get(col):
                    error_msg = f"Row {row.get('_row_number', '?')}: Missing required value for {col}"
                    logger.warning(error_msg)
                    self._validation_stats['errors'].append(error_msg)
                    return False

            # Apply column validators
            for col, validator in config.get('column_validators', {}).items():
                if col in row and row[col] is not None:
                    try:
                        if not validator(row[col]):
                            error_msg = f"Row {row.get('_row_number', '?')}: Invalid value for {col}: {row[col]}"
                            logger.warning(error_msg)
                            self._validation_stats['errors'].append(error_msg)
                            return False
                    except Exception as e:
                        error_msg = f"Row {row.get('_row_number', '?')}: Validation error for {col}: {e}"
                        logger.warning(error_msg)
                        self._validation_stats['errors'].append(error_msg)
                        return False

            # Custom validation for specific tables
            if 'custom_validation' in config:
                if not config['custom_validation'](row):
                    return False

            self._validation_stats['valid_rows'] += 1
            return True

        except Exception as e:
            error_msg = f"Row {row.get('_row_number', '?')}: Validation failed: {e}"
            logger.error(error_msg)
            self._validation_stats['errors'].append(error_msg)
            return False

    def _insert_row(self, row: Dict[str, str], config: Dict[str, Any], table_name: str) -> bool:
        """Insert a single row into the database."""
        try:
            # Transform data
            transformed_row = self._transform_row(row, config)

            # Prepare values for insertion
            if table_name == 'Students':
                values = (
                    transformed_row['FirstName'], transformed_row['LastName'],
                    transformed_row['Email'], transformed_row['DateOfBirth'],
                    transformed_row['PhoneNumber'], transformed_row['Address'],
                    transformed_row['EnrollmentDate'], transformed_row['Status']
                )
            elif table_name == 'Courses':
                values = (
                    transformed_row['CourseLevel'], transformed_row['CourseGroup'],
                    transformed_row['TeacherID'], transformed_row['CourseName'],
                    transformed_row['CourseCode'], transformed_row.get('Description'),
                    transformed_row['Credits'], transformed_row['Semester'],
                    transformed_row['AcademicYear'], transformed_row['MaxStudents'],
                    transformed_row.get('Status', 'Active')
                )
            elif table_name == 'Levels':
                values = (
                    transformed_row['CourseID'], transformed_row['LevelName'],
                    transformed_row.get('LevelCode'), transformed_row.get('Description'),
                    transformed_row['Weight'], transformed_row['MaxScore'],
                    transformed_row['OrderIndex'], transformed_row.get('IsActive', 1)
                )
            elif table_name == 'EvaluationGroups':
                values = (
                    transformed_row['LevelID'], transformed_row['GroupName'],
                    transformed_row.get('GroupCode'), transformed_row.get('Description'),
                    transformed_row['Weight'], transformed_row['MaxScore'],
                    transformed_row['OrderIndex'], transformed_row.get('IsActive', 1)
                )
            elif table_name == 'EvaluationComponents':
                values = (
                    transformed_row['CourseID'],  # Add CourseID here
                    transformed_row['GroupID'],
                    transformed_row['ComponentName'],
                    transformed_row.get('ComponentCode'),
                    transformed_row.get('Description'),
                    transformed_row['Weight'],
                    transformed_row['MaxScore'],
                    transformed_row['OrderIndex'],
                    transformed_row.get('DueDate'),
                    transformed_row.get('IsActive', 1)
                )
            elif table_name == 'StudentScores':
                values = (
                    transformed_row['StudentID'],
                    transformed_row['CourseID'],  # Add CourseID here
                    transformed_row.get('LevelID'),
                    transformed_row.get('GroupID'),
                    transformed_row.get('ComponentID'),
                    transformed_row['Score'],
                    transformed_row['MaxPossibleScore'],
                    transformed_row.get('DateCompleted'),
                    transformed_row['Status'],
                    transformed_row.get('Notes'),
                    transformed_row.get('Feedback'),
                    transformed_row.get('RecordedBy')
                )
            elif table_name == 'Teachers':
                values = (
                    transformed_row['FirstName'], transformed_row['LastName'],
                    transformed_row['Email'], transformed_row['PhoneNumber'],
                    transformed_row['Department'], transformed_row['HireDate'],
                    transformed_row['Status']
                )
            elif table_name == 'Enrollments':
                values = (
                    transformed_row['StudentID'],
                    transformed_row['CourseID'],
                    transformed_row['EnrollmentDate'],
                    transformed_row['Status'],
                    transformed_row.get('Grade')
                )

            else:
                raise ValueError(f"Insert logic not implemented for table: {table_name}")

            # Execute insert
            self.db_service.execute_query(config['insert_query'], params=values, fetch=False)
            return True

        except Exception as e:
            error_msg = f"Row {row.get('_row_number', '?')}: Insert failed: {e}"
            logger.error(error_msg)
            self._validation_stats['errors'].append(error_msg)
            return False

    def _transform_row(self, row: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformations to row data."""
        transformed = row.copy()

        for col, transformer in config.get('column_transformers', {}).items():
            if col in transformed and transformed[col] is not None:
                try:
                    transformed[col] = transformer(transformed[col])
                except Exception as e:
                    logger.warning(f"Transformation failed for {col}: {e}")

        return transformed

    def _is_duplicate(self, row: Dict[str, str], config: Dict[str, Any]) -> bool:
        """Check if row is a duplicate."""
        if not config.get('check_duplicates', False):
            return False

        try:
            duplicate_columns = config['duplicate_check_columns']
            duplicate_query = config['duplicate_query']

            # Build parameter list for duplicate check
            params = [row[col] for col in duplicate_columns]

            result = self.db_service.execute_query(duplicate_query, params=params)
            return result[0][0] > 0 if result else False

        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False

    # Validation helper methods
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def _validate_date(self, date_str: str) -> bool:
        """Validate date format (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # More flexible phone validation patterns
        patterns = [
            r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',  # Original pattern
            r'^\+1-[0-9]{3}-[0-9]{4}$',  # +1-555-0101 format
            r'^[0-9]{3}-[0-9]{4}$',  # 555-0101 format
            r'^\([0-9]{3}\) [0-9]{3}-[0-9]{4}$',  # (555) 123-4567 format
        ]

        for pattern in patterns:
            if re.match(pattern, phone.strip()):
                return True
        return False

    def _validate_integer(self, value: str) -> bool:
        """Validate integer value."""
        try:
            int(value)
            return True
        except ValueError:
            return False

    def _validate_optional_integer(self, value: str) -> bool:
        """Validate optional integer value."""
        if value is None or value == '':
            return True
        return self._validate_integer(value)

    def _validate_decimal(self, value: str) -> bool:
        """Validate decimal value."""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _validate_course_code(self, code: str) -> bool:
        """Validate course code format."""
        # Example: CS101, MATH201, etc.
        pattern = r'^[A-Z]{2,4}[0-9]{3}$'
        return re.match(pattern, code.upper()) is not None

    def _validate_polymorphic_score(self, row: Dict[str, str]) -> bool:
        """Validate StudentScores polymorphic constraint."""
        level_id = row.get('LevelID')
        group_id = row.get('GroupID')
        component_id = row.get('ComponentID')

        # Exactly one of these should be non-null
        non_null_count = sum(1 for x in [level_id, group_id, component_id]
                             if x is not None and x != '')

        if non_null_count != 1:
            error_msg = f"Row {row.get('_row_number', '?')}: Exactly one of LevelID, GroupID, or ComponentID must be specified"
            logger.warning(error_msg)
            self._validation_stats['errors'].append(error_msg)
            return False

        return True

    def _validate_optional_grade(self, grade: str) -> bool:
        """Validate optional grade value."""
        if grade is None or grade == '' or grade.strip() == '':
            return True

        # Common grade formats: A, B+, C-, etc.
        grade_pattern = r'^[A-F][+-]?$'
        return re.match(grade_pattern, grade.strip()) is not None

    def _reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            'total_rows': 0,
            'valid_rows': 0,
            'invalid_rows': 0,
            'inserted_rows': 0,
            'failed_rows': 0,
            'errors': []
        }

    def _get_results(self) -> Dict[str, Any]:
        """Get import results and statistics."""
        stats = self._validation_stats
        return {
            'success': stats['failed_rows'] == 0 and len(stats['errors']) == 0,
            'statistics': stats,
            'summary': f"Total: {stats['total_rows']}, "
                       f"Valid: {stats['valid_rows']}, "
                       f"Invalid: {stats['invalid_rows']}, "
                       f"Inserted: {stats['inserted_rows']}, "
                       f"Failed: {stats['failed_rows']}"
        }

    def get_supported_tables(self) -> List[str]:
        """Get list of tables supported for CSV import."""
        return list(self._table_configs.keys())

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a table."""
        if table_name not in self._table_configs:
            raise ValueError(f"Table '{table_name}' not configured")

        config = self._table_configs[table_name]
        return {
            'required_columns': config['required_columns'],
            'optional_columns': config.get('optional_columns', []),
            'all_columns': config['required_columns'] + config.get('optional_columns', []),
            'supports_duplicate_check': config.get('check_duplicates', False)
        }

    def generate_sample_csv(self, table_name: str, output_file: str) -> bool:
        """Generate a sample CSV file for a table."""
        try:
            if table_name not in self._table_configs:
                raise ValueError(f"Table '{table_name}' not configured")

            schema = self.get_table_schema(table_name)

            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Write header
                writer.writerow(schema['all_columns'])

                # Write sample data based on table type
                if table_name == 'Students':
                    writer.writerow([
                        'John', 'Doe', 'john.doe@student.edu', '2002-05-15',
                        '+1-555-0101', '123 Main St, City, ST 12345',
                        '2023-09-01', 'Active'
                    ])
                elif table_name == 'Courses':
                    writer.writerow([
                        'Beginner', 'CS', '1', 'Introduction to Programming', 'CS101',
                        'Basic programming concepts', '3', 'Fall', '2023', '30', 'Active'
                    ])
                # Add more sample data for other tables as needed

            logger.info(f"Sample CSV generated: {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate sample CSV: {e}")
            return False


def create_csv_loader(db_service: DatabaseService) -> CSVLoader:
    """
    Factory function to create CSV loader instance.

    Args:
        db_service: Database service instance

    Returns:
        Configured CSVLoader instance
    """
    return CSVLoader(db_service)