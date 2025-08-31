"""
student_db_manager.py
=====================
Main database manager module for the student management system.
Provides high-level interface for database operations and query execution.

Author: Assistant
Date: 2024
"""

import sqlite3
import pandas as pd
import logging
from typing import Optional, Dict, List, Any, Union, Tuple
from datetime import datetime, date
import json
import warnings

# Import from other modules (adjust import paths as needed for your project structure)
try:
    from connection import DBConnection
    from entities.queries import QueryLibrary, Query
    from config import get_config, init_config
except ImportError as e:
    print(f"Warning: Could not import required modules: {e}")
    print("Make sure all module files are in the correct location.")
    # For standalone testing, define minimal imports
    pass

# Configure module logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes SQL queries and returns results as pandas DataFrames.
    Provides methods for DDL, DML, and analysis queries.
    """

    def __init__(self, db_connection: DBConnection):
        """
        Initialize query executor.

        Args:
            db_connection: DBConnection instance
        """
        self.db_connection = db_connection
        self.query_library = QueryLibrary()
        logger.info("QueryExecutor initialized")

    def execute_query(self, query: Union[str, Query], params: Optional[Tuple] = None) -> Any:
        """
        Execute a query (DDL, DML, or SELECT).

        Args:
            query: SQL query string or Query object
            params: Optional parameters for prepared statements

        Returns:
            DataFrame for SELECT queries, True/False for others
        """
        sql = query.sql if isinstance(query, Query) else query

        # Determine query type
        sql_upper = sql.strip().upper()

        if sql_upper.startswith('SELECT'):
            return self.execute_select(sql, params)
        elif sql_upper.startswith(('INSERT', 'UPDATE', 'DELETE')):
            return self.execute_dml(sql, params)
        else:
            return self.execute_ddl(sql)

    def execute_ddl(self, query: str) -> bool:
        """
        Execute DDL (Data Definition Language) queries.

        Args:
            query: SQL DDL query string

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_connection.transaction() as conn:
                conn.executescript(query)
                logger.info("DDL query executed successfully")
                return True
        except sqlite3.Error as e:
            logger.error(f"DDL execution failed: {e}")
            return False

    def execute_dml(self, query: str, params: Optional[Tuple] = None) -> bool:
        """
        Execute DML (Data Manipulation Language) queries.

        Args:
            query: SQL DML query string
            params: Query parameters for prepared statements

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_connection.transaction() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                affected_rows = cursor.rowcount
                logger.info(f"DML query executed successfully, {affected_rows} rows affected")
                return True
        except sqlite3.Error as e:
            logger.error(f"DML execution failed: {e}")
            return False

    def execute_select(self, query: str, params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        Execute SELECT queries and return results as DataFrame.

        Args:
            query: SQL SELECT query string
            params: Query parameters for prepared statements

        Returns:
            pandas DataFrame with query results
        """
        try:
            with self.db_connection.get_connection() as conn:
                if params:
                    df = pd.read_sql_query(query, conn, params=params)
                else:
                    df = pd.read_sql_query(query, conn)
                logger.info(f"SELECT query executed, returned {len(df)} rows")
                return df
        except Exception as e:
            logger.error(f"SELECT execution failed: {e}")
            return pd.DataFrame()

    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Execute multiple DML statements with different parameters.

        Args:
            query: SQL query with placeholders
            params_list: List of parameter tuples

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_connection.transaction() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                logger.info(f"Batch execution successful, {cursor.rowcount} rows affected")
                return True
        except sqlite3.Error as e:
            logger.error(f"Batch execution failed: {e}")
            return False

    def run_named_query(self, query_name: str, params: Optional[Tuple] = None) -> Union[pd.DataFrame, bool]:
        """
        Run a predefined query from the QueryLibrary by name.

        Args:
            query_name: Name of the query in QueryLibrary
            params: Optional parameters for the query

        Returns:
            Query results (DataFrame or bool)
        """
        query = QueryLibrary.get_query(query_name)
        if not query:
            logger.error(f"Query '{query_name}' not found in library")
            return pd.DataFrame() if query_name.startswith('select') else False

        return self.execute_query(query, params)


class StudentDatabaseManager:
    """
    High-level manager for the student database system.
    Provides a simplified interface for common operations.
    """

    def __init__(self, db_path: Optional[str] = None, use_config: bool = True):
        """
        Initialize the database manager.

        Args:
            db_path: Path to SQLite database file (overrides config if provided)
            use_config: Whether to use configuration from config module
        """
        self.db_path = db_path
        self.use_config = use_config

        # Initialize connection with config support
        self.db_connection = DBConnection(db_path=db_path, use_config=use_config)
        self.query_executor = QueryExecutor(self.db_connection)

        # Store actual path from connection
        self.db_path = self.db_connection.db_path
        logger.info(f"StudentDatabaseManager initialized with database: {self.db_path}")

    def initialize_database(self, with_sample_data: bool = True) -> bool:
        """
        Initialize database with schema and optionally sample data.

        Args:
            with_sample_data: Whether to insert sample data

        Returns:
            True if successful
        """
        logger.info("Initializing database...")

        # Create schema
        if not self.create_schema():
            return False

        # Insert sample data if requested
        if with_sample_data:
            if not self.insert_sample_data():
                return False

        logger.info("Database initialized successfully")
        return True

    def create_schema(self) -> bool:
        """
        Create all database tables and indices.

        Returns:
            True if all tables created successfully
        """
        logger.info("Creating database schema...")

        schema_queries = QueryLibrary.get_queries_by_category('SCHEMA')

        # Order matters for foreign key constraints
        table_order = [
            'create_students', 'create_teachers', 'create_courses',
            'create_evaluation_components', 'create_evaluations',
            'create_grades', 'create_tutorials', 'create_bans', 'create_indices'
        ]

        for table_name in table_order:
            query = schema_queries.get(table_name)
            if query and not self.query_executor.execute_ddl(query.sql):
                logger.error(f"Failed to create: {table_name}")
                return False

        logger.info("Database schema created successfully")
        return True

    def insert_sample_data(self) -> bool:
        """
        Insert comprehensive sample data for testing.

        Returns:
            True if all data inserted successfully
        """
        logger.info("Inserting sample data...")

        try:
            # Students
            students_data = [
                ('John', 'Doe', 'john.doe@email.com', '2000-05-15'),
                ('Jane', 'Smith', 'jane.smith@email.com', '2001-03-22'),
                ('Bob', 'Johnson', 'bob.johnson@email.com', '2000-11-08'),
                ('Alice', 'Williams', 'alice.williams@email.com', '2001-07-10'),
                ('Charlie', 'Brown', 'charlie.brown@email.com', '2000-12-25')
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_student').sql,
                students_data
            )

            # Teachers
            teachers_data = [
                ('Dr. Sarah', 'Williams', 'sarah.williams@school.edu'),
                ('Prof. Michael', 'Brown', 'michael.brown@school.edu'),
                ('Dr. Emily', 'Davis', 'emily.davis@school.edu')
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_teacher').sql,
                teachers_data
            )

            # Courses
            courses_data = [
                ('Introduction to Programming', 'CS101', 1),
                ('Database Systems', 'CS201', 2),
                ('Web Development', 'CS301', 1),
                ('Data Structures', 'CS202', 3),
                ('Machine Learning', 'CS401', 2)
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_course').sql,
                courses_data
            )

            # Insert hierarchical evaluation components for CS101
            with self.db_connection.transaction() as conn:
                cursor = conn.cursor()

                # Level 1: Block
                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, None, 'block', 'Analysis', 0, 1)
                )
                block_id = cursor.lastrowid

                # Level 2: Criteria
                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, block_id, 'criteria', 'Coordination', 0, 1)
                )
                criteria_id = cursor.lastrowid

                # Level 3: Observations
                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, criteria_id, 'observation', 'Practical Exam', 0, 1)
                )
                obs1_id = cursor.lastrowid

                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, criteria_id, 'observation', 'Theoretical Exam', 1, 2)
                )
                obs2_id = cursor.lastrowid

                # Level 4: Lab components
                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, obs1_id, 'lab', 'Practice1', 1, 1)
                )
                lab1_id = cursor.lastrowid

                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (1, obs1_id, 'lab', 'Measuring Temperature', 1, 2)
                )
                lab2_id = cursor.lastrowid

                # Add components for CS201
                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (2, None, 'module', 'SQL Module', 0, 1)
                )
                module_id = cursor.lastrowid

                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (2, module_id, 'assignment', 'SQL Assignment 1', 1, 1)
                )
                assignment1_id = cursor.lastrowid

                cursor.execute(
                    QueryLibrary.get_query('insert_evaluation_component').sql,
                    (2, module_id, 'assignment', 'SQL Assignment 2', 1, 2)
                )
                assignment2_id = cursor.lastrowid

                # Insert Evaluations
                evaluations_data = [
                    (1, 1, lab1_id, 85.50, 100, 1.0, '2024-10-15', '2024-10-15', 'Good work'),
                    (1, 1, lab2_id, 92.00, 100, 1.0, '2024-10-16', '2024-10-16', 'Excellent'),
                    (1, 1, obs2_id, 88.00, 100, 2.0, '2024-10-20', '2024-10-20', None),
                    (1, 2, lab1_id, 78.00, 100, 1.0, '2024-10-15', '2024-10-15', None),
                    (1, 2, lab2_id, 81.50, 100, 1.0, '2024-10-16', '2024-10-16', 'Good effort'),
                    (1, 3, obs2_id, 95.00, 100, 2.0, '2024-10-20', '2024-10-20', 'Outstanding'),
                    (2, 1, assignment1_id, 90.00, 100, 1.0, '2024-09-10', '2024-09-10', None),
                    (2, 1, assignment2_id, 87.50, 100, 1.0, '2024-09-20', '2024-09-20', None),
                    (2, 2, assignment1_id, 76.00, 100, 1.0, '2024-09-10', '2024-09-11', 'Late submission'),
                ]
                cursor.executemany(
                    QueryLibrary.get_query('insert_evaluation').sql,
                    evaluations_data
                )

            # Grades
            grades_data = [
                (1, 1, 88.75, '2024-12-20'),
                (2, 1, 82.50, '2024-12-20'),
                (3, 1, 95.00, '2024-12-20'),
                (1, 2, 88.75, '2024-12-20'),
                (2, 2, 76.00, '2024-12-20')
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_grade').sql,
                grades_data
            )

            # Tutorials
            tutorials_data = [
                (1, '2024-09-25', 'SQL Joins', 'Reviewed different types of joins'),
                (2, '2024-09-26', 'Debugging', 'Helped with debugging assignment 3'),
                (1, '2024-10-01', 'Database Design', 'Discussed normalization'),
                (3, '2024-10-05', 'Python Basics', 'Introduction to Python syntax')
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_tutorial').sql,
                tutorials_data
            )

            # Bans
            bans_data = [
                (3, 'Library', '2024-10-01', '2024-10-15', 'Excessive noise violations'),
                (4, 'Computer Lab', '2024-11-01', None, 'Misuse of equipment')
            ]
            self.query_executor.execute_many(
                QueryLibrary.get_query('insert_ban').sql,
                bans_data
            )

            logger.info("Sample data inserted successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to insert sample data: {e}")
            return False

    # ========== Analysis Methods ==========

    def get_table_summary(self) -> pd.DataFrame:
        """Get summary of all tables with record counts."""
        return self.query_executor.run_named_query('count_all_tables')

    def get_courses_with_teachers(self) -> pd.DataFrame:
        """Get all courses with their assigned teachers."""
        return self.query_executor.run_named_query('courses_with_teachers')

    def get_student_grades(self) -> pd.DataFrame:
        """Get all student grades with course information."""
        return self.query_executor.run_named_query('student_grades_with_courses')

    def get_student_evaluations(self, student_id: Optional[int] = None) -> pd.DataFrame:
        """
        Get detailed evaluation data for students.

        Args:
            student_id: Optional specific student ID

        Returns:
            DataFrame with evaluation data
        """
        if student_id:
            query = """
                SELECT 
                    s.FirstName || ' ' || s.LastName as StudentName,
                    c.CourseName,
                    ec.ComponentName,
                    ec.ComponentLevel,
                    e.Score,
                    e.MaxScore,
                    ROUND((e.Score * 1.0 / e.MaxScore * 100), 2) as Percentage,
                    e.DateAssigned,
                    e.Notes
                FROM Evaluations e
                JOIN Students s ON e.StudentID = s.StudentID
                JOIN Courses c ON e.CourseID = c.CourseID
                JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
                WHERE s.StudentID = ?
                ORDER BY c.CourseName, e.DateAssigned
            """
            return self.query_executor.execute_select(query, (student_id,))
        else:
            return self.query_executor.run_named_query('student_evaluations_detailed')

    def get_evaluation_hierarchy(self, course_id: Optional[int] = None) -> pd.DataFrame:
        """
        Get the evaluation component hierarchy for courses.

        Args:
            course_id: Optional specific course ID

        Returns:
            DataFrame with component hierarchy
        """
        if course_id:
            query = """
                SELECT 
                    ComponentID,
                    ComponentName,
                    ComponentLevel,
                    ParentComponentID,
                    IsLeaf,
                    OrderIndex
                FROM EvaluationComponents
                WHERE CourseID = ?
                ORDER BY OrderIndex
            """
            return self.query_executor.execute_select(query, (course_id,))
        else:
            return self.query_executor.run_named_query('component_hierarchy')

    def get_course_statistics(self) -> pd.DataFrame:
        """Get statistical summary for all courses."""
        return self.query_executor.run_named_query('course_statistics')

    def get_top_performers(self, min_average: float = 80.0) -> pd.DataFrame:
        """
        Get top performing students.

        Args:
            min_average: Minimum average percentage (default 80%)

        Returns:
            DataFrame with top performers
        """
        query = """
            SELECT 
                s.StudentID,
                s.FirstName || ' ' || s.LastName as StudentName,
                s.Email,
                COUNT(DISTINCT e.CourseID) as CoursesEnrolled,
                COUNT(e.EvaluationID) as TotalEvaluations,
                ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as AveragePercentage,
                ROUND(MAX(e.Score * 1.0 / e.MaxScore * 100), 2) as BestPercentage
            FROM Evaluations e
            JOIN Students s ON e.StudentID = s.StudentID
            GROUP BY s.StudentID
            HAVING AveragePercentage >= ?
            ORDER BY AveragePercentage DESC
        """
        return self.query_executor.execute_select(query, (min_average,))

    def get_active_bans(self) -> pd.DataFrame:
        """Get currently active disciplinary bans."""
        return self.query_executor.run_named_query('active_bans')

    def get_tutorials(self, student_id: Optional[int] = None) -> pd.DataFrame:
        """
        Get tutorial sessions.

        Args:
            student_id: Optional specific student ID

        Returns:
            DataFrame with tutorial data
        """
        if student_id:
            query = """
                SELECT 
                    t.Date,
                    t.Topic,
                    t.Notes
                FROM Tutorials t
                WHERE t.StudentID = ?
                ORDER BY t.Date DESC
            """
            return self.query_executor.execute_select(query, (student_id,))
        else:
            return self.query_executor.run_named_query('tutorials_list')

    def get_student_scores_with_hierarchy(self) -> pd.DataFrame:
        """Get student scores with full evaluation hierarchy paths."""
        return self.query_executor.run_named_query('student_scores_with_hierarchy')

    # ========== Data Manipulation Methods ==========

    def add_student(self, first_name: str, last_name: str, email: str,
                    date_of_birth: Optional[str] = None) -> bool:
        """
        Add a new student to the database.

        Args:
            first_name: Student's first name
            last_name: Student's last name
            email: Student's email (must be unique)
            date_of_birth: Optional date of birth (YYYY-MM-DD format)

        Returns:
            True if successful
        """
        return self.query_executor.run_named_query(
            'insert_student',
            (first_name, last_name, email, date_of_birth)
        )

    def add_teacher(self, first_name: str, last_name: str, email: str) -> bool:
        """Add a new teacher to the database."""
        return self.query_executor.run_named_query(
            'insert_teacher',
            (first_name, last_name, email)
        )

    def add_course(self, course_name: str, course_code: str, teacher_id: int) -> bool:
        """Add a new course to the database."""
        return self.query_executor.run_named_query(
            'insert_course',
            (course_name, course_code, teacher_id)
        )

    def record_evaluation(self, course_id: int, student_id: int, component_id: int,
                          score: float, max_score: float = 100, weight: float = 1.0,
                          date_assigned: str = None, notes: str = None) -> bool:
        """
        Record a new evaluation for a student.

        Args:
            course_id: Course ID
            student_id: Student ID
            component_id: Evaluation component ID
            score: Score achieved
            max_score: Maximum possible score
            weight: Weight of this evaluation
            date_assigned: Date assigned (defaults to today)
            notes: Optional notes

        Returns:
            True if successful
        """
        if date_assigned is None:
            date_assigned = datetime.now().strftime('%Y-%m-%d')

        return self.query_executor.run_named_query(
            'insert_evaluation',
            (course_id, student_id, component_id, score, max_score, weight,
             date_assigned, date_assigned, notes)
        )

    def update_final_grade(self, student_id: int, course_id: int,
                           final_grade: float) -> bool:
        """Update or insert a final grade for a student in a course."""
        date_assigned = datetime.now().strftime('%Y-%m-%d')

        # Try to update first
        update_query = """
            UPDATE Grades 
            SET FinalGrade = ?, DateAssigned = ? 
            WHERE StudentID = ? AND CourseID = ?
        """

        with self.db_connection.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(update_query, (final_grade, date_assigned, student_id, course_id))

            if cursor.rowcount == 0:
                # No existing grade, insert new one
                return self.query_executor.run_named_query(
                    'insert_grade',
                    (student_id, course_id, final_grade, date_assigned)
                )

        return True

    # ========== Export Methods ==========

    def export_to_excel(self, output_path: str = 'student_database_report.xlsx') -> bool:
        """
        Export all analysis results to an Excel file with multiple sheets.

        Args:
            output_path: Path for the output Excel file

        Returns:
            True if successful
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Define sheets to export
                sheets = {
                    'Summary': self.get_table_summary(),
                    'Courses': self.get_courses_with_teachers(),
                    'Student Grades': self.get_student_grades(),
                    'Evaluations': self.get_student_evaluations(),
                    'Course Statistics': self.get_course_statistics(),
                    'Top Performers': self.get_top_performers(),
                    'Score Hierarchy': self.get_student_scores_with_hierarchy(),
                    'Tutorials': self.get_tutorials(),
                    'Active Bans': self.get_active_bans()
                }

                for sheet_name, df in sheets.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logger.info(f"Exported {sheet_name}: {len(df)} rows")

                logger.info(f"Results exported to {output_path}")
                return True

        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False

    def export_to_json(self, output_path: str = 'student_database.json') -> bool:
        """
        Export database content to JSON format.

        Args:
            output_path: Path for the output JSON file

        Returns:
            True if successful
        """
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'database': self.db_path,
                'summary': self.get_table_summary().to_dict('records'),
                'courses': self.get_courses_with_teachers().to_dict('records'),
                'student_grades': self.get_student_grades().to_dict('records'),
                'evaluations': self.get_student_evaluations().to_dict('records'),
                'statistics': self.get_course_statistics().to_dict('records'),
                'top_performers': self.get_top_performers().to_dict('records')
            }

            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Data exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return False

    def generate_report(self, student_id: int) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a specific student.

        Args:
            student_id: Student ID

        Returns:
            Dictionary containing student report data
        """
        # Get student info
        student_query = "SELECT * FROM Students WHERE StudentID = ?"
        student_df = self.query_executor.execute_select(student_query, (student_id,))

        if student_df.empty:
            logger.warning(f"Student {student_id} not found")
            return {}

        student_info = student_df.iloc[0].to_dict()

        # Get evaluations
        evaluations = self.get_student_evaluations(student_id)

        # Get grades
        grades_query = """
            SELECT c.CourseCode, c.CourseName, g.FinalGrade, g.DateAssigned
            FROM Grades g
            JOIN Courses c ON g.CourseID = c.CourseID
            WHERE g.StudentID = ?
        """
        grades = self.query_executor.execute_select(grades_query, (student_id,))

        # Get tutorials
        tutorials = self.get_tutorials(student_id)

        # Check for bans
        bans_query = """
            SELECT BanType, StartDate, EndDate, Reason
            FROM Bans
            WHERE StudentID = ?
            ORDER BY StartDate DESC
        """
        bans = self.query_executor.execute_select(bans_query, (student_id,))

        # Calculate statistics
        if not evaluations.empty:
            stats = {
                'average_score': round(evaluations['Percentage'].mean(), 2),
                'highest_score': evaluations['Percentage'].max(),
                'lowest_score': evaluations['Percentage'].min(),
                'total_evaluations': len(evaluations),
                'courses_enrolled': evaluations['CourseName'].nunique()
            }
        else:
            stats = {'message': 'No evaluations found'}

        return {
            'student_info': student_info,
            'statistics': stats,
            'evaluations': evaluations.to_dict('records') if not evaluations.empty else [],
            'grades': grades.to_dict('records') if not grades.empty else [],
            'tutorials': tutorials.to_dict('records') if not tutorials.empty else [],
            'bans': bans.to_dict('records') if not bans.empty else [],
            'report_generated': datetime.now().isoformat()
        }

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.

        Returns:
            Dictionary with database information
        """
        info = {
            'database_path': self.db_path,
            'tables': {}
        }

        # Get table information
        table_info_query = """
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """
        tables_df = self.query_executor.execute_select(table_info_query)

        for _, row in tables_df.iterrows():
            table_name = row['name']
            count_query = f"SELECT COUNT(*) as count FROM {table_name}"
            count_df = self.query_executor.execute_select(count_query)
            count = count_df['count'].iloc[0] if not count_df.empty else 0

            info['tables'][table_name] = {
                'record_count': count,
                'schema': row['sql']
            }

        return info

    def __repr__(self) -> str:
        """String representation of StudentDatabaseManager."""
        return f"StudentDatabaseManager(db_path='{self.db_path}')"


# ========== Utility Functions ==========

def print_dataframe_pretty(df: pd.DataFrame, title: str = "", max_rows: int = 10):
    """
    Pretty print a DataFrame with a title.

    Args:
        df: DataFrame to print
        title: Optional title
        max_rows: Maximum rows to display
    """
    if title:
        print(f"\n{title}")
        print("=" * len(title))

    if df.empty:
        print("No data found.")
    else:
        with pd.option_context('display.max_rows', max_rows,
                               'display.max_columns', None,
                               'display.width', None,
                               'display.max_colwidth', 50):
            print(df.to_string(index=False))

        if len(df) > max_rows:
            print(f"... showing {max_rows} of {len(df)} rows")


def create_sample_environment_files():
    """Create sample configuration files for reference."""

    # Create .env.example
    env_example = """# Database Configuration Example
# Copy this file to .env and update with your values

# Database Type (sqlite, mysql, postgresql)
DB_TYPE=sqlite

# SQLite Configuration
DB_PATH=student_database.db

# MySQL/PostgreSQL Configuration (uncomment if needed)
# DB_HOST=localhost
# DB_PORT=3306
# DB_DATABASE=student_db
# DB_USERNAME=your_username
# DB_PASSWORD=your_password

# Connection Settings
DB_TIMEOUT=30
DB_POOL_SIZE=5
DB_ECHO=false

# Application Environment (development, testing, staging, production)
APP_ENV=development
"""

    with open('.env.example', 'w') as f:
        f.write(env_example)

    # Create config.example.json
    config_example = {
        "database": {
            "type": "sqlite",
            "db_path": "student_database.db",
            "connection_timeout": 30,
            "pool_size": 5,
            "echo": False
        },
        "app": {
            "debug": False,
            "log_level": "INFO"
        }
    }

    with open('config.example.json', 'w') as f:
        json.dump(config_example, f, indent=2)

    print("✓ Created .env.example and config.example.json")


# ========== Demo and Testing Functions ==========

def demo_usage():
    """Demonstrate usage of the StudentDatabaseManager."""
    print("=" * 70)
    print("STUDENT DATABASE MANAGEMENT SYSTEM - DEMONSTRATION")
    print("=" * 70)

    # Initialize manager
    manager = StudentDatabaseManager('demo_student.db')

    # Initialize database with sample data
    print("\n1. Initializing database with sample data...")
    if manager.initialize_database(with_sample_data=True):
        print("   ✓ Database initialized successfully")
    else:
        print("   ✗ Database initialization failed")
        return

    # Display database info
    print("\n2. Database Information:")
    db_info = manager.get_database_info()
    print(f"   Database: {db_info['database_path']}")
    print(f"   Tables: {len(db_info['tables'])}")
    for table, info in db_info['tables'].items():
        print(f"   - {table}: {info['record_count']} records")

    # Display table summary
    print("\n3. Database Table Summary:")
    summary = manager.get_table_summary()
    print_dataframe_pretty(summary, max_rows=20)

    # Show courses with teachers
    print("\n4. Courses with Teachers:")
    courses = manager.get_courses_with_teachers()
    print_dataframe_pretty(courses)

    # Show top performers
    print("\n5. Top Performers (80% or higher):")
    top_performers = manager.get_top_performers(80.0)
    if not top_performers.empty:
        print_dataframe_pretty(top_performers)
    else:
        print("   No top performers found")

    # Show evaluation hierarchy
    print("\n6. Evaluation Hierarchy with Student Scores:")
    hierarchy = manager.get_student_scores_with_hierarchy()
    print_dataframe_pretty(hierarchy, max_rows=5)

    # Course statistics
    print("\n7. Course Statistics:")
    stats = manager.get_course_statistics()
    print_dataframe_pretty(stats)

    # Generate student report
    print("\n8. Individual Student Report (Student ID: 1):")
    report = manager.generate_report(1)
    if report:
        print(f"   Student: {report['student_info']['FirstName']} {report['student_info']['LastName']}")
        print(f"   Email: {report['student_info']['Email']}")
        if report.get('statistics') and 'average_score' in report['statistics']:
            print(f"   Average Score: {report['statistics']['average_score']:.2f}%")
            print(f"   Total Evaluations: {report['statistics']['total_evaluations']}")
            print(f"   Courses Enrolled: {report['statistics']['courses_enrolled']}")

    # Add a new student
    print("\n9. Adding new student...")
    success = manager.add_student(
        'Emma', 'Wilson', 'emma.wilson@email.com', '2001-03-15'
    )
    if success:
        print("   ✓ New student added successfully")

    # Export to Excel
    print("\n10. Exporting results to Excel...")
    if manager.export_to_excel('demo_report.xlsx'):
        print("    ✓ Results exported to 'demo_report.xlsx'")

    # Export to JSON
    print("\n11. Exporting data to JSON...")
    if manager.export_to_json('demo_data.json'):
        print("    ✓ Data exported to 'demo_data.json'")

    print("\n" + "=" * 70)
    print("Demonstration completed successfully!")
    print("Files created: demo_student.db, demo_report.xlsx, demo_data.json")
    print("=" * 70)


def demo_advanced_features():
    """Demonstrate advanced features of the system."""
    print("\n" + "=" * 70)
    print("ADVANCED FEATURES DEMONSTRATION")
    print("=" * 70)

    manager = StudentDatabaseManager('advanced_demo.db')
    manager.initialize_database(with_sample_data=True)

    # Custom query example
    print("\n1. Custom Query - Students needing improvement (<70% average):")
    query = """
        SELECT 
            s.StudentID,
            s.FirstName || ' ' || s.LastName as StudentName,
            COUNT(e.EvaluationID) as TotalEvaluations,
            ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as AveragePercentage
        FROM Evaluations e
        JOIN Students s ON e.StudentID = s.StudentID
        GROUP BY s.StudentID
        HAVING AveragePercentage < 70
        ORDER BY AveragePercentage
    """
    result = manager.query_executor.execute_select(query)
    print_dataframe_pretty(result)

    # Hierarchical component analysis
    print("\n2. Evaluation Component Hierarchy (Course 1):")
    hierarchy = manager.get_evaluation_hierarchy(course_id=1)
    print_dataframe_pretty(hierarchy)

    # Performance by component level
    print("\n3. Average Performance by Component Level:")
    query = """
        SELECT 
            ec.ComponentLevel,
            COUNT(DISTINCT e.StudentID) as StudentsEvaluated,
            COUNT(e.EvaluationID) as TotalEvaluations,
            ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as AveragePercentage
        FROM Evaluations e
        JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
        GROUP BY ec.ComponentLevel
        ORDER BY ec.ComponentLevel
    """
    result = manager.query_executor.execute_select(query)
    print_dataframe_pretty(result)

    # Tutorial effectiveness
    print("\n4. Students with Tutorials vs Performance:")
    query = """
        SELECT 
            CASE 
                WHEN t.StudentID IS NOT NULL THEN 'With Tutorials'
                ELSE 'Without Tutorials'
            END as TutorialStatus,
            COUNT(DISTINCT s.StudentID) as StudentCount,
            ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as AveragePercentage
        FROM Students s
        LEFT JOIN Tutorials t ON s.StudentID = t.StudentID
        LEFT JOIN Evaluations e ON s.StudentID = e.StudentID
        WHERE e.EvaluationID IS NOT NULL
        GROUP BY TutorialStatus
    """
    result = manager.query_executor.execute_select(query)
    print_dataframe_pretty(result)

    print("\n" + "=" * 70)
    print("Advanced demonstration completed!")
    print("=" * 70)


def interactive_demo():
    """Interactive demonstration of the database system."""
    print("\n" + "=" * 70)
    print("INTERACTIVE DATABASE EXPLORER")
    print("=" * 70)

    manager = StudentDatabaseManager('interactive.db')
    manager.initialize_database(with_sample_data=True)

    while True:
        print("\n" + "-" * 50)
        print("Available Operations:")
        print("1. View table summary")
        print("2. View all students")
        print("3. View all courses")
        print("4. View student evaluations")
        print("5. View course statistics")
        print("6. View top performers")
        print("7. Generate student report")
        print("8. Add new student")
        print("9. Record new evaluation")
        print("10. Export to Excel")
        print("11. Export to JSON")
        print("0. Exit")
        print("-" * 50)

        try:
            choice = input("\nEnter your choice (0-11): ").strip()

            if choice == '0':
                print("\nExiting interactive demo...")
                break

            elif choice == '1':
                summary = manager.get_table_summary()
                print_dataframe_pretty(summary, "Table Summary")

            elif choice == '2':
                query = "SELECT * FROM Students ORDER BY LastName, FirstName"
                students = manager.query_executor.execute_select(query)
                print_dataframe_pretty(students, "All Students")

            elif choice == '3':
                courses = manager.get_courses_with_teachers()
                print_dataframe_pretty(courses, "All Courses")

            elif choice == '4':
                evaluations = manager.get_student_evaluations()
                print_dataframe_pretty(evaluations, "Student Evaluations", max_rows=20)

            elif choice == '5':
                stats = manager.get_course_statistics()
                print_dataframe_pretty(stats, "Course Statistics")

            elif choice == '6':
                min_avg = float(input("Enter minimum average (e.g., 80): ") or "80")
                top = manager.get_top_performers(min_avg)
                print_dataframe_pretty(top, f"Top Performers (>={min_avg}%)")

            elif choice == '7':
                student_id = int(input("Enter student ID: "))
                report = manager.generate_report(student_id)
                if report and 'student_info' in report:
                    print(f"\nReport for: {report['student_info']['FirstName']} {report['student_info']['LastName']}")
                    print(json.dumps(report, indent=2, default=str))
                else:
                    print("Student not found.")

            elif choice == '8':
                print("\nAdd New Student:")
                first = input("First name: ")
                last = input("Last name: ")
                email = input("Email: ")
                dob = input("Date of birth (YYYY-MM-DD) or press Enter to skip: ")

                if manager.add_student(first, last, email, dob or None):
                    print("✓ Student added successfully!")
                else:
                    print("✗ Failed to add student (email might be duplicate)")

            elif choice == '9':
                print("\nRecord New Evaluation:")
                course_id = int(input("Course ID: "))
                student_id = int(input("Student ID: "))
                component_id = int(input("Component ID: "))
                score = float(input("Score: "))
                max_score = float(input("Max score (default 100): ") or "100")
                notes = input("Notes (optional): ")

                if manager.record_evaluation(
                        course_id, student_id, component_id,
                        score, max_score, notes=notes or None
                ):
                    print("✓ Evaluation recorded successfully!")
                else:
                    print("✗ Failed to record evaluation")

            elif choice == '10':
                filename = input("Enter filename (default: export.xlsx): ") or "export.xlsx"
                if manager.export_to_excel(filename):
                    print(f"✓ Exported to {filename}")
                else:
                    print("✗ Export failed")

            elif choice == '11':
                filename = input("Enter filename (default: export.json): ") or "export.json"
                if manager.export_to_json(filename):
                    print(f"✓ Exported to {filename}")
                else:
                    print("✗ Export failed")

            else:
                print("Invalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("\n" + "=" * 70)
    print("Thank you for using the Student Database Explorer!")
    print("=" * 70)


if __name__ == "__main__":
    """Main execution block for testing and demonstration."""

    # Suppress warnings for cleaner output
    warnings.filterwarnings('ignore')

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Create sample configuration files
        create_sample_environment_files()

        # Run the main demonstration
        demo_usage()

        # Uncomment to run additional demos:
        # demo_advanced_features()
        # interactive_demo()

    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        print(f"\nDemo failed with error: {e}")
        print("Please check the logs for more details.")