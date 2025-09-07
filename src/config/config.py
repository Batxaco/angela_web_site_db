"""
Configuration management for MySQL Student Database Management System.

This module handles configuration loading from multiple sources including
environment variables, configuration files, and default settings.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    # Connection settings
    host: str = 'localhost'
    port: int = 3306
    database: str = 'student_database'
    username: str = 'root'
    password: str = ''
    connection_timeout: int = 30
    pool_size: int = 5
    retry_attempts: int = 3

    # Operation flags
    create_schema: bool = True
    insert_sample_data: bool = False
    drop_existing: bool = False
    update_existing: bool = False
    create_views: bool = True
    create_procedures: bool = True

    # Table selection
    selected_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None

    # CSV file paths configuration
    csv_files_base_path: str = 'csv_files'
    csv_file_mappings: Dict[str, str] = field(default_factory=lambda: {
        'Students': 'students.csv',
        'Teachers': 'teachers.csv',
        'Courses': 'courses.csv',
        'Levels': 'levels.csv',
        'EvaluationGroups': 'evaluation_groups.csv',
        'EvaluationComponents': 'evaluation_components.csv',
        'StudentScores': 'student_scores.csv',
        'Enrollments': 'enrollments.csv',
        'Attendance': 'attendance.csv',
        'Grades': 'grades.csv'
    })

    # Logging configuration
    log_level: str = 'INFO'
    log_file: Optional[str] = 'mysql_database.log'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Performance settings
    batch_size: int = 100
    max_connections: int = 10

    # Internal configuration data
    _config_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization to set up derived configurations."""
        # Ensure csv_files_base_path is absolute
        if not os.path.isabs(self.csv_files_base_path):
            self.csv_files_base_path = os.path.abspath(self.csv_files_base_path)

        # Create CSV directory if it doesn't exist
        Path(self.csv_files_base_path).mkdir(parents=True, exist_ok=True)

    def get_csv_file_path(self, table_name: str) -> Optional[str]:
        """
        Get the full path to a CSV file for a given table.

        Args:
            table_name: Name of the database table

        Returns:
            Full path to CSV file or None if not configured
        """
        if table_name not in self.csv_file_mappings:
            return None

        csv_filename = self.csv_file_mappings[table_name]
        return os.path.join(self.csv_files_base_path, csv_filename)

    def get_available_csv_tables(self) -> List[str]:
        """
        Get list of tables that have CSV files configured.

        Returns:
            List of table names with CSV configurations
        """
        available_tables = []

        for table_name, csv_filename in self.csv_file_mappings.items():
            csv_path = os.path.join(self.csv_files_base_path, csv_filename)
            if os.path.exists(csv_path):
                available_tables.append(table_name)

        return available_tables

    def get_missing_csv_files(self) -> Dict[str, str]:
        """
        Get list of configured CSV files that don't exist.

        Returns:
            Dictionary mapping table names to missing CSV file paths
        """
        missing_files = {}

        for table_name, csv_filename in self.csv_file_mappings.items():
            csv_path = os.path.join(self.csv_files_base_path, csv_filename)
            if not os.path.exists(csv_path):
                missing_files[table_name] = csv_path

        return missing_files

    def add_csv_mapping(self, table_name: str, csv_filename: str) -> None:
        """
        Add a new CSV file mapping.

        Args:
            table_name: Name of the database table
            csv_filename: Name of the CSV file (relative to base path)
        """
        self.csv_file_mappings[table_name] = csv_filename

    def remove_csv_mapping(self, table_name: str) -> bool:
        """
        Remove a CSV file mapping.

        Args:
            table_name: Name of the database table

        Returns:
            True if mapping was removed, False if it didn't exist
        """
        if table_name in self.csv_file_mappings:
            del self.csv_file_mappings[table_name]
            return True
        return False

    def set_csv_base_path(self, base_path: str) -> None:
        """
        Set the base path for CSV files.

        Args:
            base_path: New base path for CSV files
        """
        self.csv_files_base_path = os.path.abspath(base_path)
        Path(self.csv_files_base_path).mkdir(parents=True, exist_ok=True)

    def get_table_list(self) -> List[str]:
        # Import the actual table order from entity module
        from entity.creation_queries import TABLE_CREATION_ORDER

        if self.selected_tables:
            return self.selected_tables

        tables = TABLE_CREATION_ORDER.copy()

        if self.exclude_tables:
            tables = [t for t in tables if t not in self.exclude_tables]

        return tables

    def validate_csv_configuration(self) -> Dict[str, Any]:
        """
        Validate CSV file configuration.

        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'configured_tables': len(self.csv_file_mappings),
            'existing_files': 0,
            'missing_files': 0
        }

        # Check base path
        if not os.path.exists(self.csv_files_base_path):
            results['errors'].append(f"CSV base path does not exist: {self.csv_files_base_path}")
            results['valid'] = False
            return results

        # Check individual files
        missing_files = self.get_missing_csv_files()
        existing_files = self.get_available_csv_tables()

        results['existing_files'] = len(existing_files)
        results['missing_files'] = len(missing_files)

        if missing_files:
            results['warnings'].extend([
                f"Missing CSV file for {table}: {path}"
                for table, path in missing_files.items()
            ])

        # Check for duplicate filenames
        filenames = list(self.csv_file_mappings.values())
        if len(filenames) != len(set(filenames)):
            results['errors'].append("Duplicate CSV filenames found in configuration")
            results['valid'] = False

        return results

    def generate_sample_csv_files(self) -> bool:
        """
        Generate sample CSV files with headers for all configured tables.

        Returns:
            True if sample files were created successfully
        """
        try:
            # Sample data for different tables
            csv_samples = {
                'Students': {
                    'headers': ['FirstName', 'LastName', 'Email', 'DateOfBirth', 'PhoneNumber', 'Address', 'EnrollmentDate', 'Status'],
                    'sample_row': ['John', 'Doe', 'john.doe@student.edu', '2002-05-15', '+1-555-0101', '123 Main St, City, ST 12345', '2023-09-01', 'Active']
                },
                'Teachers': {
                    'headers': ['FirstName', 'LastName', 'Email', 'PhoneNumber', 'Department', 'HireDate', 'Status'],
                    'sample_row': ['Jane', 'Smith', 'jane.smith@school.edu', '+1-555-0102', 'Computer Science', '2020-08-15', 'Active']
                },
                'Courses': {
                    'headers': ['CourseLevel', 'CourseGroup', 'TeacherID', 'CourseName', 'CourseCode', 'Description', 'Credits', 'Semester', 'AcademicYear', 'MaxStudents', 'Status'],
                    'sample_row': ['Beginner', 'CS', '1', 'Introduction to Programming', 'CS101', 'Basic programming concepts', '3', 'Fall', '2023', '30', 'Active']
                },
                'Levels': {
                    'headers': ['CourseID', 'LevelName', 'LevelCode', 'Description', 'Weight', 'MaxScore', 'OrderIndex', 'IsActive'],
                    'sample_row': ['1', 'Assignments', 'ASSIGN', 'Course assignments', '0.40', '100', '1', '1']
                },
                'EvaluationGroups': {
                    'headers': ['LevelID', 'GroupName', 'GroupCode', 'Description', 'Weight', 'MaxScore', 'OrderIndex', 'IsActive'],
                    'sample_row': ['1', 'Homework', 'HW', 'Weekly homework assignments', '0.60', '100', '1', '1']
                },
                'EvaluationComponents': {
                    'headers': ['GroupID', 'ComponentName', 'ComponentCode', 'Description', 'Weight', 'MaxScore', 'OrderIndex', 'DueDate', 'IsActive'],
                    'sample_row': ['1', 'Homework 1', 'HW1', 'First homework assignment', '0.10', '100', '1', '2023-09-15', '1']
                },
                'StudentScores': {
                    'headers': ['StudentID', 'LevelID', 'GroupID', 'ComponentID', 'Score', 'MaxPossibleScore', 'DateCompleted', 'Status', 'Notes', 'Feedback', 'RecordedBy'],
                    'sample_row': ['1', '', '1', '', '85', '100', '2023-09-14', 'Completed', 'Good work', 'Well done on this assignment', '1']
                },
                'Enrollments': {
                    'headers': ['StudentID', 'CourseID', 'EnrollmentDate', 'Status', 'Grade'],
                    'sample_row': ['1', '1', '2023-09-01', 'Active', '']
                },
                'Attendance': {
                    'headers': ['StudentID', 'CourseID', 'AttendanceDate', 'Status', 'Notes'],
                    'sample_row': ['1', '1', '2023-09-01', 'Present', '']
                },
                'Grades': {
                    'headers': ['StudentID', 'CourseID', 'GradeType', 'Grade', 'Points', 'DateRecorded', 'Semester', 'AcademicYear'],
                    'sample_row': ['1', '1', 'Final', 'A', '4.0', '2023-12-15', 'Fall', '2023']
                }
            }

            import csv
            created_files = []

            for table_name, csv_filename in self.csv_file_mappings.items():
                csv_path = os.path.join(self.csv_files_base_path, csv_filename)

                # Skip if file already exists
                if os.path.exists(csv_path):
                    continue

                # Get sample data
                sample_data = csv_samples.get(table_name)
                if not sample_data:
                    continue

                # Create CSV file
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(sample_data['headers'])
                    writer.writerow(sample_data['sample_row'])

                created_files.append(csv_path)
                logger.info(f"Created sample CSV file: {csv_path}")

            if created_files:
                logger.info(f"Generated {len(created_files)} sample CSV files")
            else:
                logger.info("No new sample CSV files needed (files already exist)")

            return True

        except Exception as e:
            logger.error(f"Failed to generate sample CSV files: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database': {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'username': self.username,
                'connection_timeout': self.connection_timeout,
                'pool_size': self.pool_size,
                'retry_attempts': self.retry_attempts
            },
            'operations': {
                'create_schema': self.create_schema,
                'insert_sample_data': self.insert_sample_data,
                'drop_existing': self.drop_existing,
                'update_existing': self.update_existing,
                'create_views': self.create_views,
                'create_procedures': self.create_procedures
            },
            'tables': {
                'selected_tables': self.selected_tables,
                'exclude_tables': self.exclude_tables
            },
            'csv_files': {
                'base_path': self.csv_files_base_path,
                'mappings': self.csv_file_mappings
            },
            'logging': {
                'level': self.log_level,
                'file': self.log_file,
                'format': self.log_format
            },
            'performance': {
                'batch_size': self.batch_size,
                'max_connections': self.max_connections
            }
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'DatabaseConfig':
        """Create configuration from dictionary."""
        config = cls()

        # Update from dictionary sections
        if 'database' in config_dict:
            db_config = config_dict['database']
            config.host = db_config.get('host', config.host)
            config.port = db_config.get('port', config.port)
            config.database = db_config.get('database', config.database)
            config.username = db_config.get('username', config.username)
            config.password = db_config.get('password', config.password)
            config.connection_timeout = db_config.get('connection_timeout', config.connection_timeout)
            config.pool_size = db_config.get('pool_size', config.pool_size)
            config.retry_attempts = db_config.get('retry_attempts', config.retry_attempts)

        if 'operations' in config_dict:
            ops_config = config_dict['operations']
            config.create_schema = ops_config.get('create_schema', config.create_schema)
            config.insert_sample_data = ops_config.get('insert_sample_data', config.insert_sample_data)
            config.drop_existing = ops_config.get('drop_existing', config.drop_existing)
            config.update_existing = ops_config.get('update_existing', config.update_existing)
            config.create_views = ops_config.get('create_views', config.create_views)
            config.create_procedures = ops_config.get('create_procedures', config.create_procedures)

        if 'tables' in config_dict:
            tables_config = config_dict['tables']
            config.selected_tables = tables_config.get('selected_tables', config.selected_tables)
            config.exclude_tables = tables_config.get('exclude_tables', config.exclude_tables)

        if 'csv_files' in config_dict:
            csv_config = config_dict['csv_files']
            config.csv_files_base_path = csv_config.get('base_path', config.csv_files_base_path)
            config.csv_file_mappings.update(csv_config.get('mappings', {}))

        if 'logging' in config_dict:
            log_config = config_dict['logging']
            config.log_level = log_config.get('level', config.log_level)
            config.log_file = log_config.get('file', config.log_file)
            config.log_format = log_config.get('format', config.log_format)

        if 'performance' in config_dict:
            perf_config = config_dict['performance']
            config.batch_size = perf_config.get('batch_size', config.batch_size)
            config.max_connections = perf_config.get('max_connections', config.max_connections)

        config._config_data = config_dict
        return config


class ConfigurationManager:
    """Manages configuration loading from multiple sources."""

    def __init__(self):
        self.config_paths = [
            'config.json',
            'config.yaml',
            'config.yml',
            'database_config.json',
            'database_config.yaml'
        ]

    def load_from_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from file."""
        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to parse configuration file {config_file}: {e}")

    def load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}

        # Database configuration
        if 'DB_HOST' in os.environ:
            env_config.setdefault('database', {})['host'] = os.environ['DB_HOST']
        if 'DB_PORT' in os.environ:
            env_config.setdefault('database', {})['port'] = int(os.environ['DB_PORT'])
        if 'DB_DATABASE' in os.environ:
            env_config.setdefault('database', {})['database'] = os.environ['DB_DATABASE']
        if 'DB_USERNAME' in os.environ:
            env_config.setdefault('database', {})['username'] = os.environ['DB_USERNAME']
        if 'DB_PASSWORD' in os.environ:
            env_config.setdefault('database', {})['password'] = os.environ['DB_PASSWORD']
        if 'DB_CONNECTION_TIMEOUT' in os.environ:
            env_config.setdefault('database', {})['connection_timeout'] = int(os.environ['DB_CONNECTION_TIMEOUT'])

        # CSV files configuration
        if 'CSV_FILES_PATH' in os.environ:
            env_config.setdefault('csv_files', {})['base_path'] = os.environ['CSV_FILES_PATH']

        # Operation flags
        if 'CREATE_SCHEMA' in os.environ:
            env_config.setdefault('operations', {})['create_schema'] = os.environ['CREATE_SCHEMA'].lower() == 'true'
        if 'INSERT_SAMPLE_DATA' in os.environ:
            env_config.setdefault('operations', {})['insert_sample_data'] = os.environ['INSERT_SAMPLE_DATA'].lower() == 'true'
        if 'DROP_EXISTING' in os.environ:
            env_config.setdefault('operations', {})['drop_existing'] = os.environ['DROP_EXISTING'].lower() == 'true'
        if 'UPDATE_EXISTING' in os.environ:
            env_config.setdefault('operations', {})['update_existing'] = os.environ['UPDATE_EXISTING'].lower() == 'true'

        # Logging configuration
        if 'LOG_LEVEL' in os.environ:
            env_config.setdefault('logging', {})['level'] = os.environ['LOG_LEVEL']
        if 'LOG_FILE' in os.environ:
            env_config.setdefault('logging', {})['file'] = os.environ['LOG_FILE']

        # Performance configuration
        if 'BATCH_SIZE' in os.environ:
            env_config.setdefault('performance', {})['batch_size'] = int(os.environ['BATCH_SIZE'])

        return env_config

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries."""
        merged = {}

        for config in configs:
            if not config:
                continue

            for section, values in config.items():
                if section not in merged:
                    merged[section] = {}

                if isinstance(values, dict):
                    merged[section].update(values)
                else:
                    merged[section] = values

        return merged

    def find_config_file(self) -> Optional[str]:
        """Find the first available configuration file."""
        for config_path in self.config_paths:
            if Path(config_path).exists():
                return config_path
        return None


def load_config(config_file: Optional[str] = None) -> DatabaseConfig:
    """
    Load configuration from multiple sources with precedence order.

    Precedence (highest to lowest):
    1. Command line arguments (handled by caller)
    2. Environment variables
    3. Configuration file
    4. Default values

    Args:
        config_file: Optional path to configuration file

    Returns:
        DatabaseConfig instance
    """
    manager = ConfigurationManager()

    # Start with default configuration
    config = DatabaseConfig()

    # Load from file if available
    file_config = {}
    if config_file:
        try:
            file_config = manager.load_from_file(config_file)
            logger.info(f"Loaded configuration from file: {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    else:
        # Try to find a config file automatically
        found_config = manager.find_config_file()
        if found_config:
            try:
                file_config = manager.load_from_file(found_config)
                logger.info(f"Loaded configuration from file: {found_config}")
            except Exception as e:
                logger.warning(f"Failed to load config file {found_config}: {e}")

    # Load from environment variables
    env_config = manager.load_from_env()
    if env_config:
        logger.info("Loaded configuration from environment variables")

    # Merge configurations
    merged_config = manager.merge_configs(file_config, env_config)

    # Create final configuration
    if merged_config:
        config = DatabaseConfig.from_dict(merged_config)

    logger.debug(f"Final configuration loaded with CSV base path: {config.csv_files_base_path}")
    return config


def setup_logging(config: Optional[DatabaseConfig] = None) -> None:
    """
    Setup logging configuration.

    Args:
        config: Optional DatabaseConfig instance
    """
    if config is None:
        config = DatabaseConfig()

    # Configure logging level
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Configure handlers
    handlers = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(config.log_format)
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    # File handler (if specified)
    if config.log_file:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config.log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(config.log_format)
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        except Exception as e:
            print(f"Warning: Failed to setup file logging: {e}")

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override existing configuration
    )

    # Set specific logger levels
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    logging.getLogger('pymysql').setLevel(logging.WARNING)

    logger.info(f"Logging configured: level={config.log_level}, file={config.log_file}")


def create_sample_config_file(config_file: str = 'config.json') -> bool:
    """
    Create a sample configuration file.

    Args:
        config_file: Path to configuration file to create

    Returns:
        True if file created successfully
    """
    try:
        sample_config = {
            "database": {
                "host": "localhost",
                "port": 3306,
                "database": "student_database",
                "username": "your_username",
                "password": "your_password",
                "connection_timeout": 30,
                "pool_size": 5,
                "retry_attempts": 3
            },
            "operations": {
                "create_schema": True,
                "insert_sample_data": False,
                "drop_existing": False,
                "update_existing": False,
                "create_views": True,
                "create_procedures": True
            },
            "tables": {
                "selected_tables": None,
                "exclude_tables": None
            },
            "csv_files": {
                "base_path": "csv_files",
                "mappings": {
                    "Students": "students.csv",
                    "Teachers": "teachers.csv",
                    "Courses": "courses.csv",
                    "Levels": "levels.csv",
                    "EvaluationGroups": "evaluation_groups.csv",
                    "EvaluationComponents": "evaluation_components.csv",
                    "StudentScores": "student_scores.csv",
                    "Enrollments": "enrollments.csv",
                    "Attendance": "attendance.csv",
                    "Grades": "grades.csv"
                }
            },
            "logging": {
                "level": "INFO",
                "file": "mysql_database.log",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "performance": {
                "batch_size": 100,
                "max_connections": 10
            }
        }

        config_path = Path(config_file)

        # Don't overwrite existing file
        if config_path.exists():
            logger.warning(f"Configuration file already exists: {config_file}")
            return False

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2)

        logger.info(f"Sample configuration file created: {config_file}")
        print(f"Sample configuration file created: {config_file}")
        print("Please edit the file with your actual database credentials and settings.")

        return True

    except Exception as e:
        logger.error(f"Failed to create sample config file: {e}")
        print(f"Failed to create sample config file: {e}")
        return False


def validate_config(config: DatabaseConfig) -> Dict[str, Any]:
    """
    Validate configuration settings.

    Args:
        config: DatabaseConfig instance to validate

    Returns:
        Dictionary with validation results
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # Validate database settings
    if not config.host:
        results['errors'].append("Database host is required")
        results['valid'] = False

    if not (1 <= config.port <= 65535):
        results['errors'].append(f"Invalid database port: {config.port}")
        results['valid'] = False

    if not config.database:
        results['errors'].append("Database name is required")
        results['valid'] = False

    if not config.username:
        results['errors'].append("Database username is required")
        results['valid'] = False

    # Validate CSV configuration
    csv_validation = config.validate_csv_configuration()
    if not csv_validation['valid']:
        results['errors'].extend(csv_validation['errors'])
        results['valid'] = False

    results['warnings'].extend(csv_validation['warnings'])

    # Validate logging settings
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.log_level.upper() not in valid_log_levels:
        results['warnings'].append(f"Invalid log level: {config.log_level}")

    # Validate performance settings
    if config.batch_size <= 0:
        results['errors'].append(f"Invalid batch size: {config.batch_size}")
        results['valid'] = False

    if config.pool_size <= 0:
        results['errors'].append(f"Invalid pool size: {config.pool_size}")
        results['valid'] = False

    return results


# Default configuration paths for CSV files
DEFAULT_CSV_MAPPINGS = {
    'Students': 'students.csv',
    'Teachers': 'teachers.csv',
    'Courses': 'courses.csv',
    'Levels': 'levels.csv',
    'EvaluationGroups': 'evaluation_groups.csv',
    'EvaluationComponents': 'evaluation_components.csv',
    'StudentScores': 'student_scores.csv',
    'Enrollments': 'enrollments.csv',
    'Attendance': 'attendance.csv',
    'Grades': 'grades.csv'
}

# CSV file validation schemas (for future use)
CSV_SCHEMAS = {
    'Students': {
        'required_columns': ['FirstName', 'LastName', 'Email', 'DateOfBirth', 'PhoneNumber', 'Address', 'EnrollmentDate', 'Status'],
        'optional_columns': ['StudentID', 'MiddleName', 'EmergencyContact']
    },
    'Teachers': {
        'required_columns': ['FirstName', 'LastName', 'Email', 'PhoneNumber', 'Department', 'HireDate', 'Status'],
        'optional_columns': ['TeacherID', 'MiddleName', 'Salary', 'Office']
    },
    'Courses': {
        'required_columns': ['CourseLevel', 'CourseGroup', 'TeacherID', 'CourseName', 'CourseCode', 'Credits', 'Semester', 'AcademicYear', 'MaxStudents'],
        'optional_columns': ['CourseID', 'Description', 'Status', 'Prerequisites']
    }
}