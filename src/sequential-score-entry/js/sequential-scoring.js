// Sequential Score Entry Plugin - Production Version
(function($) {
    'use strict';

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

    // Initialize when document is ready
    $(document).ready(function() {
        SSE.init();
    });

    // Also initialize when window fully loads (for Elementor compatibility)
    $(window).on('load', function() {
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
            return true;
        }

        var customDropdowns = $('[role="combobox"]');
        if (customDropdowns.length >= 3) {
            SSE.formType = 'custom';
            SSE.fields.course = customDropdowns.eq(0);
            SSE.fields.student = customDropdowns.eq(1);
            SSE.fields.component = customDropdowns.eq(2);
            return true;
        }

        return false;
    };

    SSE.setupInterface = function() {
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
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <h2 style="margin: 0 0 15px 0; color: white; font-size: 28px;">
                    📊 Sequential Student Entry Mode
                </h2>
                <div>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input type="checkbox" id="sse-toggle" style="width: 24px; height: 24px; cursor: pointer;">
                        <span style="font-size: 18px;">Enable Sequential Mode - Enter scores one student at a time</span>
                    </label>
                </div>

                <div id="sse-progress" style="display: none; margin-top: 25px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.3);">
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        Progress: Student <span id="sse-current">0</span> of <span id="sse-total">0</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.3); height: 30px; border-radius: 15px; overflow: hidden;">
                        <div id="sse-progress-bar" style="
                            height: 100%;
                            background: linear-gradient(90deg, #4caf50, #8bc34a);
                            width: 0%;
                            transition: width 0.5s ease;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <span id="sse-progress-text" style="color: white; font-weight: bold; text-shadow: 0 1px 2px rgba(0,0,0,0.3);"></span>
                        </div>
                    </div>

                    <div style="margin: 20px 0; padding: 25px; background: white; color: #333; border-radius: 10px; text-align: center;">
                        <div id="sse-student-name" style="font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 20px;">
                            Please select Course and Component
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
                                outline: none;
                            " min="0" max="100" step="0.5" placeholder="0">

                            <div style="margin-top: 25px; display: flex; justify-content: center; gap: 10px;">
                                <button type="button" id="sse-prev" style="
                                    padding: 12px 24px;
                                    background: #6c757d;
                                    color: white;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    font-size: 16px;
                                    transition: all 0.3s ease;
                                ">← Previous</button>

                                <button type="button" id="sse-skip" style="
                                    padding: 12px 24px;
                                    background: #ffc107;
                                    color: #333;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    font-size: 16px;
                                    transition: all 0.3s ease;
                                ">Skip →</button>

                                <button type="button" id="sse-save" style="
                                    padding: 12px 32px;
                                    background: #28a745;
                                    color: white;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    font-size: 16px;
                                    font-weight: bold;
                                    transition: all 0.3s ease;
                                ">Save & Next →</button>
                            </div>
                        </div>

                        <div id="sse-completion" style="display: none;">
                            <p style="font-size: 18px; color: #666; margin: 20px 0;">
                                You have successfully scored all students in this component.
                            </p>
                            <button onclick="location.reload()" style="
                                padding: 15px 30px;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                border: none;
                                border-radius: 8px;
                                font-size: 18px;
                                cursor: pointer;
                                transition: all 0.3s ease;
                            ">Start New Session</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insert interface into the page
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

        // Setup event handlers
        $('#sse-toggle').off('change').on('change', function() {
            SSE.sequentialMode = $(this).is(':checked');
            if (SSE.sequentialMode) {
                SSE.enableSequential();
            } else {
                SSE.disableSequential();
            }
        });

        SSE.setupButtonHandlers();
    };

    SSE.setupButtonHandlers = function() {
        $('#sse-prev').off('click').on('click', function(e) {
            e.preventDefault();
            if (SSE.currentIndex > 0) {
                SSE.currentIndex--;
                SSE.loadCurrentStudent();
            }
        });

        $('#sse-skip').off('click').on('click', function(e) {
            e.preventDefault();

            if (SSE.currentIndex < SSE.students.length - 1) {
                SSE.currentIndex++;
                SSE.loadCurrentStudent();
            } else {
                if (confirm('This is the last student. Mark session as complete?')) {
                    SSE.showCompletion();
                }
            }
        });

        $('#sse-save').off('click').on('click', function(e) {
            e.preventDefault();
            SSE.saveAndNext();
        });

        $('#sse-score-input').off('keypress').on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                SSE.saveAndNext();
            }
        });
    };

    SSE.enableSequential = function() {
        $('#sse-progress').slideDown();
        $('.wpda-pp-container').hide();
        SSE.setupMonitoring();
    };

    SSE.disableSequential = function() {
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
        if (courseVal === SSE.currentCourseText &&
            componentVal === SSE.currentComponentText &&
            SSE.studentsLoaded) {
            return;
        }

        if (courseVal && !courseVal.includes('Select')) {
            SSE.currentCourseText = courseVal;
            SSE.currentComponentText = componentVal;
            SSE.loadStudents(courseVal, componentVal);
        }
    };

    SSE.loadStudents = function(courseText, componentText) {
        // Map text values to database IDs
        var courseId = 1; // Default
        var componentId = 1; // Default

        // Course mapping
        if (courseText.includes("Primer")) {
            courseId = 1;
        } else if (courseText.includes("Segon")) {
            courseId = 2;
        } else if (courseText.includes("Tercer")) {
            courseId = 3;
        } else if (courseText.includes("Quart")) {
            courseId = 4;
        }

        // Component mapping
        if (componentText && componentText.includes("Nota Final")) {
            componentId = 1;
        } else if (componentText && componentText.includes("Projecte")) {
            componentId = 2;
        } else if (componentText && componentText.includes("Examen")) {
            componentId = 3;
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

                    SSE.currentIndex = 0;
                    SSE.studentsLoaded = true;
                    $('#sse-total').text(SSE.students.length);
                    $('#sse-score-section').show();
                    $('#sse-completion').hide();
                    SSE.loadCurrentStudent();
                } else {
                    $('#sse-student-name').text('No students found for this selection');
                    $('#sse-score-section').hide();
                }
            },
            error: function(xhr, status, error) {
                console.error('Failed to load students:', error);
                $('#sse-student-name').text('Error loading students. Please try again.');
                $('#sse-score-section').hide();
            }
        });
    };

    SSE.loadCurrentStudent = function() {
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

        // Update display
        $('#sse-current').text(SSE.currentIndex + 1);
        $('#sse-student-name').text(student.name);
        $('#sse-score-input').val('').focus();

        // Update progress bar
        var progress = ((SSE.currentIndex + 1) / SSE.students.length) * 100;
        $('#sse-progress-bar').css('width', progress + '%');
        $('#sse-progress-text').text(Math.round(progress) + '%');

        // Update button states
        $('#sse-prev').prop('disabled', SSE.currentIndex === 0);

        // Change skip button text for last student
        if (SSE.currentIndex === SSE.students.length - 1) {
            $('#sse-skip').text('Finish →');
        } else {
            $('#sse-skip').text('Skip →');
        }
    };

    SSE.saveAndNext = function() {
        // Prevent duplicate saves
        if (SSE.isSaving) {
            return;
        }

        var score = $('#sse-score-input').val();

        if (!score || score === '') {
            alert('Please enter a score before proceeding.');
            $('#sse-score-input').focus();
            return;
        }

        if (!SSE.students[SSE.currentIndex]) {
            console.error('No student found at current index');
            return;
        }

        var student = SSE.students[SSE.currentIndex];
        var savedIndex = SSE.currentIndex;

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
                    // Only increment if we're still at the same index
                    if (SSE.currentIndex === savedIndex) {
                        if (SSE.currentIndex < SSE.students.length - 1) {
                            SSE.currentIndex++;
                            SSE.loadCurrentStudent();
                        } else {
                            SSE.showCompletion();
                        }
                    }

                    $('#sse-save').prop('disabled', false).text('Save & Next →');
                } else {
                    alert('Error saving score: ' + (response.data || 'Unknown error'));
                    $('#sse-save').prop('disabled', false).text('Save & Next →');
                }
            },
            error: function(xhr, status, error) {
                SSE.isSaving = false;
                console.error('Save request failed:', error);
                alert('Failed to save score. Please check your connection and try again.');
                $('#sse-save').prop('disabled', false).text('Save & Next →');
            }
        });
    };

    SSE.showCompletion = function() {
        $('#sse-student-name').text('All students completed! 🎉');
        $('#sse-score-section').hide();
        $('#sse-completion').show();

        // Update progress to 100%
        $('#sse-progress-bar').css('width', '100%');
        $('#sse-progress-text').text('100%');
    };
    
})(jQuery);