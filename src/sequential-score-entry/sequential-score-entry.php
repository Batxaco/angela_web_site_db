<?php
/**
 * Plugin Name: Sequential Score Entry for WP Data Access
 * Plugin URI: https://yourwebsite.com/
 * Description: Adds sequential student scoring functionality to WP Data Access forms
 * Version: 1.0.0
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
define('SSE_PLUGIN_VERSION', '1.0.0');

class SequentialScoreEntry {
    
    public function __construct() {
        // Enqueue scripts for both frontend and admin
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_scripts'));
        
        // Register AJAX handlers
        add_action('wp_ajax_get_students_for_scoring', array($this, 'ajax_get_students_for_scoring'));
        add_action('wp_ajax_nopriv_get_students_for_scoring', array($this, 'ajax_get_students_for_scoring'));
        add_action('wp_ajax_save_student_score', array($this, 'ajax_save_student_score'));
        add_action('wp_ajax_nopriv_save_student_score', array($this, 'ajax_save_student_score'));
        add_action('wp_ajax_check_existing_score', array($this, 'ajax_check_existing_score'));
        add_action('wp_ajax_nopriv_check_existing_score', array($this, 'ajax_check_existing_score'));
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
        
        wp_localize_script('sequential-scoring', 'sequential_scoring', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('sequential_scoring_nonce')
        ));
    }
    
    public function ajax_get_students_for_scoring() {
        // Verify nonce
        if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'sequential_scoring_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }
        
        global $wpdb;
        
        $course_id = isset($_POST['course_id']) ? intval($_POST['course_id']) : 0;
        
        if (!$course_id) {
            wp_send_json_error('Missing course ID');
            return;
        }
        
        // Direct table names without WordPress prefix
        $query = "
            SELECT DISTINCT 
                StudentID,
                FullName
            FROM vw_StudentsEnrolled
            WHERE CourseID = " . intval($course_id) . "
            ORDER BY FullName
        ";
        
        $students = $wpdb->get_results($query);
        
        if ($wpdb->last_error) {
            // Try alternative query
            $alt_query = "
                SELECT 
                    StudentID,
                    CONCAT(FirstName, ' ', LastName) as FullName
                FROM Students
                ORDER BY LastName, FirstName
            ";
            
            $students = $wpdb->get_results($alt_query);
        }
        
        if ($students && count($students) > 0) {
            wp_send_json_success($students);
        } else {
            wp_send_json_error('No students found for course ID: ' . $course_id);
        }
    }
    
    public function ajax_save_student_score() {
        // Verify nonce
        if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'sequential_scoring_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }
        
        global $wpdb;
        
        $student_id = isset($_POST['student_id']) ? intval($_POST['student_id']) : 0;
        $component_id = isset($_POST['component_id']) ? intval($_POST['component_id']) : 0;
        $course_id = isset($_POST['course_id']) ? intval($_POST['course_id']) : 0;
        $score = isset($_POST['score']) ? floatval($_POST['score']) : 0;
        $notes = isset($_POST['notes']) ? sanitize_text_field($_POST['notes']) : '';
        
        if (!$student_id || !$component_id || !$course_id) {
            wp_send_json_error('Missing required fields');
            return;
        }
        
        // Check if score already exists
        $existing = $wpdb->get_row($wpdb->prepare("
            SELECT ScoreID 
            FROM StudentScores 
            WHERE StudentID = %d AND ComponentID = %d
        ", $student_id, $component_id));
        
        if ($existing) {
            // Update existing score
            $result = $wpdb->update(
                'StudentScores',
                array(
                    'Score' => $score,
                    'DateCompleted' => current_time('mysql'),
                    'Notes' => $notes
                ),
                array(
                    'StudentID' => $student_id,
                    'ComponentID' => $component_id
                ),
                array('%f', '%s', '%s'),
                array('%d', '%d')
            );
        } else {
            // Insert new score
            $result = $wpdb->insert(
                'StudentScores',
                array(
                    'StudentID' => $student_id,
                    'ComponentID' => $component_id,
                    'CourseID' => $course_id,
                    'Score' => $score,
                    'DateCompleted' => current_time('mysql'),
                    'Notes' => $notes
                ),
                array('%d', '%d', '%d', '%f', '%s', '%s')
            );
        }
        
        if ($result !== false) {
            wp_send_json_success(array(
                'message' => 'Score saved successfully',
                'student_id' => $student_id,
                'score' => $score
            ));
        } else {
            wp_send_json_error('Failed to save score: ' . $wpdb->last_error);
        }
    }
    
    public function ajax_check_existing_score() {
        // Verify nonce
        if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'sequential_scoring_nonce')) {
            wp_send_json_error('Security check failed');
            return;
        }
        
        global $wpdb;
        
        $student_id = isset($_POST['student_id']) ? intval($_POST['student_id']) : 0;
        $component_id = isset($_POST['component_id']) ? intval($_POST['component_id']) : 0;
        
        if (!$student_id || !$component_id) {
            wp_send_json_error('Missing required parameters');
            return;
        }
        
        $query = $wpdb->prepare("
            SELECT ScoreID, Score, Notes, DateCompleted
            FROM StudentScores
            WHERE StudentID = %d AND ComponentID = %d
        ", $student_id, $component_id);
        
        $score = $wpdb->get_row($query);
        
        if ($score) {
            wp_send_json_success($score);
        } else {
            wp_send_json_error('No score found');
        }
    }
}

// Initialize the plugin
new SequentialScoreEntry();