// Sequential Score Entry Plugin - Final Complete Version
(function($) {
    'use strict';
    
    console.log('[SSE] Plugin script loaded');
    
    var SSE = {
        initialized: false,
        sequentialMode: false,
        students: [],
        currentIndex: 0,
        studentsLoaded: false,
        currentCourseId: null,
        currentComponentId: null,
        currentCourseText: '',
        currentComponentText: '',
        formType: null,
        isSaving: false,
        fields: {
            course: null,
            student: null,
            component: null
        }
    };
    
    // Make SSE globally accessible for debugging
    window.SSE = SSE;
    
    // Initialize when document is ready
    $(document).ready(function() {
        console.log('[SSE] Document ready');
        SSE.init();
    });
    
    // Also try when window fully loads
    $(window).on('load', function() {
        console.log('[SSE] Window loaded');
        if (!SSE.initialized) {
            SSE.init();
        }
    });
    
    SSE.init = function() {
        var attempts = 0;
        var initInterval = setInterval(function() {
            attempts++;
            
            if (SSE.detectFormType() || attempts > 20) {
                clearInterval(initInterval);
                if (SSE.formType) {
                    SSE.setupInterface();
                    SSE.initialized = true;
                }
            }
        }, 500);
    };
    
    SSE.detectFormType = function() {
        // Check for WP Data Access custom dropdowns
        var dropdownContainers = $('.wpda-pp-container').find('input').parent();
        if (dropdownContainers.length >= 3) {
            SSE.formType = 'custom';
            SSE.fields.course = dropdownContainers.eq(0);
            SSE.fields.student = dropdownContainers.eq(1);
            SSE.fields.component = dropdownContainers.eq(2);
            console.log('[SSE] Detected WPDA form with', dropdownContainers.length, 'fields');
            return true;
        }
        
        var customDropdowns = $('[role="combobox"]');
        if (customDropdowns.length >= 3) {
            SSE.formType = 'custom';
            SSE.fields.course = customDropdowns.eq(0);
            SSE.fields.student = customDropdowns.eq(1);
            SSE.fields.component = customDropdowns.eq(2);
            console.log('[SSE] Detected custom dropdowns:', customDropdowns.length);
            return true;
        }
        
        return false;
    };
    
    SSE.setupInterface = function() {
        console.log('[SSE] Setting up interface');
        
        // Remove any existing container
        $('#sse-container').remove();
        
        var interfaceHTML = `
            <div id="sse-container" style="
                margin: 0 auto 30px;
                padding: 25px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            ">
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 28px;">
                    📊 Sequential Student Entry Mode
                </h2>
                <div>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input type="checkbox" id="sse-toggle" style="width: 24px; height: 24px;">
                        <span style="font-size: 18px;">Enable Sequential Mode - Enter scores one student at a time</span>
                    </label>
                </div>
                
                <div id="sse-progress" style="display: none; margin-top: 25px;">
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        Progress: Student <span id="sse-current">0</span> of <span id="sse-total">0</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.3); height: 30px; border-radius: 15px; overflow: hidden;">
                        <div id="sse-progress-bar" style="height: 100%; background: #4caf50; width: 0%; transition: width 0.5s; display: flex; align-items: center; justify-content: center;">
                            <span id="sse-progress-text" style="color: white; font-weight: bold;"></span>
                        </div>
                    </div>
                    
                    <div style="margin: 20px 0; padding: 25px; background: white; color: #333; border-radius: 10px; text-align: center;">
                        <div id="sse-student-name" style="font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 20px;">
                            Select Course and Component
                        </div>
                        
                        <div id="sse-score-section" style="display: none;">
                            <label style="display: block; font-size: 18px; color: #555; margin-bottom: 10px;">
                                Enter Score:
                            </label>
                            <input type="number" id="sse-score-input" style="
                                width: 200px;
                                padding: 15px;
                                font-size: 24px;
                                text-align: center;
                                border: 2px solid #667eea;
                                border-radius: 8px;
                                margin: 0 auto;
                                display: block;
                            " min="0" max="100" step="0.5">
                            
                            <div style="margin-top: 25px;">
                                <button type="button" id="sse-prev" style="
                                    padding: 12px 24px;
                                    background: #6c757d;
                                    color: white;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    margin: 0 5px;
                                ">← Previous</button>
                                
                                <button type="button" id="sse-skip" style="
                                    padding: 12px 24px;
                                    background: #ffc107;
                                    color: #333;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    margin: 0 5px;
                                ">Skip →</button>
                                
                                <button type="button" id="sse-save" style="
                                    padding: 12px 32px;
                                    background: #28a745;
                                    color: white;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    margin: 0 5px;
                                    font-weight: bold;
                                ">Save & Next →</button>
                            </div>
                        </div>
                        
                        <div id="sse-completion" style="display: none;">
                            <p style="font-size: 18px; color: #666; margin: 20px 0;">
                                You have scored all students in this component.
                            </p>
                            <button onclick="location.reload()" style="
                                padding: 15px 30px;
                                background: #667eea;
                                color: white;
                                border: none;
                                border-radius: 8px;
                                font-size: 18px;
                                cursor: pointer;
                            ">Start New Session</button>
                        </div>
                    </div>
                </div>
                
                <!-- Debug button -->
                <button type="button" onclick="SSE.debugStudents()" style="
                    margin-top: 10px;
                    padding: 5px 10px;
                    background: yellow;
                    color: black;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 12px;
                ">Debug: Show Students Info</button>
            </div>
        `;
        
        // Insert interface
        var inserted = false;
        if ($('.wpda_app_container, [class*="wpda"]').length) {
            $('.wpda_app_container, [class*="wpda"]').first().before(interfaceHTML);
            inserted = true;
        } else if ($('.elementor-widget-container').length) {
            $('.elementor-widget-container').first().prepend(interfaceHTML);
            inserted = true;
        } else if ($('#content, .entry-content, main').length) {
            $('#content, .entry-content, main').first().prepend(interfaceHTML);
            inserted = true;
        }
        
        if (!inserted) {
            $('body').prepend(interfaceHTML);
        }
        
        // Setup event handlers - remove old ones first
        $('#sse-toggle').off('change').on('change', function() {
            SSE.sequentialMode = $(this).is(':checked');
            if (SSE.sequentialMode) {
                SSE.enableSequential();
            } else {
                SSE.disableSequential();
            }
        });
        
        // Setup button handlers
        SSE.setupButtonHandlers();
        
        console.log('[SSE] Interface setup complete');
    };
    
    SSE.setupButtonHandlers = function() {
        // Remove old handlers and add new ones
        $('#sse-prev').off('click').on('click', function(e) {
            e.preventDefault();
            console.log('[SSE] Previous clicked at index:', SSE.currentIndex);
            if (SSE.currentIndex > 0) {
                SSE.currentIndex--;
                SSE.loadCurrentStudent();
            }
        });
        
        $('#sse-skip').off('click').on('click', function(e) {
            e.preventDefault();
            console.log('[SSE] Skip clicked at index:', SSE.currentIndex);
            
            if (SSE.currentIndex < SSE.students.length - 1) {
                SSE.currentIndex++;
                SSE.loadCurrentStudent();
            } else {
                if (confirm('This is the last student. Mark as complete?')) {
                    SSE.showCompletion();
                }
            }
        });
        
        $('#sse-save').off('click').on('click', function(e) {
            e.preventDefault();
            console.log('[SSE] Save button clicked');
            SSE.saveAndNext();
        });
        
        $('#sse-score-input').off('keypress').on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                console.log('[SSE] Enter key pressed');
                SSE.saveAndNext();
            }
        });
    };
    
    SSE.enableSequential = function() {
        console.log('[SSE] Enabling sequential mode');
        $('#sse-progress').slideDown();
        $('.wpda-pp-container').hide();
        SSE.setupMonitoring();
    };
    
    SSE.disableSequential = function() {
        console.log('[SSE] Disabling sequential mode');
        $('#sse-progress').slideUp();
        $('.wpda-pp-container').show();
        SSE.studentsLoaded = false;
        SSE.students = [];
        SSE.currentIndex = 0;
    };
    
    SSE.setupMonitoring = function() {
        SSE.checkAndLoadStudents();
        
        var observer = new MutationObserver(function() {
            clearTimeout(SSE.mutationTimeout);
            SSE.mutationTimeout = setTimeout(function() {
                SSE.checkAndLoadStudents();
            }, 500);
        });
        
        if ($('.wpda-pp-container').length) {
            observer.observe($('.wpda-pp-container')[0], {
                childList: true,
                subtree: true
            });
        }
    };
    
    SSE.getFieldValue = function(field) {
        if (!field || !field.length) return null;
        var $input = field.parent().find('input').first();
        if ($input.length && $input.val()) {
            return $input.val();
        }
        return null;
    };
    
    SSE.checkAndLoadStudents = function() {
        var courseVal = SSE.getFieldValue(SSE.fields.course);
        var componentVal = SSE.getFieldValue(SSE.fields.component);
        
        // Don't reload if already loaded with same values
        if (courseVal === SSE.currentCourseText && componentVal === SSE.currentComponentText && SSE.studentsLoaded) {
            return;
        }
        
        if (courseVal && !courseVal.includes('Select')) {
            SSE.currentCourseText = courseVal;
            SSE.currentComponentText = componentVal;
            SSE.loadStudents(courseVal, componentVal);
        }
    };
    
    SSE.loadStudents = function(courseText, componentText) {
        console.log('[SSE] Loading students for:', courseText, componentText);
        
        // Map text to IDs
        var courseId = 1; // Default
        var componentId = 1; // Default
        
        if (courseText.includes("Primer")) {
            courseId = 1;
        } else if (courseText.includes("Segon")) {
            courseId = 2;
        } else if (courseText.includes("Tercer")) {
            courseId = 3;
        }
        
        if (componentText && componentText.includes("Nota Final")) {
            componentId = 1;
        } else if (componentText && componentText.includes("Projecte")) {
            componentId = 2;
        }
        
        SSE.currentCourseId = courseId;
        SSE.currentComponentId = componentId;
        
        $('#sse-student-name').text('Loading students...');
        
        $.ajax({
            url: sequential_scoring.ajax_url,
            type: 'POST',
            data: {
                action: 'get_students_for_scoring',
                course_id: courseId,
                nonce: sequential_scoring.nonce
            },
            success: function(response) {
                if (response.success && response.data && response.data.length > 0) {
                    SSE.students = response.data.map(function(s) {
                        return {
                            id: s.StudentID,
                            name: s.FullName
                        };
                    });
                    console.log('[SSE] Loaded', SSE.students.length, 'students');
                    SSE.currentIndex = 0;
                    SSE.studentsLoaded = true;
                    $('#sse-total').text(SSE.students.length);
                    $('#sse-score-section').show();
                    $('#sse-completion').hide();
                    SSE.loadCurrentStudent();
                } else {
                    $('#sse-student-name').text('No students found');
                    $('#sse-score-section').hide();
                }
            },
            error: function() {
                $('#sse-student-name').text('Error loading students');
                $('#sse-score-section').hide();
            }
        });
    };
    
    SSE.loadCurrentStudent = function() {
        console.log('[SSE] Loading student at index:', SSE.currentIndex, 'of', SSE.students.length);
        
        if (!SSE.students || SSE.students.length === 0) {
            $('#sse-student-name').text('No students to display');
            $('#sse-score-section').hide();
            return;
        }
        
        if (SSE.currentIndex >= SSE.students.length) {
            SSE.showCompletion();
            return;
        }
        
        var student = SSE.students[SSE.currentIndex];
        console.log('[SSE] Displaying student:', student.name, 'ID:', student.id);
        
        $('#sse-current').text(SSE.currentIndex + 1);
        $('#sse-student-name').text(student.name);
        $('#sse-score-input').val('').focus();
        
        var progress = ((SSE.currentIndex + 1) / SSE.students.length) * 100;
        $('#sse-progress-bar').css('width', progress + '%');
        $('#sse-progress-text').text(Math.round(progress) + '%');
        
        // Update button states
        $('#sse-prev').prop('disabled', SSE.currentIndex === 0);
        
        // Update skip button text for last student
        if (SSE.currentIndex === SSE.students.length - 1) {
            $('#sse-skip').text('Finish →');
        } else {
            $('#sse-skip').text('Skip →');
        }
    };
    
    SSE.saveAndNext = function() {
        // Prevent duplicate saves
        if (SSE.isSaving) {
            console.log('[SSE] Save already in progress, ignoring');
            return;
        }
        
        var score = $('#sse-score-input').val();
        
        if (!score) {
            alert('Please enter a score');
            $('#sse-score-input').focus();
            return;
        }
        
        if (!SSE.students[SSE.currentIndex]) {
            console.error('[SSE] No student at index:', SSE.currentIndex);
            return;
        }
        
        var student = SSE.students[SSE.currentIndex];
        var savedIndex = SSE.currentIndex; // Store current index
        
        console.log('[SSE] Saving score for student:', student.name, 'at index:', savedIndex);
        
        SSE.isSaving = true;
        $('#sse-save').prop('disabled', true).text('Saving...');
        
        $.ajax({
            url: sequential_scoring.ajax_url,
            type: 'POST',
            data: {
                action: 'save_student_score',
                student_id: student.id,
                component_id: SSE.currentComponentId,
                course_id: SSE.currentCourseId,
                score: score,
                notes: '',
                nonce: sequential_scoring.nonce
            },
            success: function(response) {
                SSE.isSaving = false;
                
                if (response.success) {
                    console.log('[SSE] Score saved for index:', savedIndex);
                    
                    // Only increment if we're still at the same index
                    if (SSE.currentIndex === savedIndex) {
                        if (SSE.currentIndex < SSE.students.length - 1) {
                            SSE.currentIndex++;
                            console.log('[SSE] Moving to index:', SSE.currentIndex);
                            SSE.loadCurrentStudent();
                        } else {
                            console.log('[SSE] Last student completed');
                            SSE.showCompletion();
                        }
                    }
                    
                    $('#sse-save').prop('disabled', false).text('Save & Next →');
                } else {
                    alert('Error saving score: ' + response.data);
                    $('#sse-save').prop('disabled', false).text('Save & Next →');
                }
            },
            error: function(xhr, status, error) {
                SSE.isSaving = false;
                console.error('[SSE] Save error:', error);
                alert('Failed to save score. Please try again.');
                $('#sse-save').prop('disabled', false).text('Save & Next →');
            }
        });
    };
    
    SSE.showCompletion = function() {
        console.log('[SSE] Showing completion screen');
        $('#sse-student-name').text('All students completed! 🎉');
        $('#sse-score-section').hide();
        $('#sse-completion').show();
    };
    
    // Debug function
    SSE.debugStudents = function() {
        console.log('[SSE] === Debug Information ===');
        console.log('[SSE] Total students:', SSE.students.length);
        console.log('[SSE] Current index:', SSE.currentIndex);
        console.log('[SSE] Course ID:', SSE.currentCourseId);
        console.log('[SSE] Component ID:', SSE.currentComponentId);
        console.log('[SSE] Students array:', SSE.students);
        console.log('[SSE] Students loaded:', SSE.studentsLoaded);
        console.log('[SSE] Sequential mode:', SSE.sequentialMode);
        console.log('[SSE] Is saving:', SSE.isSaving);
        console.log('[SSE] ======================');
        
        alert('Debug info logged to console. Total students: ' + SSE.students.length + ', Current index: ' + SSE.currentIndex);
    };
    
})(jQuery);