<?php
/**
 * Plugin Name: Sequential Score Entry for WP Data Access
 * Plugin URI: https://yourwebsite.com/
 * Description: Adds sequential student scoring functionality to WP Data Access forms
 * Version: 3.6.0
 * Author: Your Name
 * License: GPL v2 or later
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('SSE_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('SSE_PLUGIN_URL', plugin_dir_url(__FILE__));
define('SSE_PLUGIN_VERSION', '3.6.0');

class SequentialScoreEntry {

    private $custom_db;

    public function __construct() {
        // Enqueue scripts for both frontend and admin
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_scripts'));

        // Register AJAX handlers
        add_action('wp_ajax_sse_get_students', array($this, 'ajax_get_students'));
        add_action('wp_ajax_nopriv_sse_get_students', array($this, 'ajax_get_students'));

        add_action('wp_ajax_sse_save_score', array($this, 'ajax_save_score'));
        add_action('wp_ajax_nopriv_sse_save_score', array($this, 'ajax_save_score'));

        add_action('wp_ajax_sse_get_courses', array($this, 'ajax_get_courses'));
        add_action('wp_ajax_nopriv_sse_get_courses', array($this, 'ajax_get_courses'));

        add_action('wp_ajax_sse_get_components', array($this, 'ajax_get_components'));
        add_action('wp_ajax_nopriv_sse_get_components', array($this, 'ajax_get_components'));

        // Initialize custom database connection
        $this->init_custom_db();
    }

    private function init_custom_db() {
        // External database credentials
        $host = 'POAPMYSQL145.dns-servicio.com';
        $port = 3306;
        $username = 'imunky';
        $password = 'YOUR_DATABASE_PASSWORD_HERE'; // Replace with the actual password for user 'imunky'
        $database = '8440072_musikperatu';

        // Format host with port
        $db_host = $host . ':' . $port;

        error_log('SSE: Attempting connection to: ' . $db_host . ' with user: ' . $username . ' database: ' . $database);

        // Create custom wpdb instance for your external database
        $this->custom_db = new wpdb($username, $password, $database, $db_host);

        if (!empty($this->custom_db->last_error)) {
            error_log('SSE Custom DB Connection Error: ' . $this->custom_db->last_error);

            // Try direct mysqli connection for debugging
            $mysqli = new mysqli($host, $username, $password, $database, $port);
            if ($mysqli->connect_error) {
                error_log('SSE Direct mysqli connection failed: ' . $mysqli->connect_error);
            } else {
                error_log('SSE Direct mysqli connection successful to external database');
                $result = $mysqli->query("SELECT COUNT(*) as count FROM Courses");
                if ($result) {
                    $row = $result->fetch_assoc();
                    error_log('SSE Direct mysqli query result: ' . $row['count'] . ' courses found');
                } else {
                    error_log('SSE Direct mysqli query failed: ' . $mysqli->error);
                }
                $mysqli->close();
            }
        } else {
            error_log('SSE Custom DB Connected successfully to external database: ' . $database);

            // Test the connection immediately
            $test_result = $this->custom_db->get_var("SELECT COUNT(*) FROM Courses");
            if ($this->custom_db->last_error) {
                error_log('SSE Test query error: ' . $this->custom_db->last_error);
            } else {
                error_log('SSE Immediate test query result: ' . $test_result . ' courses found');
            }
        }
    }

    public function enqueue_scripts() {
        wp_enqueue_script(
            'sequential-scoring',
            SSE_PLUGIN_URL . 'js/sequential-scoring.js',
            array('jquery'),
            SSE_PLUGIN_VERSION,
            true
        );

        wp_enqueue_style(
            'sequential-scoring',
            SSE_PLUGIN_URL . 'css/sequential-scoring.css',
            array(),
            SSE_PLUGIN_VERSION
        );

        // Create the sse_ajax object
        wp_localize_script('sequential-scoring', 'sse_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('sse_nonce')
        ));
    }

    public function ajax_get_courses() {
        error_log('SSE: ajax_get_courses called - version 3.6.0 - External DB');

        // Verify nonce
        $nonce = isset($_POST['nonce']) ? $_POST['nonce'] : '';
        if (!wp_verify_nonce($nonce, 'sse_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }

        if (!$this->custom_db) {
            wp_send_json_error('Database connection not available');
            return;
        }

        // Simple query with just essential columns
        $query = "
            SELECT
                CourseID,
                CourseName
            FROM Courses
            ORDER BY CourseID
        ";

        $courses = $this->custom_db->get_results($query);

        if ($this->custom_db->last_error) {
            error_log('SSE Custom DB Error: ' . $this->custom_db->last_error);
            wp_send_json_error('Database error: ' . $this->custom_db->last_error);
            return;
        }

        error_log('SSE Courses found in external DB: ' . count($courses ?: array()));
        wp_send_json_success($courses ?: array());
    }

    public function ajax_get_components() {
        error_log('SSE: ajax_get_components called - External DB');

        // Verify nonce
        $nonce = isset($_POST['nonce']) ? $_POST['nonce'] : '';
        if (!wp_verify_nonce($nonce, 'sse_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }

        if (!$this->custom_db) {
            wp_send_json_error('Database connection not available');
            return;
        }

        $course_id = isset($_POST['course_id']) ? intval($_POST['course_id']) : 0;

        if ($course_id) {
            // Get components for specific course
            $query = $this->custom_db->prepare("
                SELECT
                    ComponentID,
                    ComponentName
                FROM EvaluationComponents
                WHERE IsActive = 1
                ORDER BY ComponentID
            ");
        } else {
            // Get all active components
            $query = "
                SELECT
                    ComponentID,
                    ComponentName
                FROM EvaluationComponents
                WHERE IsActive = 1
                ORDER BY ComponentID
            ";
        }

        $components = $this->custom_db->get_results($query);

        if ($this->custom_db->last_error) {
            error_log('SSE Components Custom DB Error: ' . $this->custom_db->last_error);
            wp_send_json_error('Database error: ' . $this->custom_db->last_error);
            return;
        }

        error_log('SSE Components found in external DB: ' . count($components ?: array()));
        wp_send_json_success($components ?: array());
    }

    public function ajax_get_students() {
        error_log('SSE: ajax_get_students called - External DB');

        // Verify nonce
        $nonce = isset($_POST['nonce']) ? $_POST['nonce'] : '';
        if (!wp_verify_nonce($nonce, 'sse_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }

        if (!$this->custom_db) {
            wp_send_json_error('Database connection not available');
            return;
        }

        $course_id = isset($_POST['course_id']) ? intval($_POST['course_id']) : 0;

        if (!$course_id) {
            wp_send_json_error('Missing course ID');
            return;
        }

        // Get students enrolled in the course - simplified query
        $query = $this->custom_db->prepare("
            SELECT DISTINCT
                s.StudentID,
                s.FirstName,
                s.LastName,
                CONCAT(s.FirstName, ' ', s.LastName) as FullName
            FROM Students s
            INNER JOIN Enrollments e ON s.StudentID = e.StudentID
            WHERE e.CourseID = %d
            ORDER BY s.LastName, s.FirstName
        ", $course_id);

        $students = $this->custom_db->get_results($query);

        if ($this->custom_db->last_error) {
            error_log('SSE Students Custom DB Error: ' . $this->custom_db->last_error);
            wp_send_json_error('Database error: ' . $this->custom_db->last_error);
            return;
        }

        error_log('SSE Students found in external DB: ' . count($students ?: array()));

        if ($students && count($students) > 0) {
            wp_send_json_success($students);
        } else {
            wp_send_json_error('No students found enrolled in this course');
        }
    }

    public function ajax_save_score() {
        error_log('SSE: ajax_save_score called - External DB');

        // Verify nonce
        $nonce = isset($_POST['nonce']) ? $_POST['nonce'] : '';
        if (!wp_verify_nonce($nonce, 'sse_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }

        if (!$this->custom_db) {
            wp_send_json_error('Database connection not available');
            return;
        }

        $student_id = isset($_POST['student_id']) ? intval($_POST['student_id']) : 0;
        $component_id = isset($_POST['component_id']) ? intval($_POST['component_id']) : 0;
        $course_id = isset($_POST['course_id']) ? intval($_POST['course_id']) : 0;
        $score = isset($_POST['score']) ? floatval($_POST['score']) : 0;

        if (!$student_id || !$component_id || !$course_id) {
            wp_send_json_error('Missing required fields');
            return;
        }

        // Validate score
        if ($score < 0 || $score > 100) {
            wp_send_json_error('Score must be between 0 and 100');
            return;
        }

        // Verify that the CourseID exists in the Courses table
        $course_exists = $this->custom_db->get_var($this->custom_db->prepare(
            "SELECT CourseID FROM Courses WHERE CourseID = %d", $course_id
        ));

        if (!$course_exists) {
            error_log('SSE: CourseID ' . $course_id . ' does not exist in Courses table');
            wp_send_json_error('Invalid CourseID: Course does not exist');
            return;
        }

        // Verify that the ComponentID exists
        $component_exists = $this->custom_db->get_var($this->custom_db->prepare(
            "SELECT ComponentID FROM EvaluationComponents WHERE ComponentID = %d", $component_id
        ));

        if (!$component_exists) {
            error_log('SSE: ComponentID ' . $component_id . ' does not exist in EvaluationComponents table');
            wp_send_json_error('Invalid ComponentID: Component does not exist');
            return;
        }

        // Verify that the StudentID exists
        $student_exists = $this->custom_db->get_var($this->custom_db->prepare(
            "SELECT StudentID FROM Students WHERE StudentID = %d", $student_id
        ));

        if (!$student_exists) {
            error_log('SSE: StudentID ' . $student_id . ' does not exist in Students table');
            wp_send_json_error('Invalid StudentID: Student does not exist');
            return;
        }

        error_log('SSE: All IDs validated - CourseID: ' . $course_id . ', ComponentID: ' . $component_id . ', StudentID: ' . $student_id);

        // Build data array based on your table structure
        $data = array(
            'StudentID' => $student_id,
            'CourseID' => $course_id,
            'ComponentID' => $component_id,
            'Score' => $score,
            'LevelID' => 0,  // Based on your sample data
            'GroupID' => 0,  // Based on your sample data
            'MaxPossibleScore' => 0,  // Based on your sample data
            'Percentage' => 0,  // Based on your sample data
            'RecordedBy' => 0,  // Based on your sample data
            'RecordedAt' => current_time('mysql'),
            'UpdatedAt' => current_time('mysql')
        );

        $format = array('%d', '%d', '%d', '%f', '%d', '%d', '%d', '%d', '%d', '%s', '%s');

        error_log('SSE: Attempting to save score data: ' . print_r($data, true));

        // Check if score already exists
        $existing = $this->custom_db->get_row($this->custom_db->prepare(
            "SELECT ScoreID FROM StudentScores WHERE StudentID = %d AND ComponentID = %d AND CourseID = %d",
            $student_id, $component_id, $course_id
        ));

        if ($existing) {
            // Update existing score - only update the score and timestamp
            error_log('SSE: Updating existing score with ScoreID: ' . $existing->ScoreID);
            $update_data = array(
                'Score' => $score,
                'UpdatedAt' => current_time('mysql')
            );
            $result = $this->custom_db->update(
                'StudentScores',
                $update_data,
                array('ScoreID' => $existing->ScoreID),
                array('%f', '%s'),
                array('%d')
            );
        } else {
            // Insert new score
            error_log('SSE: Inserting new score');
            $result = $this->custom_db->insert(
                'StudentScores',
                $data,
                $format
            );
        }

        if ($result !== false) {
            error_log('SSE: Score saved successfully in external DB for student ' . $student_id);
            wp_send_json_success(array(
                'message' => 'Score saved successfully',
                'student_id' => $student_id,
                'score' => $score
            ));
        } else {
            error_log('SSE External DB Save Error: ' . ($this->custom_db->last_error ?: 'Unknown error'));
            wp_send_json_error('Failed to save score: ' . ($this->custom_db->last_error ?: 'Unknown error'));
        }
    }
}

// Initialize the plugin
new SequentialScoreEntry();