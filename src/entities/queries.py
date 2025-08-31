"""
entities/queries.py
===================
SQL queries library for the student management system.
Contains all DDL, DML, and analysis queries organized by category.

Author: Assistant
Date: 2024
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Query:
    """Represents a SQL query with metadata."""
    name: str
    sql: str
    description: str
    category: str
    params_required: bool = False


class QueryLibrary:
    """
    A library containing all SQL queries for the student management system.
    Queries are organized by category for easy access and maintenance.
    """

    # ========== SCHEMA CREATION QUERIES ==========
    SCHEMA_QUERIES = {
        'create_students': Query(
            name='create_students',
            sql="""
                CREATE TABLE IF NOT EXISTS Students (
                    StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
                    FirstName VARCHAR(100) NOT NULL,
                    LastName VARCHAR(100) NOT NULL,
                    Email VARCHAR(255) NOT NULL UNIQUE,
                    DateOfBirth DATE
                )
            """,
            description="Create Students table",
            category="SCHEMA"
        ),

        'create_teachers': Query(
            name='create_teachers',
            sql="""
                CREATE TABLE IF NOT EXISTS Teachers (
                    TeacherID INTEGER PRIMARY KEY AUTOINCREMENT,
                    FirstName VARCHAR(100) NOT NULL,
                    LastName VARCHAR(100) NOT NULL,
                    Email VARCHAR(255) NOT NULL UNIQUE
                )
            """,
            description="Create Teachers table",
            category="SCHEMA"
        ),

        'create_courses': Query(
            name='create_courses',
            sql="""
                CREATE TABLE IF NOT EXISTS Courses (
                    CourseID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CourseName VARCHAR(255) NOT NULL,
                    CourseCode VARCHAR(50) NOT NULL UNIQUE,
                    TeacherID INTEGER NOT NULL,
                    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
                        ON DELETE RESTRICT
                        ON UPDATE CASCADE
                )
            """,
            description="Create Courses table with teacher relationship",
            category="SCHEMA"
        ),

        'create_evaluation_components': Query(
            name='create_evaluation_components',
            sql="""
                CREATE TABLE IF NOT EXISTS EvaluationComponents (
                    ComponentID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CourseID INTEGER NOT NULL,
                    ParentComponentID INTEGER,
                    ComponentLevel VARCHAR(50) NOT NULL,
                    ComponentName VARCHAR(255) NOT NULL,
                    ComponentCode VARCHAR(50),
                    Description TEXT,
                    IsLeaf BOOLEAN DEFAULT 0,
                    OrderIndex INTEGER DEFAULT 0,
                    ComponentPath VARCHAR(500),
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (ParentComponentID) REFERENCES EvaluationComponents(ComponentID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """,
            description="Create hierarchical evaluation components table",
            category="SCHEMA"
        ),

        'create_evaluations': Query(
            name='create_evaluations',
            sql="""
                CREATE TABLE IF NOT EXISTS Evaluations (
                    EvaluationID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CourseID INTEGER NOT NULL,
                    StudentID INTEGER NOT NULL,
                    EvaluationComponentID INTEGER NOT NULL,
                    Score DECIMAL(5,2),
                    MaxScore DECIMAL(5,2) DEFAULT 100,
                    Weight DECIMAL(5,2) DEFAULT 1.0,
                    DateAssigned DATE NOT NULL,
                    DateCompleted DATE,
                    Notes TEXT,
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (EvaluationComponentID) REFERENCES EvaluationComponents(ComponentID)
                        ON DELETE RESTRICT
                        ON UPDATE CASCADE
                )
            """,
            description="Create Evaluations table for student assessments",
            category="SCHEMA"
        ),

        'create_grades': Query(
            name='create_grades',
            sql="""
                CREATE TABLE IF NOT EXISTS Grades (
                    GradeID INTEGER PRIMARY KEY AUTOINCREMENT,
                    StudentID INTEGER NOT NULL,
                    CourseID INTEGER NOT NULL,
                    FinalGrade DECIMAL(5,2) NOT NULL,
                    DateAssigned DATE NOT NULL,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE,
                    UNIQUE(StudentID, CourseID)
                )
            """,
            description="Create Grades table for final course grades",
            category="SCHEMA"
        ),

        'create_tutorials': Query(
            name='create_tutorials',
            sql="""
                CREATE TABLE IF NOT EXISTS Tutorials (
                    TutorialID INTEGER PRIMARY KEY AUTOINCREMENT,
                    StudentID INTEGER NOT NULL,
                    Date DATE NOT NULL,
                    Topic VARCHAR(255) NOT NULL,
                    Notes TEXT,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """,
            description="Create Tutorials table for tracking tutorial sessions",
            category="SCHEMA"
        ),

        'create_bans': Query(
            name='create_bans',
            sql="""
                CREATE TABLE IF NOT EXISTS Bans (
                    BanID INTEGER PRIMARY KEY AUTOINCREMENT,
                    StudentID INTEGER NOT NULL,
                    BanType VARCHAR(100) NOT NULL,
                    StartDate DATE NOT NULL,
                    EndDate DATE,
                    Reason TEXT NOT NULL,
                    FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                )
            """,
            description="Create Bans table for disciplinary actions",
            category="SCHEMA"
        ),

        'create_indices': Query(
            name='create_indices',
            sql="""
                CREATE INDEX IF NOT EXISTS idx_student_email ON Students(Email);
                CREATE INDEX IF NOT EXISTS idx_course_code ON Courses(CourseCode);
                CREATE INDEX IF NOT EXISTS idx_evaluation_student ON Evaluations(StudentID);
                CREATE INDEX IF NOT EXISTS idx_evaluation_course ON Evaluations(CourseID);
                CREATE INDEX IF NOT EXISTS idx_grades_student ON Grades(StudentID);
                CREATE INDEX IF NOT EXISTS idx_grades_course ON Grades(CourseID);
                CREATE INDEX IF NOT EXISTS idx_tutorials_student ON Tutorials(StudentID);
                CREATE INDEX IF NOT EXISTS idx_tutorials_date ON Tutorials(Date);
                CREATE INDEX IF NOT EXISTS idx_bans_student ON Bans(StudentID);
                CREATE INDEX IF NOT EXISTS idx_bans_dates ON Bans(StartDate, EndDate);
                CREATE INDEX IF NOT EXISTS idx_component_parent ON EvaluationComponents(ParentComponentID);
                CREATE INDEX IF NOT EXISTS idx_component_course ON EvaluationComponents(CourseID);
            """,
            description="Create performance indices",
            category="SCHEMA"
        )
    }

    # ========== DATA INSERTION QUERIES ==========
    INSERT_QUERIES = {
        'insert_student': Query(
            name='insert_student',
            sql="INSERT INTO Students (FirstName, LastName, Email, DateOfBirth) VALUES (?, ?, ?, ?)",
            description="Insert a new student",
            category="INSERT",
            params_required=True
        ),

        'insert_teacher': Query(
            name='insert_teacher',
            sql="INSERT INTO Teachers (FirstName, LastName, Email) VALUES (?, ?, ?)",
            description="Insert a new teacher",
            category="INSERT",
            params_required=True
        ),

        'insert_course': Query(
            name='insert_course',
            sql="INSERT INTO Courses (CourseName, CourseCode, TeacherID) VALUES (?, ?, ?)",
            description="Insert a new course",
            category="INSERT",
            params_required=True
        ),

        'insert_evaluation_component': Query(
            name='insert_evaluation_component',
            sql="""
                INSERT INTO EvaluationComponents 
                (CourseID, ParentComponentID, ComponentLevel, ComponentName, IsLeaf, OrderIndex) 
                VALUES (?, ?, ?, ?, ?, ?)
            """,
            description="Insert a new evaluation component",
            category="INSERT",
            params_required=True
        ),

        'insert_evaluation': Query(
            name='insert_evaluation',
            sql="""
                INSERT INTO Evaluations 
                (CourseID, StudentID, EvaluationComponentID, Score, MaxScore, Weight, DateAssigned, DateCompleted, Notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            description="Insert a new evaluation",
            category="INSERT",
            params_required=True
        ),

        'insert_grade': Query(
            name='insert_grade',
            sql="INSERT INTO Grades (StudentID, CourseID, FinalGrade, DateAssigned) VALUES (?, ?, ?, ?)",
            description="Insert a final grade",
            category="INSERT",
            params_required=True
        ),

        'insert_tutorial': Query(
            name='insert_tutorial',
            sql="INSERT INTO Tutorials (StudentID, Date, Topic, Notes) VALUES (?, ?, ?, ?)",
            description="Insert a tutorial session",
            category="INSERT",
            params_required=True
        ),

        'insert_ban': Query(
            name='insert_ban',
            sql="INSERT INTO Bans (StudentID, BanType, StartDate, EndDate, Reason) VALUES (?, ?, ?, ?, ?)",
            description="Insert a disciplinary ban",
            category="INSERT",
            params_required=True
        )
    }

    # ========== ANALYSIS QUERIES ==========
    ANALYSIS_QUERIES = {
        'count_all_tables': Query(
            name='count_all_tables',
            sql="""
                SELECT 'Students' as TableName, COUNT(*) as RecordCount FROM Students
                UNION ALL SELECT 'Teachers', COUNT(*) FROM Teachers
                UNION ALL SELECT 'Courses', COUNT(*) FROM Courses
                UNION ALL SELECT 'EvaluationComponents', COUNT(*) FROM EvaluationComponents
                UNION ALL SELECT 'Evaluations', COUNT(*) FROM Evaluations
                UNION ALL SELECT 'Grades', COUNT(*) FROM Grades
                UNION ALL SELECT 'Tutorials', COUNT(*) FROM Tutorials
                UNION ALL SELECT 'Bans', COUNT(*) FROM Bans
            """,
            description="Count records in all tables",
            category="ANALYSIS"
        ),

        'courses_with_teachers': Query(
            name='courses_with_teachers',
            sql="""
                SELECT 
                    c.CourseID,
                    c.CourseCode,
                    c.CourseName,
                    t.FirstName || ' ' || t.LastName as TeacherName,
                    t.Email as TeacherEmail
                FROM Courses c
                JOIN Teachers t ON c.TeacherID = t.TeacherID
                ORDER BY c.CourseCode
            """,
            description="List all courses with their assigned teachers",
            category="ANALYSIS"
        ),

        'student_grades_with_courses': Query(
            name='student_grades_with_courses',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    s.Email as StudentEmail,
                    c.CourseCode,
                    c.CourseName,
                    g.FinalGrade,
                    g.DateAssigned
                FROM Grades g
                JOIN Students s ON g.StudentID = s.StudentID
                JOIN Courses c ON g.CourseID = c.CourseID
                ORDER BY s.LastName, c.CourseCode
            """,
            description="Show all student grades with course information",
            category="ANALYSIS"
        ),

        'student_evaluations_detailed': Query(
            name='student_evaluations_detailed',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    c.CourseCode,
                    c.CourseName,
                    ec.ComponentName,
                    ec.ComponentLevel,
                    e.Score,
                    e.MaxScore,
                    e.Weight,
                    ROUND((e.Score / e.MaxScore * 100), 2) as Percentage,
                    e.DateAssigned,
                    e.DateCompleted,
                    e.Notes
                FROM Evaluations e
                JOIN Students s ON e.StudentID = s.StudentID
                JOIN Courses c ON e.CourseID = c.CourseID
                JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
                ORDER BY s.LastName, c.CourseCode, e.DateAssigned
            """,
            description="Detailed view of all student evaluations",
            category="ANALYSIS"
        ),

        'average_scores_by_student_course': Query(
            name='average_scores_by_student_course',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    c.CourseID,
                    c.CourseName,
                    COUNT(e.EvaluationID) as NumberOfEvaluations,
                    ROUND(AVG(e.Score), 2) as AverageScore,
                    ROUND(AVG(e.Score / e.MaxScore * 100), 2) as AveragePercentage,
                    MAX(e.Score) as HighestScore,
                    MIN(e.Score) as LowestScore
                FROM Evaluations e
                JOIN Students s ON e.StudentID = s.StudentID
                JOIN Courses c ON e.CourseID = c.CourseID
                GROUP BY s.StudentID, c.CourseID
                ORDER BY StudentName, c.CourseName
            """,
            description="Calculate average scores per student per course",
            category="ANALYSIS"
        ),

        'active_bans': Query(
            name='active_bans',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    b.BanType,
                    b.StartDate,
                    b.EndDate,
                    b.Reason,
                    CASE 
                        WHEN b.EndDate IS NULL THEN 'Permanent'
                        WHEN b.EndDate >= date('now') THEN 'Active'
                        ELSE 'Expired'
                    END as Status
                FROM Bans b
                JOIN Students s ON b.StudentID = s.StudentID
                WHERE b.EndDate IS NULL OR b.EndDate >= date('now')
                ORDER BY b.StartDate DESC
            """,
            description="Show currently active bans",
            category="ANALYSIS"
        ),

        'tutorials_list': Query(
            name='tutorials_list',
            sql="""
                SELECT 
                    t.TutorialID,
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    t.Date,
                    t.Topic,
                    t.Notes
                FROM Tutorials t
                JOIN Students s ON t.StudentID = s.StudentID
                ORDER BY t.Date DESC, s.LastName
            """,
            description="List all tutorial sessions",
            category="ANALYSIS"
        ),

        'leaf_components_by_course': Query(
            name='leaf_components_by_course',
            sql="""
                SELECT 
                    ec.ComponentID,
                    ec.ComponentName,
                    ec.ComponentLevel,
                    c.CourseCode,
                    c.CourseName,
                    ec.OrderIndex
                FROM EvaluationComponents ec
                JOIN Courses c ON ec.CourseID = c.CourseID
                WHERE ec.IsLeaf = 1
                ORDER BY c.CourseCode, ec.OrderIndex
            """,
            description="Show all evaluable (leaf) components by course",
            category="ANALYSIS"
        ),

        'component_hierarchy': Query(
            name='component_hierarchy',
            sql="""
                SELECT 
                    ec1.ComponentID,
                    ec1.ComponentName,
                    ec1.ComponentLevel,
                    ec1.ParentComponentID,
                    COALESCE(ec2.ComponentName, 'ROOT') as ParentName,
                    ec1.IsLeaf,
                    ec1.OrderIndex,
                    c.CourseCode,
                    c.CourseName
                FROM EvaluationComponents ec1
                LEFT JOIN EvaluationComponents ec2 ON ec1.ParentComponentID = ec2.ComponentID
                JOIN Courses c ON ec1.CourseID = c.CourseID
                ORDER BY c.CourseCode, ec1.OrderIndex
            """,
            description="Show evaluation component hierarchy",
            category="ANALYSIS"
        ),

        'student_scores_with_hierarchy': Query(
            name='student_scores_with_hierarchy',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName AS StudentName,
                    COALESCE(p3.ComponentName || ' > ', '') ||
                    COALESCE(p2.ComponentName || ' > ', '') ||
                    COALESCE(p1.ComponentName || ' > ', '') ||
                    ec.ComponentName AS EvaluationPath,
                    e.Score,
                    e.MaxScore,
                    ROUND((e.Score * 1.0 / e.MaxScore * 100), 2) AS Percentage,
                    e.Weight,
                    e.DateAssigned,
                    e.DateCompleted
                FROM Evaluations e
                JOIN Students s ON e.StudentID = s.StudentID
                JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
                LEFT JOIN EvaluationComponents p1 ON ec.ParentComponentID = p1.ComponentID
                LEFT JOIN EvaluationComponents p2 ON p1.ParentComponentID = p2.ComponentID
                LEFT JOIN EvaluationComponents p3 ON p2.ParentComponentID = p3.ComponentID
                ORDER BY s.LastName, s.FirstName, EvaluationPath
            """,
            description="Student scores with full evaluation hierarchy path",
            category="ANALYSIS"
        ),

        'top_performers': Query(
            name='top_performers',
            sql="""
                SELECT 
                    s.StudentID,
                    s.FirstName || ' ' || s.LastName as StudentName,
                    COUNT(DISTINCT e.CourseID) as CoursesEnrolled,
                    COUNT(e.EvaluationID) as TotalEvaluations,
                    ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as AveragePercentage,
                    ROUND(MAX(e.Score * 1.0 / e.MaxScore * 100), 2) as BestPercentage
                FROM Evaluations e
                JOIN Students s ON e.StudentID = s.StudentID
                GROUP BY s.StudentID
                HAVING AveragePercentage >= 80
                ORDER BY AveragePercentage DESC
            """,
            description="Identify top performing students (80% or higher average)",
            category="ANALYSIS"
        ),

        'course_statistics': Query(
            name='course_statistics',
            sql="""
                SELECT 
                    c.CourseID,
                    c.CourseCode,
                    c.CourseName,
                    COUNT(DISTINCT e.StudentID) as EnrolledStudents,
                    COUNT(e.EvaluationID) as TotalEvaluations,
                    ROUND(AVG(e.Score * 1.0 / e.MaxScore * 100), 2) as CourseAverage,
                    ROUND(MIN(e.Score * 1.0 / e.MaxScore * 100), 2) as LowestScore,
                    ROUND(MAX(e.Score * 1.0 / e.MaxScore * 100), 2) as HighestScore
                FROM Courses c
                LEFT JOIN Evaluations e ON c.CourseID = e.CourseID
                GROUP BY c.CourseID
                ORDER BY c.CourseCode
            """,
            description="Statistical summary for each course",
            category="ANALYSIS"
        )
    }

    # ========== UPDATE QUERIES ==========
    UPDATE_QUERIES = {
        'update_student_email': Query(
            name='update_student_email',
            sql="UPDATE Students SET Email = ? WHERE StudentID = ?",
            description="Update student email address",
            category="UPDATE",
            params_required=True
        ),

        'update_evaluation_score': Query(
            name='update_evaluation_score',
            sql="UPDATE Evaluations SET Score = ?, DateCompleted = ? WHERE EvaluationID = ?",
            description="Update evaluation score",
            category="UPDATE",
            params_required=True
        ),

        'update_final_grade': Query(
            name='update_final_grade',
            sql="UPDATE Grades SET FinalGrade = ?, DateAssigned = ? WHERE StudentID = ? AND CourseID = ?",
            description="Update final grade for a student in a course",
            category="UPDATE",
            params_required=True
        ),

        'update_ban_end_date': Query(
            name='update_ban_end_date',
            sql="UPDATE Bans SET EndDate = ? WHERE BanID = ?",
            description="Update ban end date",
            category="UPDATE",
            params_required=True
        ),

        'update_component_path': Query(
            name='update_component_path',
            sql="UPDATE EvaluationComponents SET ComponentPath = ? WHERE ComponentID = ?",
            description="Update component hierarchy path",
            category="UPDATE",
            params_required=True
        )
    }

    # ========== DELETE QUERIES ==========
    DELETE_QUERIES = {
        'delete_student': Query(
            name='delete_student',
            sql="DELETE FROM Students WHERE StudentID = ?",
            description="Delete a student (cascades to related records)",
            category="DELETE",
            params_required=True
        ),

        'delete_evaluation': Query(
            name='delete_evaluation',
            sql="DELETE FROM Evaluations WHERE EvaluationID = ?",
            description="Delete an evaluation",
            category="DELETE",
            params_required=True
        ),

        'delete_expired_bans': Query(
            name='delete_expired_bans',
            sql="DELETE FROM Bans WHERE EndDate < date('now')",
            description="Delete all expired bans",
            category="DELETE"
        )
    }

    @classmethod
    def get_query(cls, query_name: str) -> Optional[Query]:
        """
        Retrieve a specific query by name from any category.

        Args:
            query_name: The name of the query

        Returns:
            Query object or None if not found
        """
        # Search in all query dictionaries
        all_queries = {
            **cls.SCHEMA_QUERIES,
            **cls.INSERT_QUERIES,
            **cls.ANALYSIS_QUERIES,
            **cls.UPDATE_QUERIES,
            **cls.DELETE_QUERIES
        }
        return all_queries.get(query_name)

    @classmethod
    def get_queries_by_category(cls, category: str) -> Dict[str, Query]:
        """
        Get all queries in a specific category.

        Args:
            category: Category name (SCHEMA, INSERT, ANALYSIS, UPDATE, DELETE)

        Returns:
            Dictionary of queries in the category
        """
        category_map = {
            'SCHEMA': cls.SCHEMA_QUERIES,
            'INSERT': cls.INSERT_QUERIES,
            'ANALYSIS': cls.ANALYSIS_QUERIES,
            'UPDATE': cls.UPDATE_QUERIES,
            'DELETE': cls.DELETE_QUERIES
        }
        return category_map.get(category.upper(), {})

    @classmethod
    def list_all_queries(cls) -> Dict[str, List[str]]:
        """
        List all available queries organized by category.

        Returns:
            Dictionary with categories as keys and query names as values
        """
        return {
            'SCHEMA': list(cls.SCHEMA_QUERIES.keys()),
            'INSERT': list(cls.INSERT_QUERIES.keys()),
            'ANALYSIS': list(cls.ANALYSIS_QUERIES.keys()),
            'UPDATE': list(cls.UPDATE_QUERIES.keys()),
            'DELETE': list(cls.DELETE_QUERIES.keys())
        }

    @classmethod
    def get_query_info(cls, query_name: str) -> Optional[Dict[str, any]]:
        """
        Get detailed information about a query.

        Args:
            query_name: The name of the query

        Returns:
            Dictionary with query information or None
        """
        query = cls.get_query(query_name)
        if query:
            return {
                'name': query.name,
                'description': query.description,
                'category': query.category,
                'params_required': query.params_required,
                'sql': query.sql
            }
        return None