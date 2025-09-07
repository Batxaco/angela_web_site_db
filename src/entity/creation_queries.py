"""
SQL queries for creating the student database schema.

This module contains all SQL DDL (Data Definition Language) statements
for creating tables, indexes, and constraints in the MySQL database with
the new hierarchical evaluation structure.
"""

from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Table creation order (respects foreign key dependencies)
TABLE_CREATION_ORDER = [
    'Students',
    'Teachers',
    'Courses',
    'Enrollments',
    'Levels',
    'EvaluationGroups',
    'EvaluationComponents',
    'StudentScores',
    'Grades',
    'Tutorials',
    'Bans'
]

# SQL queries for creating individual tables
CREATE_TABLE_QUERIES: Dict[str, str] = {
    'Students': """
        CREATE TABLE IF NOT EXISTS Students (
            StudentID INT PRIMARY KEY AUTO_INCREMENT,
            FirstName VARCHAR(100) NOT NULL,
            LastName VARCHAR(100) NOT NULL,
            Email VARCHAR(255) NOT NULL UNIQUE,
            DateOfBirth DATE,
            PhoneNumber VARCHAR(20),
            Address TEXT,
            EnrollmentDate DATE DEFAULT NULL,
            Status ENUM('Active', 'Inactive', 'Suspended', 'Graduated') DEFAULT 'Active',
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_email (Email),
            INDEX idx_status (Status),
            INDEX idx_enrollment_date (EnrollmentDate),
            INDEX idx_name (FirstName, LastName)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Student information and enrollment details'
    """,

    'Teachers': """
        CREATE TABLE IF NOT EXISTS Teachers (
            TeacherID INT PRIMARY KEY AUTO_INCREMENT,
            FirstName VARCHAR(100) NOT NULL,
            LastName VARCHAR(100) NOT NULL,
            Email VARCHAR(255) NOT NULL UNIQUE,
            PhoneNumber VARCHAR(20),
            Department VARCHAR(100),
            HireDate DATE DEFAULT NULL,
            Status ENUM('Active', 'Inactive', 'On Leave') DEFAULT 'Active',
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            INDEX idx_email (Email),
            INDEX idx_department (Department),
            INDEX idx_status (Status),
            INDEX idx_name (FirstName, LastName)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Teacher information and employment details'
    """,

    'Courses': """
        CREATE TABLE IF NOT EXISTS Courses (
            CourseID INT PRIMARY KEY AUTO_INCREMENT,
            CourseLevel VARCHAR(50) NOT NULL,
            CourseGroup VARCHAR(10) NOT NULL,
            TeacherID INT NOT NULL,
            CourseName VARCHAR(100),
            CourseCode VARCHAR(50) UNIQUE,
            Description TEXT,
            Credits INT DEFAULT 3,
            Semester VARCHAR(50),
            AcademicYear VARCHAR(20),
            MaxStudents INT DEFAULT 30,
            Status ENUM('Active', 'Inactive', 'Cancelled') DEFAULT 'Active',
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
                ON DELETE RESTRICT ON UPDATE CASCADE,
            
            INDEX idx_course_code (CourseCode),
            INDEX idx_teacher (TeacherID),
            INDEX idx_course_level (CourseLevel),
            INDEX idx_course_group (CourseGroup),
            INDEX idx_semester_year (Semester, AcademicYear),
            INDEX idx_status (Status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Course catalog with level and group information'
    """,

    'Enrollments': """
        CREATE TABLE IF NOT EXISTS Enrollments (
            EnrollmentID INT PRIMARY KEY AUTO_INCREMENT,
            StudentID INT NOT NULL,
            CourseID INT NOT NULL,
            EnrollmentDate DATE NOT NULL,
            Status ENUM('Active', 'Dropped', 'Completed', 'Withdrawn') DEFAULT 'Active',
            Grade CHAR(2),
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE CASCADE ON UPDATE CASCADE,
    
            UNIQUE KEY unique_enrollment (StudentID, CourseID),
            INDEX idx_student (StudentID),
            INDEX idx_course (CourseID),
            INDEX idx_enrollment_date (EnrollmentDate),
            INDEX idx_status (Status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Student course enrollment records'
    """,

    'Levels': """
        CREATE TABLE IF NOT EXISTS Levels (
            LevelID INT PRIMARY KEY AUTO_INCREMENT,
            CourseID INT NOT NULL,
            LevelName VARCHAR(100) NOT NULL,
            LevelCode VARCHAR(50),
            Description TEXT,
            Weight DECIMAL(5,2) NOT NULL DEFAULT 1.0,
            MaxScore DECIMAL(10,2) NOT NULL DEFAULT 100.00,
            OrderIndex INT DEFAULT 0,
            IsActive TINYINT(1) DEFAULT 1,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            
            UNIQUE KEY unique_level_code (CourseID, LevelCode),
            INDEX idx_course (CourseID),
            INDEX idx_level_code (LevelCode),
            INDEX idx_order (OrderIndex),
            INDEX idx_active (IsActive)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Evaluation levels within courses (e.g., Midterm, Final, Projects)'
    """,

    'EvaluationGroups': """
        CREATE TABLE IF NOT EXISTS EvaluationGroups (
            GroupID INT PRIMARY KEY AUTO_INCREMENT,
            LevelID INT NOT NULL,
            GroupName VARCHAR(255) NOT NULL,
            GroupCode VARCHAR(50),
            Description TEXT,
            Weight DECIMAL(5,2) NOT NULL DEFAULT 1.0,
            MaxScore DECIMAL(10,2) NOT NULL DEFAULT 100.00,
            OrderIndex INT DEFAULT 0,
            IsActive TINYINT(1) DEFAULT 1,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (LevelID) REFERENCES Levels(LevelID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            
            UNIQUE KEY unique_group_code (LevelID, GroupCode),
            INDEX idx_level (LevelID),
            INDEX idx_group_code (GroupCode),
            INDEX idx_order (OrderIndex),
            INDEX idx_active (IsActive)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Evaluation groups within levels (e.g., Written Exams, Practical Tests)'
    """,

    'EvaluationComponents': """
        CREATE TABLE IF NOT EXISTS EvaluationComponents (
            ComponentID INT PRIMARY KEY AUTO_INCREMENT,
            CourseID INT NOT NULL,
            GroupID INT NOT NULL,
            ComponentName VARCHAR(255) NOT NULL,
            ComponentCode VARCHAR(50),
            Description TEXT,
            Weight DECIMAL(5,2) NOT NULL DEFAULT 1.0,
            MaxScore DECIMAL(10,2) NOT NULL DEFAULT 100.00,
            OrderIndex INT DEFAULT 0,
            DueDate DATE,
            IsActive TINYINT(1) DEFAULT 1,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (GroupID) REFERENCES EvaluationGroups(GroupID)
                ON DELETE CASCADE ON UPDATE CASCADE,
    
            UNIQUE KEY unique_component_code (GroupID, ComponentCode),
            INDEX idx_course (CourseID),
            INDEX idx_group (GroupID),
            INDEX idx_component_code (ComponentCode),
            INDEX idx_order (OrderIndex),
            INDEX idx_due_date (DueDate),
            INDEX idx_active (IsActive),
            INDEX idx_course_group (CourseID, GroupID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Individual evaluation components with course context'
    """,

    'StudentScores': """
        CREATE TABLE IF NOT EXISTS StudentScores (
            ScoreID INT PRIMARY KEY AUTO_INCREMENT,
            StudentID INT NOT NULL,
            CourseID INT NOT NULL,
            LevelID INT NULL,
            GroupID INT NULL,
            ComponentID INT NULL,
            Score DECIMAL(10,2),
            MaxPossibleScore DECIMAL(10,2),
            Percentage DECIMAL(5,2) DEFAULT NULL,
            DateCompleted DATE,
            Status ENUM('Not Started', 'In Progress', 'Completed', 'Late', 'Exempt') DEFAULT 'Not Started',
            Notes TEXT,
            Feedback TEXT,
            RecordedBy INT,
            RecordedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (LevelID) REFERENCES Levels(LevelID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (GroupID) REFERENCES EvaluationGroups(GroupID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (ComponentID) REFERENCES EvaluationComponents(ComponentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (RecordedBy) REFERENCES Teachers(TeacherID)
                ON DELETE SET NULL ON UPDATE CASCADE,
            
            INDEX idx_student (StudentID),
            INDEX idx_course (CourseID),
            INDEX idx_level (LevelID),
            INDEX idx_group (GroupID),
            INDEX idx_component (ComponentID),
            INDEX idx_recorded_by (RecordedBy),
            INDEX idx_date_completed (DateCompleted),
            INDEX idx_status (Status),
            INDEX idx_student_course (StudentID, CourseID),
            INDEX idx_student_level (StudentID, LevelID),
            INDEX idx_student_group (StudentID, GroupID),
            INDEX idx_student_component (StudentID, ComponentID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Polymorphic scores table supporting Level, Group, and Component evaluations with course context'
    """,

    'Grades': """
        CREATE TABLE IF NOT EXISTS Grades (
            GradeID INT PRIMARY KEY AUTO_INCREMENT,
            StudentID INT NOT NULL,
            CourseID INT NOT NULL,
            FinalGrade DECIMAL(5,2) NOT NULL,
            LetterGrade CHAR(2),
            GradePoints DECIMAL(3,2),
            Semester VARCHAR(50),
            AcademicYear VARCHAR(20),
            Status ENUM('Provisional', 'Final', 'Incomplete') DEFAULT 'Provisional',
            DateAssigned DATE NOT NULL,
            Comments TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            
            UNIQUE KEY unique_student_course (StudentID, CourseID, Semester, AcademicYear),
            INDEX idx_student (StudentID),
            INDEX idx_course (CourseID),
            INDEX idx_semester_year (Semester, AcademicYear),
            INDEX idx_grade (FinalGrade),
            INDEX idx_status (Status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Final course grades and academic records'
    """,

    'Tutorials': """
        CREATE TABLE IF NOT EXISTS Tutorials (
            TutorialID INT PRIMARY KEY AUTO_INCREMENT,
            StudentID INT NOT NULL,
            TeacherID INT,
            CourseID INT,
            Date DATE NOT NULL,
            StartTime TIME,
            EndTime TIME,
            Duration INT DEFAULT NULL,
            Topic VARCHAR(255) NOT NULL,
            Description TEXT,
            Notes TEXT,
            Status ENUM('Scheduled', 'Completed', 'Cancelled', 'No Show') DEFAULT 'Scheduled',
            Location VARCHAR(100),
            TutorialType ENUM('Individual', 'Group', 'Online') DEFAULT 'Individual',
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
                ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                ON DELETE SET NULL ON UPDATE CASCADE,
            
            INDEX idx_student (StudentID),
            INDEX idx_teacher (TeacherID),
            INDEX idx_course (CourseID),
            INDEX idx_date (Date),
            INDEX idx_status (Status),
            INDEX idx_type (TutorialType)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Tutorial sessions and academic support records'
    """,

    'Bans': """
        CREATE TABLE IF NOT EXISTS Bans (
            BanID INT PRIMARY KEY AUTO_INCREMENT,
            StudentID INT NOT NULL,
            BanType VARCHAR(100) NOT NULL,
            Category ENUM('Academic', 'Disciplinary', 'Financial', 'Administrative') NOT NULL,
            Severity ENUM('Warning', 'Minor', 'Major', 'Severe') DEFAULT 'Minor',
            StartDate DATE NOT NULL,
            EndDate DATE,
            IsActive TINYINT(1) DEFAULT NULL,
            Reason TEXT NOT NULL,
            Description TEXT,
            IssuedBy INT,
            Resolution TEXT,
            ResolutionDate DATE,
            AppealStatus ENUM('None', 'Pending', 'Approved', 'Denied') DEFAULT 'None',
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            FOREIGN KEY (StudentID) REFERENCES Students(StudentID)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (IssuedBy) REFERENCES Teachers(TeacherID)
                ON DELETE SET NULL ON UPDATE CASCADE,
            
            INDEX idx_student (StudentID),
            INDEX idx_active (IsActive),
            INDEX idx_dates (StartDate, EndDate),
            INDEX idx_type_category (BanType, Category),
            INDEX idx_severity (Severity),
            INDEX idx_appeal (AppealStatus)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='Student disciplinary and restriction records'
    """
}

# Drop table queries (in reverse dependency order)
DROP_TABLE_QUERIES: Dict[str, str] = {
    'Bans': "DROP TABLE IF EXISTS Bans",
    'Tutorials': "DROP TABLE IF EXISTS Tutorials",
    'Grades': "DROP TABLE IF EXISTS Grades",
    'StudentScores': "DROP TABLE IF EXISTS StudentScores",
    'EvaluationComponents': "DROP TABLE IF EXISTS EvaluationComponents",
    'EvaluationGroups': "DROP TABLE IF EXISTS EvaluationGroups",
    'Levels': "DROP TABLE IF EXISTS Levels",
    'Enrollments': "DROP TABLE IF EXISTS Enrollments",
    'Courses': "DROP TABLE IF EXISTS Courses",
    'Teachers': "DROP TABLE IF EXISTS Teachers",
    'Students': "DROP TABLE IF EXISTS Students",
}

# Table drop order (reverse of creation order to respect foreign keys)
TABLE_DROP_ORDER = list(reversed(TABLE_CREATION_ORDER))

# Triggers for MySQL 5.7 compatibility (replaces generated columns)
CREATE_TRIGGERS: Dict[str, str] = {
    'StudentScores_Percentage_Insert': """
        CREATE TRIGGER StudentScores_Percentage_Insert
        BEFORE INSERT ON StudentScores
        FOR EACH ROW
        BEGIN
            IF NEW.MaxPossibleScore > 0 THEN
                SET NEW.Percentage = (NEW.Score / NEW.MaxPossibleScore) * 100;
            ELSE
                SET NEW.Percentage = NULL;
            END IF;
        END
    """,

    'StudentScores_Percentage_Update': """
        CREATE TRIGGER StudentScores_Percentage_Update
        BEFORE UPDATE ON StudentScores
        FOR EACH ROW
        BEGIN
            IF NEW.MaxPossibleScore > 0 THEN
                SET NEW.Percentage = (NEW.Score / NEW.MaxPossibleScore) * 100;
            ELSE
                SET NEW.Percentage = NULL;
            END IF;
        END
    """,

    'Tutorials_Duration_Insert': """
        CREATE TRIGGER Tutorials_Duration_Insert
        BEFORE INSERT ON Tutorials
        FOR EACH ROW
        BEGIN
            IF NEW.StartTime IS NOT NULL AND NEW.EndTime IS NOT NULL THEN
                SET NEW.Duration = TIME_TO_SEC(TIMEDIFF(NEW.EndTime, NEW.StartTime)) / 60;
            ELSE
                SET NEW.Duration = NULL;
            END IF;
        END
    """,

    'Tutorials_Duration_Update': """
        CREATE TRIGGER Tutorials_Duration_Update
        BEFORE UPDATE ON Tutorials
        FOR EACH ROW
        BEGIN
            IF NEW.StartTime IS NOT NULL AND NEW.EndTime IS NOT NULL THEN
                SET NEW.Duration = TIME_TO_SEC(TIMEDIFF(NEW.EndTime, NEW.StartTime)) / 60;
            ELSE
                SET NEW.Duration = NULL;
            END IF;
        END
    """,

    'Bans_IsActive_Insert': """
        CREATE TRIGGER Bans_IsActive_Insert
        BEFORE INSERT ON Bans
        FOR EACH ROW
        BEGIN
            IF NEW.EndDate IS NULL THEN
                SET NEW.IsActive = 1;
            ELSEIF NEW.EndDate >= CURDATE() THEN
                SET NEW.IsActive = 1;
            ELSE
                SET NEW.IsActive = 0;
            END IF;
        END
    """,

    'Bans_IsActive_Update': """
        CREATE TRIGGER Bans_IsActive_Update
        BEFORE UPDATE ON Bans
        FOR EACH ROW
        BEGIN
            IF NEW.EndDate IS NULL THEN
                SET NEW.IsActive = 1;
            ELSEIF NEW.EndDate >= CURDATE() THEN
                SET NEW.IsActive = 1;
            ELSE
                SET NEW.IsActive = 0;
            END IF;
        END
    """,

    'Students_EnrollmentDate_Insert': """
        CREATE TRIGGER Students_EnrollmentDate_Insert
        BEFORE INSERT ON Students
        FOR EACH ROW
        BEGIN
            IF NEW.EnrollmentDate IS NULL THEN
                SET NEW.EnrollmentDate = CURDATE();
            END IF;
        END
    """,

    'Teachers_HireDate_Insert': """
        CREATE TRIGGER Teachers_HireDate_Insert
        BEFORE INSERT ON Teachers
        FOR EACH ROW
        BEGIN
            IF NEW.HireDate IS NULL THEN
                SET NEW.HireDate = CURDATE();
            END IF;
        END
    """
}

# Views for common queries (MySQL 5.7 compatible)
CREATE_VIEWS: Dict[str, str] = {
    'StudentGradeSummary': """
        CREATE OR REPLACE VIEW StudentGradeSummary AS
        SELECT 
            s.StudentID,
            CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
            s.Email,
            c.CourseCode,
            c.CourseName,
            c.CourseLevel,
            c.CourseGroup,
            g.FinalGrade,
            g.LetterGrade,
            g.GradePoints,
            g.Semester,
            g.AcademicYear,
            g.Status AS GradeStatus
        FROM Students s
        JOIN Grades g ON s.StudentID = g.StudentID
        JOIN Courses c ON g.CourseID = c.CourseID
        WHERE s.Status = 'Active'
        ORDER BY s.LastName, s.FirstName, g.AcademicYear DESC, g.Semester
    """,

    'CourseEvaluationStructure': """
        CREATE OR REPLACE VIEW CourseEvaluationStructure AS
        SELECT 
            c.CourseID,
            c.CourseName,
            c.CourseCode,
            c.CourseLevel,
            c.CourseGroup,
            l.LevelID,
            l.LevelName,
            l.LevelCode,
            l.Weight as LevelWeight,
            eg.GroupID,
            eg.GroupName,
            eg.Weight as GroupWeight,
            ec.ComponentID,
            ec.ComponentName,
            ec.ComponentCode,
            ec.Weight as ComponentWeight,
            ec.MaxScore,
            ec.DueDate,
            CONCAT(IFNULL(l.LevelName, ''), 
                   CASE WHEN l.LevelName IS NOT NULL AND eg.GroupName IS NOT NULL THEN ' > ' ELSE '' END,
                   IFNULL(eg.GroupName, ''),
                   CASE WHEN eg.GroupName IS NOT NULL AND ec.ComponentName IS NOT NULL THEN ' > ' ELSE '' END,
                   IFNULL(ec.ComponentName, '')) AS FullPath
        FROM Courses c
        LEFT JOIN Levels l ON c.CourseID = l.CourseID
        LEFT JOIN EvaluationGroups eg ON l.LevelID = eg.LevelID
        LEFT JOIN EvaluationComponents ec ON eg.GroupID = ec.GroupID AND c.CourseID = ec.CourseID
        WHERE (l.IsActive IS NULL OR l.IsActive = 1)
        AND (eg.IsActive IS NULL OR eg.IsActive = 1)
        AND (ec.IsActive IS NULL OR ec.IsActive = 1)
        ORDER BY c.CourseName, l.OrderIndex, eg.OrderIndex, ec.OrderIndex
    """,

    'StudentScoresSummary': """
        CREATE OR REPLACE VIEW StudentScoresSummary AS
        SELECT 
            s.StudentID,
            CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN l.CourseID
                WHEN ss.GroupID IS NOT NULL THEN l2.CourseID
                WHEN ss.ComponentID IS NOT NULL THEN l3.CourseID
                ELSE NULL
            END AS CourseID,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN c1.CourseName
                WHEN ss.GroupID IS NOT NULL THEN c2.CourseName
                WHEN ss.ComponentID IS NOT NULL THEN c3.CourseName
                ELSE NULL
            END AS CourseName,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN c1.CourseCode
                WHEN ss.GroupID IS NOT NULL THEN c2.CourseCode
                WHEN ss.ComponentID IS NOT NULL THEN c3.CourseCode
                ELSE NULL
            END AS CourseCode,
            ss.ScoreID,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN 'Level'
                WHEN ss.GroupID IS NOT NULL THEN 'Group'
                WHEN ss.ComponentID IS NOT NULL THEN 'Component'
                ELSE 'Unknown'
            END AS ScoreType,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN l.LevelName
                WHEN ss.GroupID IS NOT NULL THEN eg.GroupName
                WHEN ss.ComponentID IS NOT NULL THEN ec.ComponentName
                ELSE NULL
            END AS EvaluationName,
            CASE 
                WHEN ss.LevelID IS NOT NULL THEN l.LevelCode
                WHEN ss.GroupID IS NOT NULL THEN eg.GroupCode
                WHEN ss.ComponentID IS NOT NULL THEN ec.ComponentCode
                ELSE NULL
            END AS EvaluationCode,
            ss.Score,
            ss.MaxPossibleScore,
            ss.Percentage,
            ss.Status,
            ss.DateCompleted,
            CONCAT(t.FirstName, ' ', t.LastName) AS RecordedByTeacher
        FROM StudentScores ss
        JOIN Students s ON ss.StudentID = s.StudentID
        LEFT JOIN Levels l ON ss.LevelID = l.LevelID
        LEFT JOIN Courses c1 ON l.CourseID = c1.CourseID
        LEFT JOIN EvaluationGroups eg ON ss.GroupID = eg.GroupID
        LEFT JOIN Levels l2 ON eg.LevelID = l2.LevelID
        LEFT JOIN Courses c2 ON l2.CourseID = c2.CourseID
        LEFT JOIN EvaluationComponents ec ON ss.ComponentID = ec.ComponentID
        LEFT JOIN EvaluationGroups eg2 ON ec.GroupID = eg2.GroupID
        LEFT JOIN Levels l3 ON eg2.LevelID = l3.LevelID
        LEFT JOIN Courses c3 ON l3.CourseID = c3.CourseID
        LEFT JOIN Teachers t ON ss.RecordedBy = t.TeacherID
        WHERE s.Status = 'Active'
        ORDER BY s.LastName, s.FirstName, CourseID, ss.DateCompleted DESC
    """,

    'ActiveBansSummary': """
        CREATE OR REPLACE VIEW ActiveBansSummary AS
        SELECT 
            b.BanID,
            s.StudentID,
            CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
            s.Email,
            b.BanType,
            b.Category,
            b.Severity,
            b.StartDate,
            b.EndDate,
            b.IsActive,
            DATEDIFF(IFNULL(b.EndDate, CURDATE()), b.StartDate) AS DaysActive,
            b.Reason,
            CONCAT(t.FirstName, ' ', t.LastName) AS IssuedByName
        FROM Bans b
        JOIN Students s ON b.StudentID = s.StudentID
        LEFT JOIN Teachers t ON b.IssuedBy = t.TeacherID
        WHERE b.IsActive = 1
        ORDER BY 
            CASE b.Severity 
                WHEN 'Severe' THEN 1 
                WHEN 'Major' THEN 2 
                WHEN 'Minor' THEN 3 
                WHEN 'Warning' THEN 4 
                ELSE 5 
            END, 
            b.StartDate DESC
    """
}

# Stored procedures for common operations (MySQL 5.7 compatible)
CREATE_PROCEDURES: Dict[str, str] = {
    'CalculateStudentGPA': """
        DROP PROCEDURE IF EXISTS CalculateStudentGPA;

        CREATE PROCEDURE CalculateStudentGPA(
            IN student_id INT,
            IN academic_year VARCHAR(20),
            OUT gpa DECIMAL(3,2)
        )
        BEGIN
            DECLARE total_points DECIMAL(10,2) DEFAULT 0;
            DECLARE total_credits INT DEFAULT 0;

            SELECT 
                IFNULL(SUM(g.GradePoints * c.Credits), 0),
                IFNULL(SUM(c.Credits), 0)
            INTO total_points, total_credits
            FROM Grades g
            JOIN Courses c ON g.CourseID = c.CourseID
            WHERE g.StudentID = student_id 
            AND (academic_year IS NULL OR g.AcademicYear = academic_year)
            AND g.Status = 'Final';

            IF total_credits > 0 THEN
                SET gpa = total_points / total_credits;
            ELSE
                SET gpa = 0.00;
            END IF;
        END
    """,

    'GetStudentTranscript': """
        DROP PROCEDURE IF EXISTS GetStudentTranscript;

        CREATE PROCEDURE GetStudentTranscript(
            IN student_id INT
        )
        BEGIN
            SELECT 
                c.CourseCode,
                c.CourseName,
                c.CourseLevel,
                c.CourseGroup,
                c.Credits,
                g.FinalGrade,
                g.LetterGrade,
                g.GradePoints,
                g.Semester,
                g.AcademicYear,
                CONCAT(t.FirstName, ' ', t.LastName) AS Teacher
            FROM Grades g
            JOIN Courses c ON g.CourseID = c.CourseID
            JOIN Teachers t ON c.TeacherID = t.TeacherID
            WHERE g.StudentID = student_id
            AND g.Status = 'Final'
            ORDER BY g.AcademicYear, g.Semester, c.CourseCode;
        END
    """,

    'CalculateWeightedScore': """
        DROP PROCEDURE IF EXISTS CalculateWeightedScore;

        CREATE PROCEDURE CalculateWeightedScore(
            IN student_id INT,
            IN course_id INT,
            IN target_level VARCHAR(20),
            OUT weighted_score DECIMAL(10,2)
        )
        BEGIN
            DECLARE total_weighted DECIMAL(10,2) DEFAULT 0;
            DECLARE total_weight DECIMAL(10,2) DEFAULT 0;

            IF target_level = 'Course' THEN
                SELECT 
                    IFNULL(SUM((ss.Score / ss.MaxPossibleScore) * l.Weight), 0),
                    IFNULL(SUM(l.Weight), 0)
                INTO total_weighted, total_weight
                FROM StudentScores ss
                JOIN Levels l ON ss.LevelID = l.LevelID
                WHERE ss.StudentID = student_id 
                AND l.CourseID = course_id
                AND ss.Status = 'Completed';

            ELSEIF target_level = 'Level' THEN
                SELECT 
                    IFNULL(SUM((ss.Score / ss.MaxPossibleScore) * eg.Weight), 0),
                    IFNULL(SUM(eg.Weight), 0)
                INTO total_weighted, total_weight
                FROM StudentScores ss
                JOIN EvaluationGroups eg ON ss.GroupID = eg.GroupID
                JOIN Levels l ON eg.LevelID = l.LevelID
                WHERE ss.StudentID = student_id 
                AND l.CourseID = course_id
                AND ss.Status = 'Completed';

            ELSEIF target_level = 'Group' THEN
                SELECT 
                    IFNULL(SUM((ss.Score / ss.MaxPossibleScore) * ec.Weight), 0),
                    IFNULL(SUM(ec.Weight), 0)
                INTO total_weighted, total_weight
                FROM StudentScores ss
                JOIN EvaluationComponents ec ON ss.ComponentID = ec.ComponentID
                WHERE ss.StudentID = student_id 
                AND ss.Status = 'Completed';
            END IF;

            IF total_weight > 0 THEN
                SET weighted_score = (total_weighted / total_weight) * 100;
            ELSE
                SET weighted_score = 0.00;
            END IF;
        END
    """
}

# Interface functions expected by main.py
def get_creation_queries_by_order(table_names: List[str] = None) -> List[Tuple[str, str]]:
    """
    Get creation queries in dependency order.
    Expected by main.py - returns list of (table_name, query) tuples.

    Args:
        table_names: Optional list of specific tables to include

    Returns:
        List of tuples (table_name, query) in creation order
    """
    if table_names is None:
        table_names = TABLE_CREATION_ORDER
    else:
        # Filter and maintain order
        table_names = [t for t in TABLE_CREATION_ORDER if t in table_names]

    return [(table, CREATE_TABLE_QUERIES[table]) for table in table_names]


def get_drop_queries_by_order(table_names: List[str] = None) -> List[Tuple[str, str]]:
    """
    Get drop queries in reverse dependency order.
    Expected by main.py - returns list of (table_name, query) tuples.

    Args:
        table_names: Optional list of specific tables to include

    Returns:
        List of tuples (table_name, query) in drop order
    """
    if table_names is None:
        table_names = TABLE_DROP_ORDER
    else:
        # Filter and maintain reverse order
        table_names = [t for t in TABLE_DROP_ORDER if t in table_names]

    return [(table, DROP_TABLE_QUERIES[table]) for table in table_names]


def get_trigger_queries() -> List[Tuple[str, str]]:
    """
    Get trigger creation queries for MySQL 5.7 compatibility.
    Expected by main.py - returns list of (trigger_name, query) tuples.

    Returns:
        List of tuples (trigger_name, query)
    """
    return [(name, query) for name, query in CREATE_TRIGGERS.items()]


# Additional utility functions for compatibility and debugging
def debug_table_creation_order() -> None:
    """Debug function to print table creation order and dependencies."""
    dependencies = validate_table_dependencies()
    print("Table Creation Order:")
    for i, table in enumerate(TABLE_CREATION_ORDER, 1):
        deps = dependencies.get(table, [])
        print(f"{i}. {table} (depends on: {deps if deps else 'none'})")

    # Validate order
    created_tables = set()
    for table in TABLE_CREATION_ORDER:
        deps = dependencies.get(table, [])
        missing_deps = [dep for dep in deps if dep not in created_tables]
        if missing_deps:
            print(f"WARNING: {table} depends on {missing_deps} which haven't been created yet!")
        created_tables.add(table)


def validate_table_dependencies() -> Dict[str, List[str]]:
    """
    Validate and return table dependencies.

    Returns:
        Dictionary mapping table names to their dependencies
    """
    dependencies = {
        'Students': [],
        'Teachers': [],
        'Courses': ['Teachers'],
        'Levels': ['Courses'],
        'EvaluationGroups': ['Levels'],
        'EvaluationComponents': ['EvaluationGroups'],
        'StudentScores': ['Students', 'Levels', 'EvaluationGroups', 'EvaluationComponents', 'Teachers'],
        'Grades': ['Students', 'Courses'],
        'Tutorials': ['Students', 'Teachers', 'Courses'],
        'Bans': ['Students', 'Teachers']
    }

    logger.debug(f"Table dependencies validated: {dependencies}")
    return dependencies


def get_table_creation_query(table_name: str) -> str:
    """
    Get the creation query for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        SQL CREATE TABLE query

    Raises:
        KeyError: If table name is not found
    """
    if table_name not in CREATE_TABLE_QUERIES:
        raise KeyError(f"No creation query found for table: {table_name}")

    return CREATE_TABLE_QUERIES[table_name]


def get_table_drop_query(table_name: str) -> str:
    """
    Get the drop query for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        SQL DROP TABLE query

    Raises:
        KeyError: If table name is not found
    """
    if table_name not in DROP_TABLE_QUERIES:
        raise KeyError(f"No drop query found for table: {table_name}")

    return DROP_TABLE_QUERIES[table_name]


def get_all_table_names() -> List[str]:
    """
    Get list of all available table names.

    Returns:
        List of table names
    """
    return list(CREATE_TABLE_QUERIES.keys())


def get_table_creation_order() -> List[str]:
    """
    Get the order in which tables should be created.

    Returns:
        List of table names in creation order
    """
    return TABLE_CREATION_ORDER.copy()


def get_table_drop_order() -> List[str]:
    """
    Get the order in which tables should be dropped.

    Returns:
        List of table names in drop order
    """
    return TABLE_DROP_ORDER.copy()


def get_mysql57_compatibility_info() -> Dict[str, Any]:
    """
    Get information about MySQL 5.7 compatibility changes.

    Returns:
        Dictionary with compatibility information
    """
    return {
        'compatibility_version': '5.7',
        'changes_made': [
            'Removed DEFAULT (CURRENT_DATE) syntax - changed to DEFAULT NULL with triggers',
            'Replaced GENERATED ALWAYS AS columns with regular columns + triggers',
            'Changed BOOLEAN to TINYINT(1) for better compatibility',
            'Replaced COALESCE with IFNULL in views and procedures',
            'Added triggers for calculated fields (Percentage, Duration, IsActive)',
            'Updated views to use IFNULL instead of COALESCE',
            'Modified constraint syntax for MySQL 5.7 compatibility'
        ],
        'triggers_added': list(CREATE_TRIGGERS.keys()),
        'features_replaced': {
            'generated_columns': 'triggers',
            'check_constraints': 'application_logic',
            'current_date_default': 'trigger_based_defaults'
        },
        'manual_steps_required': [
            'Percentage calculation handled by triggers',
            'Tutorial duration calculation handled by triggers',
            'Ban active status calculation handled by triggers',
            'Default dates set by triggers on insert'
        ]
    }


def validate_query_syntax(table_name: str) -> bool:
    """
    Validate basic SQL syntax for a table creation query.

    Args:
        table_name: Name of the table to validate

    Returns:
        True if query syntax appears valid
    """
    if table_name not in CREATE_TABLE_QUERIES:
        logger.error(f"Table {table_name} not found in creation queries")
        return False

    query = CREATE_TABLE_QUERIES[table_name]

    # Basic syntax checks
    required_elements = [
        'CREATE TABLE IF NOT EXISTS',
        table_name,
        'ENGINE=InnoDB',
        'DEFAULT CHARSET=utf8mb4'
    ]

    for element in required_elements:
        if element not in query:
            logger.error(f"Missing required element '{element}' in {table_name} query")
            return False

    # Check for primary key
    if 'PRIMARY KEY' not in query and 'AUTO_INCREMENT' not in query:
        logger.warning(f"Table {table_name} may be missing a primary key")
        return False

    logger.debug(f"Query syntax validated for table {table_name}")
    return True


def create_sample_evaluation_structure() -> List[str]:
    """
    Generate sample SQL statements to create a typical evaluation structure.

    Returns:
        List of SQL INSERT statements for sample data
    """
    return [
        # Sample Course
        """INSERT INTO Courses (CourseLevel, CourseGroup, TeacherID, CourseName, CourseCode) 
           VALUES ('Intermediate', 'CS', 1, 'Advanced Programming', 'CS201')""",

        # Sample Levels
        """INSERT INTO Levels (CourseID, LevelName, LevelCode, Weight, OrderIndex) VALUES
           (1, 'Midterm Evaluations', 'MID', 40.0, 1),
           (1, 'Final Evaluations', 'FINAL', 60.0, 2)""",

        # Sample Groups
        """INSERT INTO EvaluationGroups (LevelID, GroupName, GroupCode, Weight, OrderIndex) VALUES
           (1, 'Written Exams', 'WRITTEN', 70.0, 1),
           (1, 'Programming Assignments', 'PROG', 30.0, 2),
           (2, 'Final Assessment', 'FINAL_ASSESS', 100.0, 1)""",

        # Sample Components
        """INSERT INTO EvaluationComponents (GroupID, ComponentName, ComponentCode, Weight, MaxScore, OrderIndex) VALUES
           (1, 'Midterm Exam', 'MID_EXAM', 100.0, 100.0, 1),
           (2, 'Assignment 1', 'ASSIGN1', 50.0, 100.0, 1),
           (2, 'Assignment 2', 'ASSIGN2', 50.0, 100.0, 2),
           (3, 'Final Exam', 'FINAL_EXAM', 80.0, 100.0, 1),
           (3, 'Final Project', 'FINAL_PROJ', 20.0, 100.0, 2)""",

        # Sample Scores (triggers will calculate percentage automatically)
        """INSERT INTO StudentScores (StudentID, ComponentID, Score, MaxPossibleScore, DateCompleted, Status, RecordedBy) VALUES
           (1, 1, 85.0, 100.0, '2023-10-15', 'Completed', 1),
           (1, 2, 92.0, 100.0, '2023-09-30', 'Completed', 1),
           (1, 3, 88.0, 100.0, '2023-10-30', 'Completed', 1),
           (2, 1, 78.0, 100.0, '2023-10-15', 'Completed', 1),
           (2, 2, 85.0, 100.0, '2023-09-30', 'Completed', 1)"""
    ]


def get_evaluation_hierarchy_info() -> Dict[str, Any]:
    """
    Get information about the new evaluation hierarchy structure.

    Returns:
        Dictionary with evaluation hierarchy details
    """
    return {
        'structure': {
            'Course': {
                'description': 'Top level - represents the entire course',
                'table': 'Courses',
                'children': ['Levels']
            },
            'Level': {
                'description': 'Major evaluation categories (e.g., Midterm, Final, Projects)',
                'table': 'Levels',
                'parent': 'Course',
                'children': ['EvaluationGroups']
            },
            'Group': {
                'description': 'Sub-categories within levels (e.g., Written Exams, Lab Work)',
                'table': 'EvaluationGroups',
                'parent': 'Level',
                'children': ['EvaluationComponents']
            },
            'Component': {
                'description': 'Individual assessments (e.g., Quiz 1, Assignment 2)',
                'table': 'EvaluationComponents',
                'parent': 'Group',
                'children': []
            }
        },
        'scoring': {
            'polymorphic': True,
            'description': 'StudentScores table can store scores at any level',
            'constraint': 'Only one of LevelID, GroupID, or ComponentID can be non-null (enforced by application logic)',
            'flexibility': 'Allows scoring at different granularities',
            'mysql57_compatibility': 'Uses triggers instead of generated columns'
        },
        'benefits': [
            'More flexible evaluation structures',
            'Better organization of complex grading schemes',
            'Supports different assessment methodologies',
            'Easier reporting and analysis',
            'Polymorphic scoring for maximum flexibility',
            'MySQL 5.7+ compatible with trigger-based calculations'
        ]
    }


def get_schema_info() -> Dict[str, Any]:
    """
    Get comprehensive schema information.

    Returns:
        Dictionary with schema metadata
    """
    return {
        'total_tables': len(CREATE_TABLE_QUERIES),
        'table_names': list(CREATE_TABLE_QUERIES.keys()),
        'creation_order': TABLE_CREATION_ORDER,
        'drop_order': TABLE_DROP_ORDER,
        'dependencies': validate_table_dependencies(),
        'views_count': len(CREATE_VIEWS),
        'procedures_count': len(CREATE_PROCEDURES),
        'triggers_count': len(CREATE_TRIGGERS),
        'evaluation_structure': {
            'levels': 'Course evaluation levels (e.g., Midterm, Final)',
            'groups': 'Evaluation groups within levels (e.g., Written, Practical)',
            'components': 'Individual components (e.g., Quiz 1, Assignment 2)',
            'polymorphic_scores': 'Flexible scoring at any level'
        },
        'mysql57_compatibility': {
            'version': '5.7',
            'triggers_for_calculated_fields': True,
            'tinyint_for_boolean': True,
            'ifnull_instead_of_coalesce': True
        }
    }


# Export all major functions and constants for easy import
__all__ = [
    # Main interface functions expected by main.py
    'get_creation_queries_by_order',
    'get_drop_queries_by_order',
    'get_trigger_queries',
    'CREATE_VIEWS',
    'CREATE_PROCEDURES',

    # Table management
    'TABLE_CREATION_ORDER',
    'CREATE_TABLE_QUERIES',
    'DROP_TABLE_QUERIES',
    'CREATE_TRIGGERS',

    # Utility functions
    'get_table_creation_query',
    'get_table_drop_query',
    'get_all_table_names',
    'get_table_creation_order',
    'get_table_drop_order',
    'validate_table_dependencies',
    'validate_query_syntax',
    'debug_table_creation_order',

    # Information functions
    'get_mysql57_compatibility_info',
    'get_evaluation_hierarchy_info',
    'get_schema_info',
    'create_sample_evaluation_structure'
]