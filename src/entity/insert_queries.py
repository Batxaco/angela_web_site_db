"""
SQL queries for inserting sample data into the student database.

This module contains all SQL DML (Data Manipulation Language) statements
for inserting test and sample data into the MySQL database tables with
the new hierarchical evaluation structure.
"""

from typing import Dict, List, Any
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

# Sample data insertion queries for all 10 tables
INSERT_SAMPLE_DATA_QUERIES: Dict[str, str] = {
    'Students': """
        INSERT INTO Students (
            FirstName, LastName, Email, DateOfBirth, PhoneNumber, 
            Address, EnrollmentDate, Status
        ) VALUES
        ('John', 'Doe', 'john.doe@student.edu', '2002-05-15', '+1-555-0101', 
         '123 Main St, Anytown, ST 12345', '2023-09-01', 'Active'),
        ('Jane', 'Smith', 'jane.smith@student.edu', '2001-03-22', '+1-555-0102', 
         '456 Oak Ave, Somewhere, ST 12346', '2023-09-01', 'Active'),
        ('Robert', 'Johnson', 'robert.johnson@student.edu', '2000-11-08', '+1-555-0103', 
         '789 Pine Rd, Elsewhere, ST 12347', '2022-09-01', 'Active'),
        ('Emily', 'Davis', 'emily.davis@student.edu', '2002-07-30', '+1-555-0104', 
         '321 Elm St, Nowhere, ST 12348', '2023-09-01', 'Active'),
        ('Michael', 'Wilson', 'michael.wilson@student.edu', '2001-12-14', '+1-555-0105', 
         '654 Maple Dr, Anywhere, ST 12349', '2022-09-01', 'Active'),
        ('Sarah', 'Brown', 'sarah.brown@student.edu', '2003-01-25', '+1-555-0106', 
         '987 Cedar Ln, Someplace, ST 12350', '2023-09-01', 'Active'),
        ('David', 'Garcia', 'david.garcia@student.edu', '2001-09-18', '+1-555-0107', 
         '147 Birch Way, Overthere, ST 12351', '2022-09-01', 'Suspended'),
        ('Lisa', 'Miller', 'lisa.miller@student.edu', '2000-04-03', '+1-555-0108', 
         '258 Spruce Ct, Underthis, ST 12352', '2021-09-01', 'Graduated')
    """,

    'Teachers': """
        INSERT INTO Teachers (
            FirstName, LastName, Email, PhoneNumber, Department, 
            HireDate, Status
        ) VALUES
        ('Dr. Sarah', 'Williams', 'sarah.williams@university.edu', '+1-555-1001', 
         'Computer Science', '2018-08-15', 'Active'),
        ('Prof. Michael', 'Brown', 'michael.brown@university.edu', '+1-555-1002', 
         'Information Systems', '2015-01-10', 'Active'),
        ('Dr. Jennifer', 'Taylor', 'jennifer.taylor@university.edu', '+1-555-1003', 
         'Mathematics', '2020-09-01', 'Active'),
        ('Prof. James', 'Anderson', 'james.anderson@university.edu', '+1-555-1004', 
         'Computer Science', '2017-03-15', 'Active'),
        ('Dr. Patricia', 'Thomas', 'patricia.thomas@university.edu', '+1-555-1005', 
         'Data Science', '2019-06-01', 'Active'),
        ('Prof. Christopher', 'Jackson', 'christopher.jackson@university.edu', '+1-555-1006', 
         'Software Engineering', '2016-11-20', 'On Leave'),
        ('Dr. Maria', 'Rodriguez', 'maria.rodriguez@university.edu', '+1-555-1007', 
         'Computer Science', '2021-02-01', 'Active')
    """,

    'Courses': """
        INSERT INTO Courses (
            CourseLevel, CourseGroup, TeacherID, CourseName, CourseCode, 
            Description, Credits, Semester, AcademicYear, MaxStudents, Status
        ) VALUES
        ('Beginner', 'CS', 1, 'Introduction to Programming', 'CS101', 
         'Basic programming concepts using Python', 3, 'Fall', '2023', 30, 'Active'),
        ('Intermediate', 'CS', 2, 'Database Systems', 'CS201', 
         'Relational database design and SQL', 4, 'Fall', '2023', 25, 'Active'),
        ('Advanced', 'CS', 1, 'Web Development', 'CS301', 
         'Full-stack web development with modern frameworks', 3, 'Spring', '2024', 28, 'Active'),
        ('Intermediate', 'CS', 4, 'Data Structures and Algorithms', 'CS202', 
         'Advanced data structures and algorithmic thinking', 4, 'Spring', '2024', 25, 'Active'),
        ('Advanced', 'DS', 5, 'Machine Learning Fundamentals', 'DS401', 
         'Introduction to machine learning concepts and applications', 3, 'Fall', '2023', 20, 'Active'),
        ('Advanced', 'SE', 6, 'Software Engineering Principles', 'SE301', 
         'Software development lifecycle and engineering practices', 3, 'Fall', '2023', 22, 'Inactive'),
        ('Advanced', 'CS', 2, 'Advanced Database Administration', 'CS401', 
         'Advanced database management and optimization', 3, 'Spring', '2024', 15, 'Active'),
        ('Beginner', 'MATH', 3, 'Calculus I', 'MATH101', 
         'Differential and integral calculus', 4, 'Fall', '2023', 35, 'Active'),
        ('Intermediate', 'STAT', 5, 'Statistics for Data Science', 'STAT201', 
         'Statistical methods for data analysis', 3, 'Spring', '2024', 30, 'Active'),
        ('Intermediate', 'CS', 7, 'Computer Networks', 'CS302', 
         'Network protocols and distributed systems', 3, 'Fall', '2023', 20, 'Active')
    """,

    'Levels': """
        INSERT INTO Levels (
            CourseID, LevelName, LevelCode, Description, Weight, MaxScore, OrderIndex, IsActive
        ) VALUES
        -- CS101: Introduction to Programming
        (1, 'Midterm Evaluations', 'MID', 'Midterm assessment period', 40.0, 100.0, 1, 1),
        (1, 'Final Evaluations', 'FINAL', 'Final assessment period', 60.0, 100.0, 2, 1),
        
        -- CS201: Database Systems  
        (2, 'Continuous Assessment', 'CONT', 'Ongoing assessments throughout semester', 30.0, 100.0, 1, 1),
        (2, 'Project Work', 'PROJ', 'Major project assignments', 40.0, 100.0, 2, 1),
        (2, 'Final Examination', 'FINAL', 'Comprehensive final exam', 30.0, 100.0, 3, 1),
        
        -- CS301: Web Development
        (3, 'Portfolio Projects', 'PORT', 'Web development portfolio', 70.0, 100.0, 1, 1),
        (3, 'Technical Assessment', 'TECH', 'Technical skills evaluation', 30.0, 100.0, 2, 1),
        
        -- CS202: Data Structures and Algorithms
        (4, 'Problem Solving', 'PROB', 'Algorithmic problem solving', 50.0, 100.0, 1, 1),
        (4, 'Implementation Projects', 'IMPL', 'Algorithm implementation projects', 50.0, 100.0, 2, 1),
        
        -- DS401: Machine Learning Fundamentals
        (5, 'Theoretical Understanding', 'THEORY', 'ML theory and concepts', 40.0, 100.0, 1, 1),
        (5, 'Practical Application', 'PRACT', 'Hands-on ML projects', 60.0, 100.0, 2, 1)
    """,

    'EvaluationGroups': """
        INSERT INTO EvaluationGroups (
            LevelID, GroupName, GroupCode, Description, Weight, MaxScore, OrderIndex, IsActive
        ) VALUES
        -- CS101 Midterm Evaluations (LevelID: 1)
        (1, 'Written Examinations', 'WRITTEN', 'Traditional written tests', 70.0, 100.0, 1, 1),
        (1, 'Programming Assignments', 'PROG_ASSIGN', 'Coding assignments', 30.0, 100.0, 2, 1),
        
        -- CS101 Final Evaluations (LevelID: 2)
        (2, 'Final Examination', 'FINAL_EXAM', 'Comprehensive final exam', 80.0, 100.0, 1, 1),
        (2, 'Final Project', 'FINAL_PROJ', 'Capstone programming project', 20.0, 100.0, 2, 1),
        
        -- CS201 Continuous Assessment (LevelID: 3)
        (3, 'Weekly Quizzes', 'QUIZZES', 'Regular knowledge checks', 60.0, 100.0, 1, 1),
        (3, 'Class Participation', 'PARTICIPATION', 'Active class engagement', 40.0, 100.0, 2, 1),
        
        -- CS201 Project Work (LevelID: 4)
        (4, 'Database Design', 'DB_DESIGN', 'Database design projects', 50.0, 100.0, 1, 1),
        (4, 'SQL Implementation', 'SQL_IMPL', 'SQL query and procedure work', 50.0, 100.0, 2, 1),
        
        -- CS201 Final Examination (LevelID: 5)
        (5, 'Written Exam', 'WRITTEN_FINAL', 'Traditional final examination', 100.0, 100.0, 1, 1),
        
        -- CS301 Portfolio Projects (LevelID: 6)
        (6, 'Frontend Development', 'FRONTEND', 'Frontend projects and assignments', 50.0, 100.0, 1, 1),
        (6, 'Backend Development', 'BACKEND', 'Backend and API development', 50.0, 100.0, 2, 1),
        
        -- CS301 Technical Assessment (LevelID: 7)
        (7, 'Technical Interview', 'TECH_INTERVIEW', 'Technical skills interview', 100.0, 100.0, 1, 1)
    """,

    'EvaluationComponents': """
        INSERT INTO EvaluationComponents (
            GroupID, ComponentName, ComponentCode, Description, Weight, MaxScore, OrderIndex, DueDate, IsActive
        ) VALUES
        -- CS101 Midterm Written Examinations (GroupID: 1)
        (1, 'Midterm Exam', 'MID_EXAM', 'Midterm written examination', 100.0, 100.0, 1, '2023-10-15', 1),
        
        -- CS101 Midterm Programming Assignments (GroupID: 2)
        (2, 'Assignment 1: Variables and Types', 'ASSIGN1', 'Basic programming concepts', 30.0, 100.0, 1, '2023-09-20', 1),
        (2, 'Assignment 2: Control Structures', 'ASSIGN2', 'Loops and conditionals', 35.0, 100.0, 2, '2023-10-05', 1),
        (2, 'Assignment 3: Functions', 'ASSIGN3', 'Function definition and usage', 35.0, 100.0, 3, '2023-10-20', 1),
        
        -- CS101 Final Examination (GroupID: 3)
        (3, 'Final Exam', 'FINAL_EXAM', 'Comprehensive final examination', 100.0, 100.0, 1, '2023-12-15', 1),
        
        -- CS101 Final Project (GroupID: 4)
        (4, 'Final Programming Project', 'FINAL_PROJECT', 'Complete programming application', 100.0, 100.0, 1, '2023-12-10', 1),
        
        -- CS201 Weekly Quizzes (GroupID: 5)
        (5, 'Quiz 1: Database Fundamentals', 'QUIZ1', 'Basic database concepts', 25.0, 100.0, 1, '2023-09-15', 1),
        (5, 'Quiz 2: SQL Basics', 'QUIZ2', 'Basic SQL queries', 25.0, 100.0, 2, '2023-09-29', 1),
        (5, 'Quiz 3: Advanced SQL', 'QUIZ3', 'Complex queries and joins', 25.0, 100.0, 3, '2023-10-13', 1),
        (5, 'Quiz 4: Database Design', 'QUIZ4', 'Normalization and design', 25.0, 100.0, 4, '2023-10-27', 1),
        
        -- CS201 Class Participation (GroupID: 6)
        (6, 'Attendance and Engagement', 'ATTENDANCE', 'Regular class attendance and participation', 100.0, 100.0, 1, '2023-12-01', 1),
        
        -- CS201 Database Design (GroupID: 7)
        (7, 'ER Diagram Project', 'ER_DIAGRAM', 'Entity-relationship diagram design', 40.0, 100.0, 1, '2023-10-31', 1),
        (7, 'Schema Design Project', 'SCHEMA_DESIGN', 'Complete database schema', 60.0, 100.0, 2, '2023-11-15', 1),
        
        -- CS201 SQL Implementation (GroupID: 8)
        (8, 'Query Portfolio', 'QUERY_PORT', 'Collection of SQL queries', 50.0, 100.0, 1, '2023-11-30', 1),
        (8, 'Stored Procedures Project', 'STORED_PROC', 'Database procedures and functions', 50.0, 100.0, 2, '2023-12-05', 1),
        
        -- CS201 Written Final (GroupID: 9)
        (9, 'Database Final Exam', 'DB_FINAL', 'Comprehensive database examination', 100.0, 100.0, 1, '2023-12-18', 1),
        
        -- CS301 Frontend Development (GroupID: 10)
        (10, 'HTML/CSS Project', 'HTML_CSS', 'Static website project', 30.0, 100.0, 1, '2024-02-15', 1),
        (10, 'JavaScript Application', 'JS_APP', 'Interactive web application', 40.0, 100.0, 2, '2024-03-01', 1),
        (10, 'React Component Library', 'REACT_LIB', 'Reusable React components', 30.0, 100.0, 3, '2024-03-15', 1),
        
        -- CS301 Backend Development (GroupID: 11)
        (11, 'REST API Project', 'REST_API', 'RESTful web service', 50.0, 100.0, 1, '2024-03-30', 1),
        (11, 'Database Integration', 'DB_INTEGRATION', 'Full-stack database integration', 50.0, 100.0, 2, '2024-04-15', 1),
        
        -- CS301 Technical Interview (GroupID: 12)
        (12, 'Live Coding Assessment', 'LIVE_CODING', 'Real-time programming evaluation', 100.0, 100.0, 1, '2024-04-30', 1)
    """,

    'StudentScores': """
        INSERT INTO StudentScores (
            StudentID, LevelID, GroupID, ComponentID, Score, MaxPossibleScore, 
            DateCompleted, Status, Notes, Feedback, RecordedBy
        ) VALUES
        -- John Doe (StudentID: 1) - CS101 Scores
        (1, NULL, NULL, 1, 85.0, 100.0, '2023-10-15', 'Completed', 'Good performance on midterm', 'Solid understanding of basic concepts', 1),
        (1, NULL, NULL, 2, 92.0, 100.0, '2023-09-20', 'Completed', 'Excellent first assignment', 'Perfect variable usage', 1),
        (1, NULL, NULL, 3, 78.0, 100.0, '2023-10-05', 'Completed', 'Some issues with loops', 'Review nested loop concepts', 1),
        (1, NULL, NULL, 4, 88.0, 100.0, '2023-10-20', 'Completed', 'Good function implementation', 'Clean code structure', 1),
        (1, NULL, NULL, 5, 90.0, 100.0, '2023-12-15', 'Completed', 'Strong final exam performance', 'Comprehensive understanding shown', 1),
        (1, NULL, NULL, 6, 95.0, 100.0, '2023-12-10', 'Completed', 'Outstanding final project', 'Creative and well-implemented solution', 1),
        
        -- Jane Smith (StudentID: 2) - CS101 Scores
        (2, NULL, NULL, 1, 94.0, 100.0, '2023-10-15', 'Completed', 'Excellent midterm performance', 'Top of class performance', 1),
        (2, NULL, NULL, 2, 98.0, 100.0, '2023-09-20', 'Completed', 'Perfect assignment', 'Exceptional coding style', 1),
        (2, NULL, NULL, 3, 89.0, 100.0, '2023-10-05', 'Completed', 'Very good control structures', 'Minor optimization suggestions', 1),
        (2, NULL, NULL, 4, 96.0, 100.0, '2023-10-20', 'Completed', 'Excellent functions work', 'Advanced concepts mastered', 1),
        
        -- Robert Johnson (StudentID: 3) - CS201 Scores
        (3, NULL, NULL, 7, 82.0, 100.0, '2023-09-15', 'Completed', 'Good database fundamentals', 'Solid foundation understanding', 2),
        (3, NULL, NULL, 8, 75.0, 100.0, '2023-09-29', 'Completed', 'Basic SQL needs improvement', 'Practice more complex queries', 2),
        (3, NULL, NULL, 9, 88.0, 100.0, '2023-10-13', 'Completed', 'Much improved on advanced SQL', 'Good progress shown', 2),
        (3, NULL, NULL, 10, 79.0, 100.0, '2023-10-27', 'Completed', 'Database design understanding', 'Normalization concepts grasped', 2),
        (3, NULL, NULL, 12, 85.0, 100.0, '2023-10-31', 'Completed', 'Good ER diagram work', 'Clear entity relationships', 2),
        (3, NULL, NULL, 13, 91.0, 100.0, '2023-11-15', 'Completed', 'Excellent schema design', 'Well-structured database', 2),
        
        -- Emily Davis (StudentID: 4) - CS301 Scores
        (4, NULL, NULL, 16, 87.0, 100.0, '2024-02-15', 'Completed', 'Good HTML/CSS skills', 'Clean and semantic markup', 1),
        (4, NULL, NULL, 17, 93.0, 100.0, '2024-03-01', 'Completed', 'Excellent JavaScript work', 'Advanced DOM manipulation', 1),
        (4, NULL, NULL, 18, 89.0, 100.0, '2024-03-15', 'Completed', 'Good React components', 'Reusable and well-documented', 1),
        (4, NULL, NULL, 19, 85.0, 100.0, '2024-03-30', 'Completed', 'Solid REST API implementation', 'Good error handling', 1),
        
        -- Michael Wilson (StudentID: 5) - Mixed courses
        (5, NULL, NULL, 1, 76.0, 100.0, '2023-10-15', 'Completed', 'Struggled with midterm', 'Needs additional practice', 1),
        (5, NULL, NULL, 2, 82.0, 100.0, '2023-09-20', 'Completed', 'Improvement shown', 'Better understanding developed', 1),
        (5, NULL, NULL, 7, 89.0, 100.0, '2023-09-15', 'Completed', 'Strong database concepts', 'Natural aptitude for databases', 2),
        (5, NULL, NULL, 8, 91.0, 100.0, '2023-09-29', 'Completed', 'Excellent SQL skills', 'Advanced query techniques', 2),
        
        -- Sarah Brown (StudentID: 6) - Various scores
        (6, NULL, NULL, 1, 88.0, 100.0, '2023-10-15', 'Completed', 'Good midterm result', 'Consistent performance', 1),
        (6, NULL, NULL, 2, 95.0, 100.0, '2023-09-20', 'Completed', 'Excellent programming', 'Innovative approach', 1),
        (6, NULL, NULL, 16, 92.0, 100.0, '2024-02-15', 'Completed', 'Outstanding frontend work', 'Creative design solutions', 1),
        
        -- Level and Group aggregate scores (examples)
        (1, 1, NULL, NULL, 86.5, 100.0, '2023-10-30', 'Completed', 'Midterm level aggregate', 'Overall good midterm performance', 1),
        (2, 1, NULL, NULL, 92.0, 100.0, '2023-10-30', 'Completed', 'Midterm level aggregate', 'Excellent midterm overall', 1),
        (3, 3, NULL, NULL, 81.0, 100.0, '2023-11-15', 'Completed', 'Continuous assessment aggregate', 'Steady improvement pattern', 2),
        (1, NULL, 2, NULL, 86.0, 100.0, '2023-10-25', 'Completed', 'Programming assignments group', 'Strong programming skills', 1),
        (2, NULL, 2, NULL, 94.3, 100.0, '2023-10-25', 'Completed', 'Programming assignments group', 'Exceptional programming ability', 1)
    """,

    'Grades': """
        INSERT INTO Grades (
            StudentID, CourseID, FinalGrade, LetterGrade, GradePoints, 
            Semester, AcademicYear, Status, DateAssigned, Comments
        ) VALUES
        -- Fall 2023 Final Grades
        (1, 1, 87.5, 'B+', 3.33, 'Fall', '2023', 'Final', '2023-12-20', 'Good progress in programming fundamentals'),
        (2, 1, 93.2, 'A-', 3.67, 'Fall', '2023', 'Final', '2023-12-20', 'Excellent understanding of programming concepts'),
        (3, 2, 83.7, 'B', 3.00, 'Fall', '2023', 'Final', '2023-12-20', 'Solid database skills developed'),
        (4, 1, 85.8, 'B+', 3.33, 'Fall', '2023', 'Final', '2023-12-20', 'Strong programming foundation'),
        (5, 1, 79.2, 'C+', 2.33, 'Fall', '2023', 'Final', '2023-12-20', 'Improvement needed in advanced concepts'),
        (6, 1, 91.5, 'A-', 3.67, 'Fall', '2023', 'Final', '2023-12-20', 'Excellent programming skills'),
        (1, 8, 76.5, 'C+', 2.33, 'Fall', '2023', 'Final', '2023-12-20', 'Mathematics requires more practice'),
        (2, 8, 94.2, 'A', 4.00, 'Fall', '2023', 'Final', '2023-12-20', 'Outstanding mathematical ability'),
        (7, 2, 68.5, 'D+', 1.33, 'Fall', '2023', 'Final', '2023-12-20', 'Poor attendance impacted performance'),
        (5, 2, 88.9, 'B+', 3.33, 'Fall', '2023', 'Final', '2023-12-20', 'Strong database understanding'),
        
        -- Spring 2024 Provisional Grades
        (4, 3, 89.3, 'B+', 3.33, 'Spring', '2024', 'Provisional', '2024-05-15', 'Excellent web development portfolio'),
        (1, 4, 82.1, 'B-', 2.67, 'Spring', '2024', 'Provisional', '2024-05-15', 'Data structures concepts grasped'),
        (2, 4, 91.8, 'A-', 3.67, 'Spring', '2024', 'Provisional', '2024-05-15', 'Outstanding algorithmic thinking'),
        (3, 7, 84.5, 'B', 3.00, 'Spring', '2024', 'Provisional', '2024-05-15', 'Good database administration skills'),
        (5, 9, 87.3, 'B+', 3.33, 'Spring', '2024', 'Provisional', '2024-05-15', 'Applied statistics well'),
        (6, 9, 92.7, 'A-', 3.67, 'Spring', '2024', 'Provisional', '2024-05-15', 'Excellent statistical analysis'),
        
        -- Previous academic year grades
        (8, 1, 95.5, 'A', 4.00, 'Fall', '2021', 'Final', '2021-12-15', 'Exceptional programming talent'),
        (8, 2, 93.2, 'A-', 3.67, 'Spring', '2022', 'Final', '2022-05-15', 'Strong database skills'),
        (8, 3, 89.8, 'B+', 3.33, 'Fall', '2022', 'Final', '2022-12-15', 'Good web development project'),
        (8, 4, 92.7, 'A-', 3.67, 'Spring', '2023', 'Final', '2023-05-15', 'Excellent algorithmic problem solving')
    """,

    'Tutorials': """
        INSERT INTO Tutorials (
            StudentID, TeacherID, CourseID, Date, StartTime, EndTime, 
            Topic, Description, Status, Location, TutorialType, Notes
        ) VALUES
        (1, 1, 1, '2023-09-25', '14:00:00', '15:00:00', 
         'Python Basics', 'Review of variables and data types', 'Completed', 'Office CS-201', 'Individual', 
         'Student needed clarification on variable scope'),
        (1, 1, 1, '2023-10-10', '14:00:00', '15:00:00', 
         'Control Structures', 'Help with loops and conditionals', 'Completed', 'Office CS-201', 'Individual', 
         'Improved understanding of nested loops'),
        (2, 2, 2, '2023-10-05', '10:00:00', '11:30:00', 
         'SQL Joins', 'Advanced join operations', 'Completed', 'Lab CS-301', 'Individual', 
         'Student mastered complex joins'),
        (3, 2, 2, '2023-10-20', '15:00:00', '16:00:00', 
         'Database Normalization', 'Review of normal forms', 'Completed', 'Office CS-205', 'Individual', 
         'Helped with 3NF conversion'),
        (4, 1, 3, '2024-02-14', '13:00:00', '14:30:00', 
         'JavaScript DOM', 'DOM manipulation techniques', 'Completed', 'Lab CS-302', 'Individual', 
         'Good progress with event handling'),
        (5, 5, 5, '2023-11-15', '16:00:00', '17:00:00', 
         'ML Algorithms', 'Linear regression explanation', 'Completed', 'Office DS-101', 'Individual', 
         'Mathematical concepts clarified'),
        (6, 3, 8, '2023-10-30', '11:00:00', '12:00:00', 
         'Calculus Integration', 'Integration by parts method', 'Completed', 'Office MATH-204', 'Individual', 
         'Student showed improvement'),
        (7, 2, 2, '2023-11-01', '14:00:00', '15:00:00', 
         'SQL Review', 'Basic query structure review', 'No Show', 'Office CS-205', 'Individual', 
         'Student did not attend scheduled session'),
        -- Group tutorials
        (1, 1, 1, '2023-11-20', '15:00:00', '16:30:00', 
         'Final Exam Prep', 'Group review session for final exam', 'Completed', 'Classroom CS-101', 'Group', 
         'Beneficial group discussion'),
        (2, 1, 1, '2023-11-20', '15:00:00', '16:30:00', 
         'Final Exam Prep', 'Group review session for final exam', 'Completed', 'Classroom CS-101', 'Group', 
         'Active participation in group session'),
        (4, 1, 1, '2023-11-20', '15:00:00', '16:30:00', 
         'Final Exam Prep', 'Group review session for final exam', 'Completed', 'Classroom CS-101', 'Group', 
         'Helped other students with concepts'),
        -- Online tutorials
        (5, 5, 5, '2023-12-01', '19:00:00', '20:00:00', 
         'ML Project Help', 'Assistance with final project', 'Completed', 'Zoom Meeting', 'Online', 
         'Screen sharing was very helpful'),
        (6, 5, 9, '2024-03-10', '18:00:00', '19:00:00', 
         'Statistical Testing', 'Hypothesis testing review', 'Scheduled', 'Zoom Meeting', 'Online', 
         'Upcoming session for midterm prep'),
        (3, 2, 2, '2023-11-30', '16:00:00', '17:30:00', 
         'Database Design Review', 'Final project consultation', 'Completed', 'Office CS-205', 'Individual', 
         'Excellent progress on database design'),
        (4, 1, 3, '2024-03-20', '14:00:00', '15:30:00', 
         'React Components', 'Advanced React patterns', 'Completed', 'Lab CS-302', 'Individual', 
         'Complex state management concepts clarified'),
        (1, 4, 4, '2024-04-05', '13:00:00', '14:00:00', 
         'Algorithm Optimization', 'Time complexity analysis', 'Completed', 'Office CS-210', 'Individual', 
         'Big O notation understanding improved')
    """,

    'Bans': """
        INSERT INTO Bans (
            StudentID, BanType, Category, Severity, StartDate, EndDate, 
            Reason, Description, IssuedBy, Resolution, ResolutionDate, AppealStatus
        ) VALUES
        (7, 'Academic Probation', 'Academic', 'Major', '2023-12-15', '2024-05-15', 
         'Low GPA', 'GPA fell below 2.0 minimum requirement for two consecutive semesters', 2, 
         'Must maintain 2.5 GPA in spring semester and complete academic success workshop', '2024-01-15', 'None'),
        (7, 'Library Privileges Suspended', 'Administrative', 'Minor', '2023-10-01', '2023-11-01', 
         'Overdue Materials', 'Multiple overdue library books and unpaid fines totaling $45', 3, 
         'All materials returned and fines paid in full', '2023-10-25', 'None'),
        (3, 'Late Assignment Warning', 'Academic', 'Warning', '2023-11-15', NULL, 
         'Chronic Late Submissions', 'Submitted 4 out of 6 assignments past the deadline without prior approval', 1, 
         NULL, NULL, 'None'),
        (6, 'Parking Violation', 'Administrative', 'Minor', '2023-09-20', '2023-10-20', 
         'Unauthorized Parking', 'Vehicle found parked in faculty reserved space without permit', 4, 
         'Parking fine paid and campus parking regulations reviewed', '2023-09-25', 'None'),
        (5, 'Lab Equipment Damage', 'Administrative', 'Minor', '2023-10-15', '2023-11-15', 
         'Equipment Misuse', 'Damaged computer monitor in CS lab due to improper handling', 1, 
         'Replacement cost paid and lab safety training completed', '2023-10-30', 'None'),
        -- Historical ban for graduated student
        (8, 'Academic Integrity Warning', 'Academic', 'Warning', '2021-10-01', '2021-11-01', 
         'Suspected Plagiarism', 'Similarities found in programming assignment code with online sources', 1, 
         'Completed academic integrity workshop and rewrote assignment', '2021-10-15', 'None'),
        -- Active severe ban
        (7, 'Campus Access Restricted', 'Disciplinary', 'Severe', '2024-01-15', '2024-06-15', 
         'Academic Misconduct', 'Caught using unauthorized materials during database systems final examination', 2, 
         NULL, NULL, 'Pending'),
        (1, 'Computer Lab Warning', 'Administrative', 'Warning', '2023-09-10', '2023-09-17', 
         'Lab Policy Violation', 'Found eating food in computer lab during programming session', 1, 
         'Reviewed lab policies and agreed to compliance', '2023-09-12', 'None'),
        (2, 'Research Ethics Training Required', 'Academic', 'Minor', '2024-02-01', '2024-03-01', 
         'Research Protocol Violation', 'Failed to complete required ethics training before starting research project', 5, 
         'Completed online ethics training certification', '2024-02-15', 'None'),
        (4, 'Network Usage Warning', 'Administrative', 'Warning', '2024-01-20', '2024-01-27', 
         'Bandwidth Misuse', 'Excessive network usage for non-academic streaming during class hours', 7, 
         'Agreed to appropriate network usage guidelines', '2024-01-22', 'None')
    """
}

# Bulk insert templates for efficient data loading
BULK_INSERT_TEMPLATES: Dict[str, str] = {
    'Students': """
        INSERT INTO Students (
            FirstName, LastName, Email, DateOfBirth, PhoneNumber, 
            Address, EnrollmentDate, Status
        ) VALUES %s
    """,

    'Teachers': """
        INSERT INTO Teachers (
            FirstName, LastName, Email, PhoneNumber, Department, 
            HireDate, Status
        ) VALUES %s
    """,

    'Courses': """
        INSERT INTO Courses (
            CourseLevel, CourseGroup, TeacherID, CourseName, CourseCode, 
            Description, Credits, Semester, AcademicYear, MaxStudents, Status
        ) VALUES %s
    """,

    'Levels': """
        INSERT INTO Levels (
            CourseID, LevelName, LevelCode, Description, Weight, MaxScore, OrderIndex, IsActive
        ) VALUES %s
    """,

    'EvaluationGroups': """
        INSERT INTO EvaluationGroups (
            LevelID, GroupName, GroupCode, Description, Weight, MaxScore, OrderIndex, IsActive
        ) VALUES %s
    """,

    'EvaluationComponents': """
        INSERT INTO EvaluationComponents (
            GroupID, ComponentName, ComponentCode, Description, Weight, MaxScore, OrderIndex, DueDate, IsActive
        ) VALUES %s
    """,

    'StudentScores': """
        INSERT INTO StudentScores (
            StudentID, LevelID, GroupID, ComponentID, Score, MaxPossibleScore, 
            DateCompleted, Status, Notes, Feedback, RecordedBy
        ) VALUES %s
    """,

    'Grades': """
        INSERT INTO Grades (
            StudentID, CourseID, FinalGrade, LetterGrade, GradePoints, 
            Semester, AcademicYear, Status, DateAssigned, Comments
        ) VALUES %s
    """,

    'Tutorials': """
        INSERT INTO Tutorials (
            StudentID, TeacherID, CourseID, Date, StartTime, EndTime, 
            Topic, Description, Status, Location, TutorialType, Notes
        ) VALUES %s
    """,

    'Bans': """
        INSERT INTO Bans (
            StudentID, BanType, Category, Severity, StartDate, EndDate, 
            Reason, Description, IssuedBy, Resolution, ResolutionDate, AppealStatus
        ) VALUES %s
    """
}

# Sample data for bulk operations and testing
SAMPLE_DATA: Dict[str, List[tuple]] = {
    'additional_students': [
        ('Alexander', 'Thompson', 'alex.thompson@student.edu', '2002-03-12', '+1-555-0201',
         '111 First St, Town, ST 12401', '2023-09-01', 'Active'),
        ('Olivia', 'Martinez', 'olivia.martinez@student.edu', '2001-08-25', '+1-555-0202',
         '222 Second Ave, City, ST 12402', '2023-09-01', 'Active'),
        ('William', 'Anderson', 'william.anderson@student.edu', '2002-11-03', '+1-555-0203',
         '333 Third Blvd, Village, ST 12403', '2022-09-01', 'Active'),
        ('Sophia', 'Taylor', 'sophia.taylor@student.edu', '2001-06-18', '+1-555-0204',
         '444 Fourth St, Hamlet, ST 12404', '2023-09-01', 'Active'),
        ('James', 'Wilson', 'james.wilson@student.edu', '2000-09-07', '+1-555-0205',
         '555 Fifth Ave, Borough, ST 12405', '2021-09-01', 'Active')
    ],

    'additional_courses': [
        ('Beginner', 'CS', 1, 'Object-Oriented Programming', 'CS102',
         'Advanced programming with OOP concepts', 3, 'Spring', '2024', 25, 'Active'),
        ('Advanced', 'CS', 4, 'Computer Graphics', 'CS303',
         'Introduction to 2D and 3D graphics programming', 3, 'Fall', '2024', 20, 'Active'),
        ('Advanced', 'AI', 5, 'Artificial Intelligence', 'CS402',
         'AI algorithms and applications', 4, 'Spring', '2024', 18, 'Active'),
        ('Intermediate', 'CS', 1, 'Mobile App Development', 'CS304',
         'iOS and Android application development', 3, 'Fall', '2024', 22, 'Active'),
        ('Intermediate', 'CS', 7, 'Cybersecurity Fundamentals', 'CS305',
         'Network security and cryptography basics', 3, 'Spring', '2024', 25, 'Active')
    ],

    'additional_evaluation_components': [
        # Additional components for more comprehensive evaluation
        ('Quiz 5: Optimization', 'QUIZ5', 'Database optimization techniques', 25.0, 100.0, 5, '2023-11-10', 1),
        ('Project Defense', 'PROJ_DEFENSE', 'Oral presentation of final project', 20.0, 100.0, 1, '2023-12-12', 1),
        ('Peer Review Assignment', 'PEER_REVIEW', 'Code review and feedback exercise', 15.0, 100.0, 4, '2023-11-25', 1),
        ('Lab Practical Exam', 'LAB_PRACTICAL', 'Hands-on programming assessment', 30.0, 100.0, 1, '2023-12-08', 1)
    ]
}

def get_insert_query(table_name: str) -> str:
    """
    Get the sample data insertion query for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        SQL INSERT query with sample data

    Raises:
        KeyError: If table name is not found
    """
    if table_name not in INSERT_SAMPLE_DATA_QUERIES:
        raise KeyError(f"No sample data query found for table: {table_name}")

    return INSERT_SAMPLE_DATA_QUERIES[table_name]


def get_bulk_insert_template(table_name: str) -> str:
    """
    Get the bulk insert template for a specific table.

    Args:
        table_name: Name of the table

    Returns:
        SQL INSERT template for bulk operations

    Raises:
        KeyError: If table name is not found
    """
    if table_name not in BULK_INSERT_TEMPLATES:
        raise KeyError(f"No bulk insert template found for table: {table_name}")

    return BULK_INSERT_TEMPLATES[table_name]


def get_sample_data(data_set: str) -> List[tuple]:
    """
    Get sample data for bulk operations.

    Args:
        data_set: Name of the data set

    Returns:
        List of tuples containing sample data

    Raises:
        KeyError: If data set name is not found
    """
    if data_set not in SAMPLE_DATA:
        raise KeyError(f"No sample data found for: {data_set}")

    return SAMPLE_DATA[data_set]


def get_insert_order() -> List[str]:
    """
    Get the order in which tables should be populated.
    Respects foreign key dependencies.

    Returns:
        List of table names in insertion order
    """
    return [
        'Students', 'Teachers', 'Courses', 'Levels', 'EvaluationGroups',
        'EvaluationComponents', 'StudentScores', 'Grades', 'Tutorials', 'Bans'
    ]


def validate_sample_data() -> Dict[str, bool]:
    """
    Validate that all required tables have sample data.

    Returns:
        Dictionary mapping table names to data availability
    """
    required_tables = get_insert_order()
    validation_results = {}

    for table in required_tables:
        validation_results[table] = table in INSERT_SAMPLE_DATA_QUERIES

    logger.debug(f"Sample data validation: {validation_results}")
    return validation_results


def get_hierarchical_sample_data() -> Dict[str, Any]:
    """
    Get sample data that demonstrates the hierarchical evaluation structure.

    Returns:
        Dictionary with hierarchical sample data examples
    """
    return {
        'course_structure_example': {
            'course': 'CS101 - Introduction to Programming',
            'levels': [
                {
                    'name': 'Midterm Evaluations',
                    'weight': 40.0,
                    'groups': [
                        {
                            'name': 'Written Examinations',
                            'weight': 70.0,
                            'components': ['Midterm Exam']
                        },
                        {
                            'name': 'Programming Assignments',
                            'weight': 30.0,
                            'components': ['Assignment 1', 'Assignment 2', 'Assignment 3']
                        }
                    ]
                },
                {
                    'name': 'Final Evaluations',
                    'weight': 60.0,
                    'groups': [
                        {
                            'name': 'Final Examination',
                            'weight': 80.0,
                            'components': ['Final Exam']
                        },
                        {
                            'name': 'Final Project',
                            'weight': 20.0,
                            'components': ['Final Programming Project']
                        }
                    ]
                }
            ]
        },
        'scoring_examples': {
            'component_level': 'Individual assignment or exam scores',
            'group_level': 'Aggregate scores for assignment groups or exam categories',
            'level_level': 'Aggregate scores for major evaluation periods',
            'polymorphic_scoring': 'Can score at any level depending on assessment needs'
        }
    }


def generate_random_students(count: int) -> List[tuple]:
    """
    Generate random student data for testing.

    Args:
        count: Number of students to generate

    Returns:
        List of tuples with student data
    """
    import random
    from datetime import datetime, timedelta

    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily',
                   'James', 'Jessica', 'William', 'Ashley', 'Christopher', 'Amanda', 'Daniel',
                   'Alexander', 'Olivia', 'Matthew', 'Sophia', 'Andrew']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
                  'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
                  'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

    students = []
    base_date = datetime(2000, 1, 1)

    for i in range(count):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}{i+100}@student.edu"

        # Random birth date between 2000-2003
        birth_date = base_date + timedelta(days=random.randint(0, 1095))

        phone = f"+1-555-{random.randint(1000, 9999):04d}"
        address = f"{random.randint(100, 999)} Random St, City, ST {random.randint(10000, 99999)}"

        # Random enrollment date
        enrollment_years = [2021, 2022, 2023, 2024]
        enrollment_date = f"{random.choice(enrollment_years)}-09-01"

        status = random.choice(['Active', 'Active', 'Active', 'Active', 'Inactive'])  # 80% active

        students.append((
            first_name, last_name, email, birth_date.strftime('%Y-%m-%d'),
            phone, address, enrollment_date, status
        ))

    return students


def generate_evaluation_structure_sample(course_id: int, course_name: str) -> Dict[str, List[str]]:
    """
    Generate sample evaluation structure queries for a specific course.

    Args:
        course_id: Course ID for the evaluation structure
        course_name: Name of the course

    Returns:
        Dictionary with SQL queries for levels, groups, and components
    """
    queries = {
        'levels': [
            f"""INSERT INTO Levels (CourseID, LevelName, LevelCode, Weight, OrderIndex) VALUES 
               ({course_id}, 'Continuous Assessment', 'CONT', 40.0, 1),
               ({course_id}, 'Major Projects', 'PROJ', 35.0, 2),
               ({course_id}, 'Final Evaluation', 'FINAL', 25.0, 3)"""
        ],
        'groups': [
            f"""INSERT INTO EvaluationGroups (LevelID, GroupName, Weight, OrderIndex) VALUES 
               ((SELECT LevelID FROM Levels WHERE CourseID = {course_id} AND LevelCode = 'CONT'), 'Weekly Quizzes', 60.0, 1),
               ((SELECT LevelID FROM Levels WHERE CourseID = {course_id} AND LevelCode = 'CONT'), 'Lab Work', 40.0, 2),
               ((SELECT LevelID FROM Levels WHERE CourseID = {course_id} AND LevelCode = 'PROJ'), 'Individual Projects', 70.0, 1),
               ((SELECT LevelID FROM Levels WHERE CourseID = {course_id} AND LevelCode = 'PROJ'), 'Group Projects', 30.0, 2),
               ((SELECT LevelID FROM Levels WHERE CourseID = {course_id} AND LevelCode = 'FINAL'), 'Final Exam', 100.0, 1)"""
        ],
        'components': [
            f"""INSERT INTO EvaluationComponents (GroupID, ComponentName, Weight, MaxScore, OrderIndex) VALUES 
               ((SELECT g.GroupID FROM EvaluationGroups g JOIN Levels l ON g.LevelID = l.LevelID 
                 WHERE l.CourseID = {course_id} AND g.GroupName = 'Weekly Quizzes'), 'Quiz 1', 25.0, 100.0, 1),
               ((SELECT g.GroupID FROM EvaluationGroups g JOIN Levels l ON g.LevelID = l.LevelID 
                 WHERE l.CourseID = {course_id} AND g.GroupName = 'Weekly Quizzes'), 'Quiz 2', 25.0, 100.0, 2),
               ((SELECT g.GroupID FROM EvaluationGroups g JOIN Levels l ON g.LevelID = l.LevelID 
                 WHERE l.CourseID = {course_id} AND g.GroupName = 'Individual Projects'), 'Project 1', 100.0, 100.0, 1)"""
        ]
    }

    return queries


def create_comprehensive_sample_data() -> List[str]:
    """
    Create comprehensive sample data that demonstrates all features of the hierarchical system.

    Returns:
        List of SQL statements for comprehensive sample data
    """
    return [
        # Additional students for testing
        """INSERT INTO Students (FirstName, LastName, Email, DateOfBirth, Status) VALUES 
           ('Test', 'Student1', 'test.student1@example.edu', '2002-01-01', 'Active'),
           ('Test', 'Student2', 'test.student2@example.edu', '2002-02-02', 'Active'),
           ('Test', 'Student3', 'test.student3@example.edu', '2002-03-03', 'Active')""",

        # Sample scores at different levels to demonstrate polymorphic scoring
        """INSERT INTO StudentScores (StudentID, LevelID, Score, MaxPossibleScore, Status, Notes) VALUES 
           (9, 1, 85.0, 100.0, 'Completed', 'Level aggregate score for Midterm Evaluations'),
           (10, 1, 92.0, 100.0, 'Completed', 'Level aggregate score for Midterm Evaluations')""",

        """INSERT INTO StudentScores (StudentID, GroupID, Score, MaxPossibleScore, Status, Notes) VALUES 
           (9, 1, 88.0, 100.0, 'Completed', 'Group aggregate for Written Examinations'),
           (10, 2, 90.0, 100.0, 'Completed', 'Group aggregate for Programming Assignments')""",

        # Demonstrate the trigger functionality
        """INSERT INTO StudentScores (StudentID, ComponentID, Score, MaxPossibleScore, Status, Notes) VALUES 
           (11, 1, 75.0, 100.0, 'Completed', 'Percentage will be calculated automatically by trigger')"""
    ]


def get_table_count_by_type() -> Dict[str, int]:
    """
    Get count of records per table type for validation.

    Returns:
        Dictionary with expected record counts per table
    """
    return {
        'Students': 8,
        'Teachers': 7,
        'Courses': 10,
        'Levels': 11,
        'EvaluationGroups': 12,
        'EvaluationComponents': 21,
        'StudentScores': 30,
        'Grades': 20,
        'Tutorials': 16,
        'Bans': 10
    }


def verify_hierarchical_integrity() -> List[str]:
    """
    Generate validation queries to check hierarchical data integrity.

    Returns:
        List of SQL validation queries
    """
    return [
        # Check that all levels belong to valid courses
        """SELECT 'Levels without valid courses' as check_type, COUNT(*) as count
           FROM Levels l LEFT JOIN Courses c ON l.CourseID = c.CourseID 
           WHERE c.CourseID IS NULL""",

        # Check that all groups belong to valid levels
        """SELECT 'Groups without valid levels' as check_type, COUNT(*) as count
           FROM EvaluationGroups eg LEFT JOIN Levels l ON eg.LevelID = l.LevelID 
           WHERE l.LevelID IS NULL""",

        # Check that all components belong to valid groups
        """SELECT 'Components without valid groups' as check_type, COUNT(*) as count
           FROM EvaluationComponents ec LEFT JOIN EvaluationGroups eg ON ec.GroupID = eg.GroupID 
           WHERE eg.GroupID IS NULL""",

        # Check polymorphic scoring constraint
        """SELECT 'Invalid polymorphic scores' as check_type, COUNT(*) as count
           FROM StudentScores 
           WHERE (LevelID IS NOT NULL AND (GroupID IS NOT NULL OR ComponentID IS NOT NULL))
              OR (GroupID IS NOT NULL AND (LevelID IS NOT NULL OR ComponentID IS NOT NULL))
              OR (ComponentID IS NOT NULL AND (LevelID IS NOT NULL OR GroupID IS NOT NULL))""",

        # Check trigger functionality (percentage calculation)
        """SELECT 'Scores with missing percentages' as check_type, COUNT(*) as count
           FROM StudentScores 
           WHERE Score IS NOT NULL AND MaxPossibleScore > 0 AND Percentage IS NULL"""
    ]


# Export all functions for easy access
__all__ = [
    'INSERT_SAMPLE_DATA_QUERIES',
    'BULK_INSERT_TEMPLATES',
    'SAMPLE_DATA',
    'get_insert_query',
    'get_bulk_insert_template',
    'get_sample_data',
    'get_insert_order',
    'validate_sample_data',
    'get_hierarchical_sample_data',
    'generate_random_students',
    'generate_evaluation_structure_sample',
    'create_comprehensive_sample_data',
    'get_table_count_by_type',
    'verify_hierarchical_integrity'
]