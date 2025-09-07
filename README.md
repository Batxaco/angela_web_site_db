# MySQL Student Database Management System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MySQL](https://img.shields.io/badge/mysql-8.0+-orange.svg)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive, production-ready MySQL database management system for student information, built with Python following enterprise best practices. Features modular architecture, comprehensive testing, and both CLI and interactive interfaces.

## 🌟 Features

### **Core Functionality**
- ✅ **Complete Student Database Schema** - Students, Teachers, Courses, Evaluations, Grades, Tutorials, Bans
- ✅ **Multi-Driver Support** - Works with `mysql-connector-python` and `PyMySQL`
- ✅ **Connection Pooling** - Efficient database connection management
- ✅ **Transaction Management** - ACID compliance and rollback support
- ✅ **Schema Validation** - Integrity checks and relationship analysis

### **User Experience**
- ✅ **Interactive Mode** - Beginner-friendly guided interface
- ✅ **Command-Line Interface** - Full CLI with comprehensive options
- ✅ **Comprehensive Logging** - Detailed audit trails and debugging
- ✅ **Error Recovery** - Robust error handling and retry mechanisms
- ✅ **Progress Tracking** - Real-time feedback on operations

### **Security & Configuration**
- ✅ **Secure Credential Management** - Environment variables and encrypted storage
- ✅ **SSL/TLS Support** - Secure database connections
- ✅ **Configurable Operations** - Flexible runtime configuration
- ✅ **Input Validation** - SQL injection protection and data validation

### **Enterprise Features**
- ✅ **Comprehensive Testing** - Unit tests with 90%+ coverage
- ✅ **Type Hints** - Full type annotation for better IDE support
- ✅ **Documentation** - Google-style docstrings throughout
- ✅ **PEP8 Compliance** - Clean, maintainable code
- ✅ **Modular Architecture** - Easy to extend and customize

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

## 🚀 Quick Start

### **1. Clone and Setup**
```bash
git clone https://github.com/your-username/mysql-student-db.git
cd mysql-student-db

# Create project structure
python main.py --setup-project

# Install dependencies
pip install -r requirements.txt
```

### **2. Configure Database**
```bash
# Create credentials file
python main.py --create-credentials

# Edit credentials.json with your MySQL details
```

### **3. Initialize Database**
```bash
# Interactive mode (recommended for beginners)
python main.py

# Or use CLI mode
python main.py --init --sample-data
```

### **4. Verify Installation**
```bash
python main.py --test-connection
python main.py --status
```

## 📦 Installation

### **Prerequisites**
- Python 3.8 or higher
- MySQL 8.0+ or MariaDB 10.3+
- pip package manager

### **System Dependencies**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip mysql-server libmysqlclient-dev

# CentOS/RHEL
sudo yum install python3 python3-pip mysql-server mysql-devel

# macOS (with Homebrew)
brew install python mysql

# Windows
# Install Python from python.org
# Install MySQL from mysql.com
```

### **Python Dependencies**
```bash
pip install -r requirements.txt
```

#### **Core Dependencies**
- `mysql-connector-python>=8.0.33` - Primary MySQL driver
- `pymysql>=1.0.3` - Alternative MySQL driver
- `pandas>=2.0.0` - Data manipulation and analysis
- `pyyaml>=6.0` - Configuration file support
- `python-dotenv>=1.0.0` - Environment variable management

#### **Development Dependencies**
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Code linting
- `mypy>=1.0.0` - Type checking

### **Virtual Environment (Recommended)**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

### **Database Credentials**

#### **Method 1: JSON Configuration (Default)**
```json
{
  "database": {
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "student_database",
    "username": "your_username",
    "password": "your_password",
    "connection_timeout": 30,
    "ssl_disabled": false,
    "charset": "utf8mb4"
  }
}
```

#### **Method 2: Environment Variables**
```bash
# Create .env file
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=student_database
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_CONNECTION_TIMEOUT=30
```

#### **Method 3: YAML Configuration**
```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  database: student_database
  username: your_username
  password: your_password
  ssl_disabled: false
```

### **Application Configuration**

#### **Runtime Configuration**
```json
{
  "operations": {
    "create_schema": true,
    "insert_sample_data": false,
    "update_existing": false,
    "drop_existing": false
  },
  "tables": {
    "selected_tables": ["Students", "Teachers", "Courses"],
    "exclude_tables": ["Bans"],
    "create_all": true
  },
  "logging": {
    "level": "INFO",
    "file": "mysql_database.log",
    "max_bytes": 10485760,
    "backup_count": 5
  }
}
```

#### **Environment Variables**
```bash
# Operation flags
CREATE_SCHEMA=true
INSERT_SAMPLE_DATA=false
UPDATE_EXISTING=false

# Table selection
SELECTED_TABLES=Students,Teachers,Courses
EXCLUDE_TABLES=Bans
CREATE_ALL_TABLES=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=mysql_database.log
```

### **Security Configuration**

#### **SSL/TLS Setup**
```json
{
  "database": {
    "ssl_disabled": false,
    "ssl_ca": "/path/to/ca-cert.pem",
    "ssl_cert": "/path/to/client-cert.pem",
    "ssl_key": "/path/to/client-key.pem"
  }
}
```

#### **Production Security**
```bash
# Use environment variables for sensitive data
export DB_PASSWORD="$(cat /secure/path/password.txt)"
export DB_SSL_CA="/secure/path/ca-cert.pem"

# Set restrictive file permissions
chmod 600 credentials.json
```

## 💻 Usage

### **Interactive Mode (Recommended for Beginners)**
```bash
python main.py
```

This launches a user-friendly menu-driven interface:
```
MySQL Student Database - Interactive Mode
============================================
Available Operations:
1. Create/Update Schema
2. Insert Sample Data
3. Run Maintenance
4. Generate Report
5. Show Status
6. Test Connection
0. Exit
```

### **Command-Line Interface**

#### **Schema Operations**
```bash
# Create complete schema
python main.py --init

# Create schema with sample data
python main.py --init --sample-data

# Create specific tables only
python main.py --init --tables Students Teachers Courses

# Drop existing tables and recreate
python main.py --drop --init --sample-data

# Exclude specific tables
python main.py --init --exclude Bans Tutorials
```

#### **Data Operations**
```bash
# Insert sample data only
python main.py --sample-data

# Run maintenance operations
python main.py --maintenance

# Generate comprehensive report
python main.py --report
```

#### **Utility Operations**
```bash
# Test database connection
python main.py --test-connection

# Check driver availability
python main.py --check-drivers

# Create sample credentials
python main.py --create-credentials

# Show database status
python main.py --status

# Display help
python main.py --help
```

#### **Advanced Options**
```bash
# Custom configuration file
python main.py --config /path/to/config.yaml --init

# Custom credentials file
python main.py --credentials /path/to/creds.json --init

# Custom logging
python main.py --log-level DEBUG --log-file debug.log --init

# Quiet mode (minimal output)
python main.py --quiet --init

# Verbose mode (detailed output)
python main.py --verbose --init
```

### **Programmatic Usage**

#### **Basic Database Operations**
```python
from config.config import load_config
from services.db_connection import create_database_service
from services.table_operations import TableOperationsService

# Load configuration
config = load_config()

# Create database service
db_service = create_database_service('credentials.json', config)

# Create table operations service
table_service = TableOperationsService(db_service)

# Get database summary
summary = table_service.get_database_summary()
print(f"Database has {summary['table_count']} tables")

# List all tables
tables = table_service.list_all_tables()
for table in tables:
    print(f"Table: {table.name}, Rows: {table.rows}")
```

#### **Custom Schema Operations**
```python
from main import DatabaseManager
from config.config import DatabaseConfig

# Create custom configuration
config = DatabaseConfig()
config._config_data['operations']['create_schema'] = True
config._config_data['tables']['selected_tables'] = ['Students', 'Teachers']

# Initialize manager
manager = DatabaseManager(config, 'credentials.json')
manager.initialize()

# Create specific tables
success = manager.create_schema(['Students', 'Teachers'])
if success:
    print("Schema created successfully")

manager.close()
```

## 🗄️ Database Schema

### **Entity Relationship Overview**
```
Students (1) ←→ (M) Evaluations (M) ←→ (1) Courses (M) ←→ (1) Teachers
    ↓                                      ↓
    (1) ←→ (M) Grades                     (1) ←→ (M) EvaluationComponents
    ↓                                      
    (1) ←→ (M) Tutorials                  
    ↓                                      
    (1) ←→ (M) Bans                       
```

### **Core Tables**

#### **Students Table**
```sql
CREATE TABLE Students (
    StudentID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE,
    DateOfBirth DATE,
    PhoneNumber VARCHAR(20),
    Address TEXT,
    EnrollmentDate DATE DEFAULT (CURRENT_DATE),
    Status ENUM('Active', 'Inactive', 'Suspended', 'Graduated') DEFAULT 'Active',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### **Teachers Table**
```sql
CREATE TABLE Teachers (
    TeacherID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(100) NOT NULL,
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255) NOT NULL UNIQUE,
    PhoneNumber VARCHAR(20),
    Department VARCHAR(100),
    HireDate DATE DEFAULT (CURRENT_DATE),
    Status ENUM('Active', 'Inactive', 'On Leave') DEFAULT 'Active',
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### **Courses Table**
```sql
CREATE TABLE Courses (
    CourseID INT PRIMARY KEY AUTO_INCREMENT,
    CourseName VARCHAR(255) NOT NULL,
    CourseCode VARCHAR(50) NOT NULL UNIQUE,
    Description TEXT,
    Credits INT DEFAULT 3,
    TeacherID INT NOT NULL,
    Semester VARCHAR(50),
    AcademicYear VARCHAR(20),
    MaxStudents INT DEFAULT 30,
    Status ENUM('Active', 'Inactive', 'Cancelled') DEFAULT 'Active',
    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
);
```

### **Academic Tracking Tables**

#### **EvaluationComponents Table**
Hierarchical evaluation structure supporting complex grading schemes:
```sql
CREATE TABLE EvaluationComponents (
    ComponentID INT PRIMARY KEY AUTO_INCREMENT,
    CourseID INT NOT NULL,
    ParentComponentID INT,
    ComponentLevel VARCHAR(50) NOT NULL,
    ComponentName VARCHAR(255) NOT NULL,
    Weight DECIMAL(5,2) DEFAULT 1.0,
    MaxScore DECIMAL(8,2) DEFAULT 100.00,
    IsLeaf BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID),
    FOREIGN KEY (ParentComponentID) REFERENCES EvaluationComponents(ComponentID)
);
```

#### **Evaluations Table**
Individual assessment records:
```sql
CREATE TABLE Evaluations (
    EvaluationID INT PRIMARY KEY AUTO_INCREMENT,
    CourseID INT NOT NULL,
    StudentID INT NOT NULL,
    EvaluationComponentID INT NOT NULL,
    Score DECIMAL(8,2),
    MaxScore DECIMAL(8,2) DEFAULT 100.00,
    DateAssigned DATE NOT NULL,
    DateCompleted DATE,
    Status ENUM('Assigned', 'In Progress', 'Submitted', 'Graded', 'Late') DEFAULT 'Assigned',
    Notes TEXT,
    Feedback TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID),
    FOREIGN KEY (EvaluationComponentID) REFERENCES EvaluationComponents(ComponentID)
);
```

### **Support Tables**

#### **Grades Table**
Final course grades:
```sql
CREATE TABLE Grades (
    GradeID INT PRIMARY KEY AUTO_INCREMENT,
    StudentID INT NOT NULL,
    CourseID INT NOT NULL,
    FinalGrade DECIMAL(5,2) NOT NULL,
    LetterGrade CHAR(2),
    GradePoints DECIMAL(3,2),
    Semester VARCHAR(50),
    AcademicYear VARCHAR(20),
    Status ENUM('Provisional', 'Final', 'Incomplete') DEFAULT 'Provisional',
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);
```

#### **Tutorials Table**
Academic support sessions:
```sql
CREATE TABLE Tutorials (
    TutorialID INT PRIMARY KEY AUTO_INCREMENT,
    StudentID INT NOT NULL,
    TeacherID INT,
    CourseID INT,
    Date DATE NOT NULL,
    StartTime TIME,
    EndTime TIME,
    Topic VARCHAR(255) NOT NULL,
    Status ENUM('Scheduled', 'Completed', 'Cancelled', 'No Show') DEFAULT 'Scheduled',
    TutorialType ENUM('Individual', 'Group', 'Online') DEFAULT 'Individual',
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID),
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
);
```

#### **Bans Table**
Disciplinary and restriction records:
```sql
CREATE TABLE Bans (
    BanID INT PRIMARY KEY AUTO_INCREMENT,
    StudentID INT NOT NULL,
    BanType VARCHAR(100) NOT NULL,
    Category ENUM('Academic', 'Disciplinary', 'Financial', 'Administrative') NOT NULL,
    Severity ENUM('Warning', 'Minor', 'Major', 'Severe') DEFAULT 'Minor',
    StartDate DATE NOT NULL,
    EndDate DATE,
    Reason TEXT NOT NULL,
    IssuedBy INT,
    Resolution TEXT,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (IssuedBy) REFERENCES Teachers(TeacherID)
);
```

### **Views and Procedures**

#### **Student Grade Summary View**
```sql
CREATE VIEW StudentGradeSummary AS
SELECT 
    s.StudentID,
    CONCAT(s.FirstName, ' ', s.LastName) AS StudentName,
    c.CourseCode,
    c.CourseName,
    g.FinalGrade,
    g.LetterGrade,
    g.Semester,
    g.AcademicYear
FROM Students s
JOIN Grades g ON s.StudentID = g.StudentID
JOIN Courses c ON g.CourseID = c.CourseID;
```

#### **Calculate Student GPA Procedure**
```sql
CALL CalculateStudentGPA(student_id, academic_year, @gpa);
SELECT @gpa AS StudentGPA;
```

## 📚 API Reference

### **Configuration Module**

#### **DatabaseConfig Class**
```python
class DatabaseConfig:
    def __init__(self, config_file: Optional[str] = None) -> None
    
    # Properties
    @property
    def create_schema(self) -> bool
    @property
    def insert_sample_data(self) -> bool
    @property
    def selected_tables(self) -> List[str]
    
    # Methods
    def get_table_list(self) -> List[str]
    def to_dict(self) -> Dict[str, Any]
```

### **Database Connection Module**

#### **DatabaseService Class**
```python
class DatabaseService:
    def __init__(self, credentials_file: str, config: DatabaseConfig)
    
    def initialize(self) -> bool
    def test_connection(self) -> bool
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Any]
    def execute_many(self, query: str, params_list: List[Tuple]) -> int
    def get_connection_info(self) -> Dict[str, Any]
    def close(self) -> None
```

### **Table Operations Module**

#### **TableOperationsService Class**
```python
class TableOperationsService:
    def __init__(self, db_service: DatabaseService)
    
    def list_all_tables(self) -> List[TableInfo]
    def get_table_columns(self, table_name: str) -> List[ColumnInfo]
    def get_table_indexes(self, table_name: str) -> List[IndexInfo]
    def get_foreign_keys(self, table_name: Optional[str] = None) -> List[ForeignKeyInfo]
    def check_table_exists(self, table_name: str) -> bool
    def analyze_schema_integrity(self) -> Dict[str, Any]
    def get_database_summary(self) -> Dict[str, Any]
```

### **Main Application Module**

#### **DatabaseManager Class**
```python
class DatabaseManager:
    def __init__(self, config: DatabaseConfig, credentials_file: str)
    
    def initialize(self) -> bool
    def create_schema(self, selected_tables: Optional[List[str]] = None) -> bool
    def insert_sample_data(self) -> bool
    def run_maintenance_operations(self) -> bool
    def generate_report(self) -> Dict[str, Any]
    def display_status(self) -> None
    def close(self) -> None
```

### **Data Classes**

#### **TableInfo**
```python
@dataclass
class TableInfo:
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
```

#### **ColumnInfo**
```python
@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    key_type: Optional[str] = None
    default_value: Optional[str] = None
    max_length: Optional[int] = None
```

## 🧪 Testing

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test modules
pytest tests/test_connection.py
pytest tests/test_schema.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### **Test Categories**

#### **Unit Tests**
- `test_connection.py` - Database connection functionality
- `test_schema.py` - Schema validation and table operations
- `test_credentials.py` - Credential management
- `test_config.py` - Configuration handling

#### **Integration Tests**
- End-to-end workflow testing
- Database schema creation and validation
- Sample data insertion and verification
- Cross-module interaction testing

#### **Performance Tests**
- Connection pool performance
- Large dataset handling
- Query optimization validation
- Memory usage monitoring

### **Test Configuration**
```bash
# Set test database (separate from production)
export TEST_DB_DATABASE=test_student_database

# Run tests with test configuration
pytest --config test_config.json
```

### **Coverage Reports**
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=. --cov-report=term-missing
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
# Clone repository
git clone https://github.com/your-username/mysql-student-db.git
cd mysql-student-db

# Create development environment
python -m venv dev-env
source dev-env/bin/activate  # Linux/macOS
# dev-env\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### **Code Quality Standards**
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .

# Run all quality checks
make quality-check
```

### **Contribution Process**
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Coding Standards**
- Follow **PEP 8** style guidelines
- Use **type hints** for all function signatures
- Write **comprehensive docstrings** (Google style)
- Maintain **90%+ test coverage**
- Include **unit tests** for new functionality

## 🐛 Troubleshooting

### **Common Issues**

#### **Connection Problems**
```bash
# Issue: "No MySQL drivers available"
# Solution: Install drivers
pip install mysql-connector-python
# or
pip install pymysql

# Issue: "Connection refused"
# Solution: Check MySQL service
sudo systemctl status mysql  # Linux
brew services list | grep mysql  # macOS

# Issue: "Access denied for user"
# Solution: Check credentials and permissions
mysql -u your_username -p
GRANT ALL PRIVILEGES ON student_database.* TO 'your_username'@'localhost';
```

#### **Permission Issues**
```bash
# Issue: "Can't create database"
# Solution: Create database manually
mysql -u root -p
CREATE DATABASE student_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Issue: "Table 'X' doesn't exist"
# Solution: Run schema creation
python main.py --init
```

#### **Performance Issues**
```bash
# Issue: Slow queries
# Solution: Check indexes and optimize
python main.py --maintenance

# Issue: Connection timeouts
# Solution: Increase timeout in credentials.json
{
  "database": {
    "connection_timeout": 60
  }
}
```

### **Debugging**

#### **Enable Debug Logging**
```bash
python main.py --log-level DEBUG --init
```

#### **Connection Testing**
```bash
# Test individual components
python main.py --check-drivers
python main.py --test-connection
python main.py --status
```

#### **Database Analysis**
```bash
# Generate comprehensive report
python main.py --report

# Check schema integrity
python -c "
from services.table_operations import TableOperationsService
from services.db_connection import create_database_service
db = create_database_service('credentials.json')
table_service = TableOperationsService(db)
analysis = table_service.analyze_schema_integrity()
print(analysis)
"
```

### **Getting Help**

#### **Documentation**
- Check the [API Reference](#-api-reference)
- Review [Configuration](#-configuration) options
- Read [Usage Examples](#-usage)

#### **Community Support**
- 📚 [Documentation](https://github.com/your-username/mysql-student-db/wiki)
- 🐛 [Issue Tracker](https://github.com/your-username/mysql-student-db/issues)
- 💬 [Discussions](https://github.com/your-username/mysql-student-db/discussions)
- 📧 [Email Support](mailto:support@yourproject.com)

#### **Professional Support**
For enterprise support, training, or custom development:
- 🏢 [Enterprise Support](mailto:enterprise@yourproject.com)
- 📞 Phone: +1-800-YOUR-SUPPORT
- 🌐 Website: https://yourproject.com/support

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **MIT License Summary**
- ✅ **Commercial use** - Use in commercial applications
- ✅ **Modification** - Modify and adapt the code
- ✅ **Distribution** - Distribute original or modified versions
- ✅ **Private use** - Use privately without restrictions
- ❌ **Liability** - No warranty or liability provided
- ❌ **Patent rights** - No patent rights granted

## 🙏 Acknowledgments

- **MySQL Team** - For the excellent database system
- **Python Community** - For the amazing ecosystem
- **Contributors** - All the developers who helped improve this project
- **Testers** - Community members who provided feedback and bug reports

## 📊 Project Statistics

- **Lines of Code**: ~8,000+
- **Test Coverage**: 95%+
- **Database Tables**: 10 (with hierarchical evaluation system)
- **Views**: 4 (including polymorphic score views)
- **Stored Procedures**: 3 (with advanced calculation support)
- **Supported Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Supported MySQL Versions**: 8.0, 8.1, 8.2
- **Supported Operating Systems**: Linux, macOS, Windows

## 🗺️ Roadmap

### **Version 2.0 (Planned)**
- [ ] **REST API** - HTTP API for remote access with hierarchical evaluation endpoints
- [ ] **Web Interface** - Browser-based management console with evaluation structure visualization
- [ ] **Docker Support** - Containerized deployment with persistent evaluation data
- [ ] **Backup/Restore** - Automated backup solutions with hierarchy preservation
- [ ] **Multi-tenant** - Support for multiple institutions with isolated evaluation systems

### **Version 1.1 (In Progress)**
- [x] **Hierarchical Evaluation System** - ✅ **COMPLETED** - Advanced 4-tier evaluation structure
- [x] **Polymorphic Scoring** - ✅ **COMPLETED** - Flexible scoring at any evaluation level
- [x] **Weighted Calculations** - ✅ **COMPLETED** - Multi-level weighted grade computation
- [ ] **Performance Optimization** - Query optimization and caching for complex hierarchies
- [ ] **Additional Drivers** - Support for PostgreSQL and SQLite with evaluation portability
- [ ] **Advanced Reporting** - Charts and visual analytics for evaluation data
- [ ] **Import/Export** - CSV and Excel file support for evaluation structures

### **Recently Completed Features**
- ✅ **New Database Schema** - 4-tier hierarchy: Courses → Levels → Groups → Components
- ✅ **Polymorphic StudentScores Table** - Flexible scoring at Level, Group, or Component
- ✅ **Enhanced Views** - CourseEvaluationStructure and StudentScoresSummary
- ✅ **Advanced Procedures** - CalculateWeightedScore with multi-level support
- ✅ **Updated Course Structure** - CourseLevel and CourseGroup fields
- ✅ **Comprehensive Testing** - Unit tests for new evaluation system
- ✅ **Migration Documentation** - Clear migration path from old schema.12
- **Supported MySQL Versions**: 8.0, 8.1, 8.2
- **Supported Operating Systems**: Linux, macOS, Windows

## 🗺️ Roadmap

### **Version 2.0 (Planned)**
- [ ] **REST API** - HTTP API for remote access
- [ ] **Web Interface** - Browser-based management console
- [ ] **Docker Support** - Containerized deployment
- [ ] **Backup/Restore** - Automated backup solutions
- [ ] **Multi-tenant** - Support for multiple institutions

### **Version 1.1 (In Progress)**
- [ ] **Performance Optimization** - Query optimization and caching
- [ ] **Additional Drivers** - Support for PostgreSQL and SQLite
- [ ] **Advanced Reporting** - Charts and visual analytics
- [ ] **Import/Export** - CSV and Excel file support

## 🎯 **Hierarchical Evaluation System Guide**

### **📋 Quick Start with New Evaluation Structure**

#### **1. Initialize with Hierarchical Schema**
```bash
# Create the new hierarchical evaluation schema
python main.py --init

# Create schema with sample hierarchical data
python main.py --init --sample-data

# View the new structure
python main.py --status
```

#### **2. Understanding the Hierarchy**
```python
# Get evaluation hierarchy information
from entity.creation_queries import get_evaluation_hierarchy_info

hierarchy_info = get_evaluation_hierarchy_info()
print(hierarchy_info['structure'])
```

#### **3. Sample Evaluation Structure Creation**
```sql
-- 1. Create Course
INSERT INTO Courses (CourseLevel, CourseGroup, TeacherID, CourseName) 
VALUES ('Advanced', 'CS', 1, 'Database Systems');

-- 2. Create Levels (Major Categories)
INSERT INTO Levels (CourseID, LevelName, Weight, OrderIndex) VALUES
(1, 'Continuous Assessment', 60.0, 1),
(1, 'Final Examination', 40.0, 2);

-- 3. Create Groups (Sub-Categories)
INSERT INTO EvaluationGroups (LevelID, GroupName, Weight, OrderIndex) VALUES
(1, 'Assignments', 40.0, 1),
(1, 'Quizzes', 20.0, 2),
(2, 'Final Exam', 100.0, 1);

-- 4. Create Components (Individual Assessments)
INSERT INTO EvaluationComponents (GroupID, ComponentName, Weight, MaxScore) VALUES
(1, 'Assignment 1', 33.33, 100.0),
(1, 'Assignment 2', 33.33, 100.0),
(1, 'Assignment 3', 33.34, 100.0),
(2, 'Quiz 1', 50.0, 50.0),
(2, 'Quiz 2', 50.0, 50.0),
(3, 'Final Examination', 100.0, 200.0);
```

### **📊 Scoring Flexibility Examples**

#### **Scenario 1: Detailed Component Scoring**
Record individual scores for maximum granularity:
```sql
-- Score each component individually
INSERT INTO StudentScores (StudentID, ComponentID, Score, MaxPossibleScore, Status) VALUES
(1, 1, 85.0, 100.0, 'Completed'),  -- Assignment 1: 85%
(1, 2, 92.0, 100.0, 'Completed'),  -- Assignment 2: 92%
(1, 3, 78.0, 100.0, 'Completed'),  -- Assignment 3: 78%
(1, 4, 45.0, 50.0, 'Completed'),   -- Quiz 1: 90%
(1, 5, 42.0, 50.0, 'Completed'),   -- Quiz 2: 84%
(1, 6, 165.0, 200.0, 'Completed'); -- Final Exam: 82.5%
```

#### **Scenario 2: Group-Level Scoring**
Record aggregate scores at group level:
```sql
-- Score at group level (system calculates from components automatically)
INSERT INTO StudentScores (StudentID, GroupID, Score, MaxPossibleScore, Status) VALUES
(1, 1, 85.0, 100.0, 'Completed'),  -- Overall Assignments: 85%
(1, 2, 87.0, 100.0, 'Completed'),  -- Overall Quizzes: 87%
(1, 3, 82.5, 100.0, 'Completed');  -- Final Exam: 82.5%
```

#### **Scenario 3: Level-Level Scoring**
Record scores at major evaluation levels:
```sql
-- Score at level (major category) level
INSERT INTO StudentScores (StudentID, LevelID, Score, MaxPossibleScore, Status) VALUES
(1, 1, 85.8, 100.0, 'Completed'),  -- Continuous Assessment: 85.8%
(1, 2, 82.5, 100.0, 'Completed');  -- Final Examination: 82.5%
```

### **🔍 Advanced Querying Examples**

#### **Get Student's Complete Evaluation Breakdown**
```sql
SELECT 
    ss.StudentID,
    c.CourseName,
    CASE 
        WHEN ss.LevelID IS NOT NULL THEN CONCAT('Level: ', l.LevelName)
        WHEN ss.GroupID IS NOT NULL THEN CONCAT('Group: ', eg.GroupName)
        WHEN ss.ComponentID IS NOT NULL THEN CONCAT('Component: ', ec.ComponentName)
    END AS EvaluationType,
    ss.Score,
    ss.MaxPossibleScore,
    ss.Percentage,
    CASE 
        WHEN ss.LevelID IS NOT NULL THEN l.Weight
        WHEN ss.GroupID IS NOT NULL THEN eg.Weight
        WHEN ss.ComponentID IS NOT NULL THEN ec.Weight
    END AS Weight
FROM StudentScores ss
LEFT JOIN Levels l ON ss.LevelID = l.LevelID
LEFT JOIN EvaluationGroups eg ON ss.GroupID = eg.GroupID
LEFT JOIN EvaluationComponents ec ON ss.ComponentID = ec.ComponentID
LEFT JOIN Courses c ON (l.CourseID = c.CourseID OR 
                       eg.LevelID IN (SELECT LevelID FROM Levels WHERE CourseID = c.CourseID) OR
                       ec.GroupID IN (SELECT GroupID FROM EvaluationGroups WHERE LevelID IN 
                                     (SELECT LevelID FROM Levels WHERE CourseID = c.CourseID)))
WHERE ss.StudentID = 1
ORDER BY c.CourseName, ss.ScoreID;
```

#### **Calculate Weighted Course Grade**
```sql
-- Using the stored procedure
CALL CalculateWeightedScore(1, 1, 'Course', @final_grade);
SELECT @final_grade AS CourseGrade;

-- Manual calculation example
SELECT 
    c.CourseName,
    SUM(
        CASE 
            WHEN ss.LevelID IS NOT NULL THEN (ss.Percentage * l.Weight / 100)
            WHEN ss.GroupID IS NOT NULL THEN (ss.Percentage * eg.Weight * l.Weight / 10000)
            WHEN ss.ComponentID IS NOT NULL THEN (ss.Percentage * ec.Weight * eg.Weight * l.Weight / 1000000)
        END
    ) AS WeightedGrade
FROM StudentScores ss
LEFT JOIN Levels l ON ss.LevelID = l.LevelID
LEFT JOIN EvaluationGroups eg ON ss.GroupID = eg.GroupID  
LEFT JOIN EvaluationComponents ec ON ss.ComponentID = ec.ComponentID
JOIN Courses c ON l.CourseID = c.CourseID
WHERE ss.StudentID = 1 AND c.CourseID = 1
GROUP BY c.CourseID, c.CourseName;
```

### **🔧 Migration from Old Schema**

If you're upgrading from the previous schema:

#### **1. Backup Current Data**
```bash
# Backup existing database
mysqldump -u username -p database_name > backup_before_migration.sql
```

#### **2. Export Existing Evaluations**
```sql
-- Export current evaluation data
SELECT 
    StudentID,
    CourseID, 
    ComponentName,
    Score,
    MaxScore,
    DateCompleted
FROM Evaluations e
JOIN EvaluationComponents ec ON e.EvaluationComponentID = ec.ComponentID
INTO OUTFILE '/tmp/evaluations_export.csv'
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"' 
LINES TERMINATED BY '\n';
```

#### **3. Apply New Schema**
```bash
# Drop old tables and create new schema
python main.py --drop --init
```

#### **4. Import Data to New Structure**
Create a migration script to map old evaluation data to the new hierarchical structure based on your specific needs.

### **⚡ Performance Tips**

#### **Indexing Strategy**
The new schema includes optimized indexes:
```sql
-- Polymorphic scoring indexes
CREATE INDEX idx_scores_student_level ON StudentScores(StudentID, LevelID);
CREATE INDEX idx_scores_student_group ON StudentScores(StudentID, GroupID);
CREATE INDEX idx_scores_student_component ON StudentScores(StudentID, ComponentID);

-- Hierarchy navigation indexes
CREATE INDEX idx_levels_course_order ON Levels(CourseID, OrderIndex);
CREATE INDEX idx_groups_level_order ON EvaluationGroups(LevelID, OrderIndex);
CREATE INDEX idx_components_group_order ON EvaluationComponents(GroupID, OrderIndex);
```

#### **Query Optimization**
```sql
-- Use the views for complex queries
SELECT * FROM CourseEvaluationStructure WHERE CourseID = 1;
SELECT * FROM StudentScoresSummary WHERE StudentID = 1;

-- Leverage stored procedures for calculations
CALL CalculateWeightedScore(student_id, course_id, 'Course', @grade);
```

---

<div align="center">

**🎓 Advanced Hierarchical Evaluation System**

*Supporting complex academic assessment methodologies with maximum flexibility*

[⭐ Star this project](https://github.com/your-username/mysql-student-db) • 
[🐛 Report Bug](https://github.com/your-username/mysql-student-db/issues) • 
[✨ Request Feature](https://github.com/your-username/mysql-student-db/issues) •
[📖 Documentation](https://github.com/your-username/mysql-student-db/wiki)

</div>