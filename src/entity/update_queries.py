"""
SQL queries for updating data in the student database.

This module contains all SQL DML (Data Manipulation Language) statements
for updating existing records in the MySQL database tables.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Common update query templates
UPDATE_QUERY_TEMPLATES: Dict[str, str] = {
    'student_info': """
        UPDATE Students 
        SET FirstName = %s, LastName = %s, Email = %s, PhoneNumber = %s, 
            Address = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE StudentID = %s
    """,

    'student_status': """
        UPDATE Students 
        SET Status = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE StudentID = %s
    """,

    'teacher_info': """
        UPDATE Teachers 
        SET FirstName = %s, LastName = %s, Email = %s, PhoneNumber = %s, 
            Department = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE TeacherID = %s
    """,

    'teacher_status': """
        UPDATE Teachers 
        SET Status = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE TeacherID = %s
    """,

    'course_info': """
        UPDATE Courses 
        SET CourseName = %s, Description = %s, Credits = %s, MaxStudents = %s,
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE CourseID = %s
    """,

    'course_teacher': """
        UPDATE Courses 
        SET TeacherID = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE CourseID = %s
    """,

    'course_status': """
        UPDATE Courses 
        SET Status = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE CourseID = %s
    """,

    'evaluation_score': """
        UPDATE Evaluations 
        SET Score = %s, DateCompleted = %s, Status = 'Graded', 
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE EvaluationID = %s
    """,

    'evaluation_feedback': """
        UPDATE Evaluations 
        SET Notes = %s, Feedback = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE EvaluationID = %s
    """,

    'grade_final': """
        UPDATE Grades 
        SET FinalGrade = %s, LetterGrade = %s, GradePoints = %s, 
            Status = 'Final', UpdatedAt = CURRENT_TIMESTAMP
        WHERE GradeID = %s
    """,

    'tutorial_status': """
        UPDATE Tutorials 
        SET Status = %s, Notes = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE TutorialID = %s
    """,

    'ban_resolution': """
        UPDATE Bans 
        SET Resolution = %s, ResolutionDate = %s, EndDate = %s,
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE BanID = %s
    """,

    'ban_appeal': """
        UPDATE Bans 
        SET AppealStatus = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE BanID = %s
    """
}

# Batch update operations
BATCH_UPDATE_QUERIES: Dict[str, str] = {
    'activate_students': """
        UPDATE Students 
        SET Status = 'Active', UpdatedAt = CURRENT_TIMESTAMP
        WHERE StudentID IN (%s)
    """,

    'graduate_students': """
        UPDATE Students 
        SET Status = 'Graduated', UpdatedAt = CURRENT_TIMESTAMP
        WHERE StudentID IN (%s)
    """,

    'suspend_students': """
        UPDATE Students 
        SET Status = 'Suspended', UpdatedAt = CURRENT_TIMESTAMP
        WHERE StudentID IN (%s)
    """,

    'finalize_grades': """
        UPDATE Grades 
        SET Status = 'Final', UpdatedAt = CURRENT_TIMESTAMP
        WHERE Semester = %s AND AcademicYear = %s AND Status = 'Provisional'
    """,

    'close_semester_courses': """
        UPDATE Courses 
        SET Status = 'Inactive', UpdatedAt = CURRENT_TIMESTAMP
        WHERE Semester = %s AND AcademicYear = %s AND Status = 'Active'
    """,

    'expire_old_bans': """
        UPDATE Bans 
        SET UpdatedAt = CURRENT_TIMESTAMP
        WHERE EndDate < CURDATE() AND EndDate IS NOT NULL
    """,

    'complete_past_tutorials': """
        UPDATE Tutorials 
        SET Status = 'Completed', UpdatedAt = CURRENT_TIMESTAMP
        WHERE Date < CURDATE() AND Status = 'Scheduled'
    """,

    'update_evaluation_components_weights': """
        UPDATE EvaluationComponents 
        SET Weight = %s, UpdatedAt = CURRENT_TIMESTAMP
        WHERE CourseID = %s AND ComponentLevel = %s
    """
}

# Complex update operations with subqueries
COMPLEX_UPDATE_QUERIES: Dict[str, str] = {
    'calculate_final_grades': """
        UPDATE Grades g
        JOIN (
            SELECT 
                e.StudentID,
                e.CourseID,
                ROUND(
                    SUM(e.Score * ec.Weight / ec.MaxScore * 100) / 
                    SUM(ec.Weight), 2
                ) AS calculated_grade
            FROM Evaluations e
            JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
            WHERE e.Status = 'Graded' AND ec.IsLeaf = TRUE
            GROUP BY e.StudentID, e.CourseID
        ) calc ON g.StudentID = calc.StudentID AND g.CourseID = calc.CourseID
        SET g.FinalGrade = calc.calculated_grade,
            g.LetterGrade = CASE 
                WHEN calc.calculated_grade >= 97 THEN 'A+'
                WHEN calc.calculated_grade >= 93 THEN 'A'
                WHEN calc.calculated_grade >= 90 THEN 'A-'
                WHEN calc.calculated_grade >= 87 THEN 'B+'
                WHEN calc.calculated_grade >= 83 THEN 'B'
                WHEN calc.calculated_grade >= 80 THEN 'B-'
                WHEN calc.calculated_grade >= 77 THEN 'C+'
                WHEN calc.calculated_grade >= 73 THEN 'C'
                WHEN calc.calculated_grade >= 70 THEN 'C-'
                WHEN calc.calculated_grade >= 67 THEN 'D+'
                WHEN calc.calculated_grade >= 65 THEN 'D'
                ELSE 'F'
            END,
            g.GradePoints = CASE 
                WHEN calc.calculated_grade >= 97 THEN 4.00
                WHEN calc.calculated_grade >= 93 THEN 4.00
                WHEN calc.calculated_grade >= 90 THEN 3.67
                WHEN calc.calculated_grade >= 87 THEN 3.33
                WHEN calc.calculated_grade >= 83 THEN 3.00
                WHEN calc.calculated_grade >= 80 THEN 2.67
                WHEN calc.calculated_grade >= 77 THEN 2.33
                WHEN calc.calculated_grade >= 73 THEN 2.00
                WHEN calc.calculated_grade >= 70 THEN 1.67
                WHEN calc.calculated_grade >= 67 THEN 1.33
                WHEN calc.calculated_grade >= 65 THEN 1.00
                ELSE 0.00
            END,
            g.UpdatedAt = CURRENT_TIMESTAMP
        WHERE g.Semester = %s AND g.AcademicYear = %s
    """,

    'update_component_paths': """
        UPDATE EvaluationComponents ec1
        SET ComponentPath = (
            SELECT GROUP_CONCAT(ComponentName ORDER BY level SEPARATOR ' > ')
            FROM (
                WITH RECURSIVE component_hierarchy AS (
                    SELECT ComponentID, ComponentName, ComponentID as RootID, 
                           ComponentName as ComponentPath, 0 as Level
                    FROM EvaluationComponents 
                    WHERE ParentComponentID IS NULL
                    UNION ALL
                    SELECT ec.ComponentID, ec.ComponentName, ch.RootID,
                           CONCAT(ch.ComponentPath, ' > ', ec.ComponentName), ch.Level + 1
                    FROM EvaluationComponents ec
                    JOIN component_hierarchy ch ON ec.ParentComponentID = ch.ComponentID
                )
                SELECT ComponentName, Level 
                FROM component_hierarchy 
                WHERE ComponentID = ec1.ComponentID
                ORDER BY Level
            ) path_components
        ),
        UpdatedAt = CURRENT_TIMESTAMP
        WHERE CourseID = %s
    """,

    'update_student_gpa': """
        UPDATE Students s
        SET UpdatedAt = CURRENT_TIMESTAMP
        WHERE s.StudentID IN (
            SELECT DISTINCT g.StudentID
            FROM Grades g
            WHERE g.Status = 'Final'
            AND g.AcademicYear = %s
        )
    """,

    'archive_old_evaluations': """
        UPDATE Evaluations 
        SET Status = 'Archived', UpdatedAt = CURRENT_TIMESTAMP
        WHERE DateAssigned < DATE_SUB(CURDATE(), INTERVAL %s MONTH)
        AND Status IN ('Graded', 'Submitted')
    """,

    'reactivate_students_after_probation': """
        UPDATE Students s
        SET Status = 'Active', UpdatedAt = CURRENT_TIMESTAMP
        WHERE s.StudentID IN (
            SELECT DISTINCT b.StudentID
            FROM Bans b
            WHERE b.BanType = 'Academic Probation'
            AND b.EndDate <= CURDATE()
            AND b.IsActive = FALSE
        )
        AND s.Status = 'Suspended'
    """
}

# Data correction and maintenance queries
MAINTENANCE_QUERIES: Dict[str, str] = {
    'fix_evaluation_percentages': """
        UPDATE Evaluations 
        SET UpdatedAt = CURRENT_TIMESTAMP
        WHERE MaxScore > 0
    """,

    'normalize_phone_numbers': """
        UPDATE Students 
        SET PhoneNumber = CONCAT('+1-', 
            REGEXP_REPLACE(
                REGEXP_REPLACE(PhoneNumber, '[^0-9]', ''), 
                '^1?([0-9]{3})([0-9]{3})([0-9]{4}), 
                '\\1-\\2-\\3'
            )
        ),
        UpdatedAt = CURRENT_TIMESTAMP
        WHERE PhoneNumber IS NOT NULL 
        AND PhoneNumber NOT LIKE '+1-%'
    """,

    'update_tutorial_durations': """
        UPDATE Tutorials 
        SET UpdatedAt = CURRENT_TIMESTAMP
        WHERE StartTime IS NOT NULL AND EndTime IS NOT NULL
    """,

    'clean_component_codes': """
        UPDATE EvaluationComponents 
        SET ComponentCode = UPPER(TRIM(ComponentCode)),
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE ComponentCode IS NOT NULL
    """,

    'standardize_email_domains': """
        UPDATE Students 
        SET Email = LOWER(Email),
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE Email IS NOT NULL
    """,

    'update_course_years': """
        UPDATE Courses 
        SET AcademicYear = %s,
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE AcademicYear IS NULL OR AcademicYear = ''
    """
}

# Conditional update queries
CONDITIONAL_UPDATE_QUERIES: Dict[str, str] = {
    'update_late_evaluations': """
        UPDATE Evaluations 
        SET Status = 'Late',
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE DateCompleted > (
            SELECT DueDate 
            FROM EvaluationComponents ec 
            WHERE ec.ComponentID = Evaluations.EvaluationComponentID
            AND ec.DueDate IS NOT NULL
        )
        AND Status = 'Submitted'
    """,

    'promote_provisional_grades': """
        UPDATE Grades 
        SET Status = 'Final',
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE Status = 'Provisional'
        AND DateAssigned <= DATE_SUB(CURDATE(), INTERVAL %s DAY)
    """,

    'deactivate_inactive_teachers': """
        UPDATE Teachers 
        SET Status = 'Inactive',
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE TeacherID NOT IN (
            SELECT DISTINCT TeacherID 
            FROM Courses 
            WHERE Status = 'Active' 
            AND AcademicYear >= %s
        )
        AND Status = 'Active'
    """,

    'update_overdue_tutorials': """
        UPDATE Tutorials 
        SET Status = 'No Show',
            Notes = CONCAT(COALESCE(Notes, ''), ' - Marked as no show due to overdue date'),
            UpdatedAt = CURRENT_TIMESTAMP
        WHERE Date < CURDATE()
        AND Status = 'Scheduled'
    """
}


def get_update_query(query_name: str) -> str:
    """
    Get an update query by name.

    Args:
        query_name: Name of the query template

    Returns:
        SQL UPDATE query template

    Raises:
        KeyError: If query name is not found
    """
    all_queries = {
        **UPDATE_QUERY_TEMPLATES,
        **BATCH_UPDATE_QUERIES,
        **COMPLEX_UPDATE_QUERIES,
        **MAINTENANCE_QUERIES,
        **CONDITIONAL_UPDATE_QUERIES
    }

    if query_name not in all_queries:
        raise KeyError(f"No update query found for: {query_name}")

    return all_queries[query_name]


def get_student_update_queries() -> Dict[str, str]:
    """Get all student-related update queries."""
    return {k: v for k, v in UPDATE_QUERY_TEMPLATES.items() if k.startswith('student_')}


def get_teacher_update_queries() -> Dict[str, str]:
    """Get all teacher-related update queries."""
    return {k: v for k, v in UPDATE_QUERY_TEMPLATES.items() if k.startswith('teacher_')}


def get_course_update_queries() -> Dict[str, str]:
    """Get all course-related update queries."""
    return {k: v for k, v in UPDATE_QUERY_TEMPLATES.items() if k.startswith('course_')}


def get_maintenance_queries() -> Dict[str, str]:
    """Get all maintenance and data correction queries."""
    return MAINTENANCE_QUERIES


def create_bulk_update_query(table: str, updates: Dict[str, Any], where_clause: str) -> str:
    """
    Create a dynamic bulk update query.

    Args:
        table: Table name to update
        updates: Dictionary of column names and values
        where_clause: WHERE clause for the update

    Returns:
        Formatted SQL UPDATE query
    """
    if not updates:
        raise ValueError("Updates dictionary cannot be empty")

    set_clauses = []
    for column, value in updates.items():
        if isinstance(value, str):
            set_clauses.append(f"{column} = '{value}'")
        elif value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = {value}")

    set_clauses.append("UpdatedAt = CURRENT_TIMESTAMP")

    query = f"""
        UPDATE {table} 
        SET {', '.join(set_clauses)}
        WHERE {where_clause}
    """

    return query


def create_conditional_update(table: str, updates: Dict[str, Any],
                              conditions: Dict[str, Any]) -> str:
    """
    Create a conditional update query with multiple conditions.

    Args:
        table: Table name to update
        updates: Dictionary of column names and values to update
        conditions: Dictionary of column names and values for WHERE clause

    Returns:
        Formatted SQL UPDATE query
    """
    if not updates or not conditions:
        raise ValueError("Both updates and conditions must be provided")

    # Build SET clause
    set_clauses = []
    for column, value in updates.items():
        if isinstance(value, str):
            set_clauses.append(f"{column} = '{value}'")
        elif value is None:
            set_clauses.append(f"{column} = NULL")
        else:
            set_clauses.append(f"{column} = {value}")

    set_clauses.append("UpdatedAt = CURRENT_TIMESTAMP")

    # Build WHERE clause
    where_clauses = []
    for column, value in conditions.items():
        if isinstance(value, str):
            where_clauses.append(f"{column} = '{value}'")
        elif value is None:
            where_clauses.append(f"{column} IS NULL")
        elif isinstance(value, (list, tuple)):
            value_list = "', '".join(str(v) for v in value)
            where_clauses.append(f"{column} IN ('{value_list}')")
        else:
            where_clauses.append(f"{column} = {value}")

    query = f"""
        UPDATE {table} 
        SET {', '.join(set_clauses)}
        WHERE {' AND '.join(where_clauses)}
    """

    return query


def get_grade_calculation_query(semester: str, academic_year: str) -> str:
    """
    Get the complex grade calculation query for a specific semester.

    Args:
        semester: Semester name (Fall, Spring, Summer)
        academic_year: Academic year (e.g., '2023', '2024')

    Returns:
        SQL query for calculating final grades
    """
    return COMPLEX_UPDATE_QUERIES['calculate_final_grades']


def validate_update_parameters(query_name: str, parameters: List[Any]) -> bool:
    """
    Validate parameters for a specific update query.

    Args:
        query_name: Name of the update query
        parameters: List of parameters to validate

    Returns:
        True if parameters are valid, False otherwise
    """
    query = get_update_query(query_name)
    expected_params = query.count('%s')

    if len(parameters) != expected_params:
        logger.error(f"Query {query_name} expects {expected_params} parameters, "
                     f"got {len(parameters)}")
        return False

    return True


def get_update_history_query(table: str, record_id: int, id_column: str = None) -> str:
    """
    Create a query to track update history for a record.

    Args:
        table: Table name
        record_id: ID of the record
        id_column: Name of the ID column (defaults to {table}ID)

    Returns:
        SQL query to get update history
    """
    if id_column is None:
        id_column = f"{table}ID"

    return f"""
        SELECT 
            {id_column},
            UpdatedAt,
            CreatedAt,
            TIMESTAMPDIFF(MINUTE, CreatedAt, UpdatedAt) as MinutesSinceCreation,
            CASE 
                WHEN UpdatedAt > CreatedAt THEN 'Modified'
                ELSE 'Original'
            END as RecordStatus
        FROM {table}
        WHERE {id_column} = {record_id}
    """


# Sample update operations data
SAMPLE_UPDATE_OPERATIONS: Dict[str, List[Dict[str, Any]]] = {
    'student_status_updates': [
        {'student_id': 7, 'status': 'Active', 'reason': 'Probation period completed'},
        {'student_id': 3, 'status': 'Suspended', 'reason': 'Academic misconduct investigation'}
    ],

    'grade_updates': [
        {'grade_id': 1, 'final_grade': 87.5, 'letter_grade': 'B+', 'grade_points': 3.33},
        {'grade_id': 2, 'final_grade': 94.2, 'letter_grade': 'A', 'grade_points': 4.00}
    ],

    'course_capacity_updates': [
        {'course_id': 1, 'max_students': 35, 'reason': 'Increased demand'},
        {'course_id': 5, 'max_students': 25, 'reason': 'Lab capacity limitations'}
    ],

    'tutorial_completions': [
        {'tutorial_id': 8, 'status': 'Completed', 'notes': 'Student showed significant improvement'},
        {'tutorial_id': 13, 'status': 'Cancelled', 'notes': 'Student scheduling conflict'}
    ]
}