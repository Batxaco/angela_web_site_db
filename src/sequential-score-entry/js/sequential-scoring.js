// Sequential Score Entry Plugin - Working Version 3.2.0
(function($) {
    'use strict';

    // Make SSE globally accessible
    window.SSE = {
        initialized: false,
        sequentialMode: false,
        students: [],
        currentIndex: 0,
        studentsLoaded: false,
        currentCourseId: null,
        currentComponentId: null,
        currentCourseText: '',
        currentComponentText: '',
        isSaving: false,
        isLoading: false,
        courses: [],
        components: []
    };

    // Initialize when document is ready
    $(document).ready(function() {
        console.log('[SSE] Initializing plugin v3.2.0...');

        // Check if sse_ajax is available
        if (typeof sse_ajax === 'undefined') {
            console.error('[SSE] sse_ajax not found. Plugin may not be loaded correctly.');
            return;
        }

        SSE.init();
    });

    SSE.init = function() {
        SSE.setupInterface();
        SSE.loadCourses();
        SSE.initialized = true;
        console.log('[SSE] Plugin initialized successfully');
    };

    SSE.log = function(message, data) {
        console.log('[SSE]', message, data || '');
    };

    SSE.error = function(message, data) {
        console.error('[SSE]', message, data || '');
    };

    SSE.updateStatus = function(message) {
        $('#sse-status-msg').text(message);
        SSE.log('Status: ' + message);
    };

    SSE.loadCourses = function() {
        if (typeof sse_ajax === 'undefined') {
            SSE.error('sse_ajax not available');
            return;
        }

        SSE.updateStatus('Loading courses...');

        $.ajax({
            url: sse_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'sse_get_courses',
                nonce: sse_ajax.nonce
            },
            timeout: 30000,
            success: function(response) {
                console.log('[SSE] Courses response:', response);

                if (response.success && response.data) {
                    if (Array.isArray(response.data) && response.data.length > 0) {
                        SSE.courses = response.data;
                        SSE.updateCourseDropdown();
                        SSE.updateStatus('Loaded ' + SSE.courses.length + ' courses');
                        SSE.log('Successfully loaded ' + SSE.courses.length + ' courses');
                    } else {
                        SSE.updateStatus('No courses found in database');
                        SSE.error('No courses found - check if Courses table has active records');
                    }
                } else {
                    SSE.error('Invalid courses response:', response);
                    SSE.updateStatus('Error loading courses: ' + (response.data || 'Unknown error'));
                }
            },
            error: function(xhr, status, error) {
                SSE.error('Courses AJAX error:', { status: status, error: error });
                SSE.updateStatus('Error loading courses: ' + error);
                console.error('[SSE] AJAX Response:', xhr.responseText);
            }
        });
    };

    SSE.loadComponents = function(courseId) {
        if (typeof sse_ajax === 'undefined') {
            SSE.error('sse_ajax not available');
            return;
        }

        SSE.updateStatus('Loading components...');

        var data = {
            action: 'sse_get_components',
            nonce: sse_ajax.nonce
        };

        if (courseId) {
            data.course_id = courseId;
        }

        $.ajax({
            url: sse_ajax.ajax_url,
            type: 'POST',
            data: data,
            timeout: 30000,
            success: function(response) {
                console.log('[SSE] Components response:', response);

                if (response.success && response.data) {
                    if (Array.isArray(response.data)) {
                        SSE.components = response.data;
                        SSE.updateComponentDropdown();

                        if (response.data.length > 0) {
                            SSE.updateStatus('Loaded ' + SSE.components.length + ' components');
                        } else {
                            SSE.updateStatus('No components found for selected course');
                        }

                        SSE.log('Successfully loaded ' + response.data.length + ' components');
                    } else {
                        SSE.error('Components response is not an array:', response.data);
                        SSE.updateStatus('Error: Invalid response format');
                    }
                } else {
                    SSE.error('Invalid components response:', response);
                    SSE.updateStatus('Error loading components: ' + (response.data || 'Unknown error'));
                }
            },
            error: function(xhr, status, error) {
                SSE.error('Components AJAX error:', { status: status, error: error });
                SSE.updateStatus('Error loading components: ' + error);
                console.error('[SSE] AJAX Response:', xhr.responseText);
            }
        });
    };

    SSE.updateCourseDropdown = function() {
        var $select = $('#sse-course-select');
        $select.empty();
        $select.append('<option value="">Select Course</option>');

        if (SSE.courses && SSE.courses.length > 0) {
            SSE.courses.forEach(function(course) {
                var label = course.CourseID + ' - ' + course.CourseName;
                if (course.CourseCode) {
                    label += ' (' + course.CourseCode + ')';
                }
                $select.append('<option value="' + course.CourseID + '">' + label + '</option>');
            });
        } else {
            $select.append('<option value="">No courses available</option>');
        }
    };

    SSE.updateComponentDropdown = function() {
        var $select = $('#sse-component-select');
        $select.empty();
        $select.append('<option value="">Select Component</option>');

        if (SSE.components && SSE.components.length > 0) {
            SSE.components.forEach(function(component) {
                var label = component.ComponentName;
                if (component.CourseName) {
                    label += ' (' + component.CourseName + ')';
                }
                $select.append('<option value="' + component.ComponentID + '">' + label + '</option>');
            });
        } else {
            $select.append('<option value="">No components available</option>');
        }
    };

    SSE.setupInterface = function() {
        // Remove any existing container
        $('#sse-container').remove();

        var interfaceHTML = `
            <div id="sse-container" style="
                margin: 20px auto;
                padding: 25px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 10px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 1000px;
            ">
                <h2 style="margin: 0 0 20px 0; color: white; font-size: 28px;">
                    📊 Sequential Student Entry Mode
                </h2>

                <div style="margin-bottom: 20px;">
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input type="checkbox" id="sse-toggle" style="width: 24px; height: 24px; cursor: pointer;">
                        <span style="font-size: 18px;">Enable Sequential Mode</span>
                    </label>
                </div>

                <!-- Course and Component Selection -->
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin: 0 0 15px 0; font-size: 16px;">Select Course and Component:</h3>

                    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;">
                        <select id="sse-course-select" style="padding: 8px; border-radius: 4px; border: none; min-width: 200px;">
                            <option value="">Loading courses...</option>
                        </select>

                        <button id="sse-refresh-components-btn" style="
                            padding: 8px 12px;
                            background: #17a2b8;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                        ">↻ Load Components</button>
                    </div>

                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <select id="sse-component-select" style="padding: 8px; border-radius: 4px; border: none; min-width: 200px;">
                            <option value="">First select a course</option>
                        </select>

                        <button id="sse-load-students-btn" style="
                            padding: 8px 16px;
                            background: #28a745;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            cursor: pointer;
                        ">Load Students</button>
                    </div>

                    <div id="sse-status-msg" style="margin-top: 10px; font-size: 14px; opacity: 0.9;">
                        Ready to load courses...
                    </div>
                </div>

                <!-- Progress Section -->
                <div id="sse-progress" style="display: none;">
                    <div style="font-size: 16px; margin-bottom: 10px;">
                        Progress: Student <span id="sse-current">0</span> of <span id="sse-total">0</span>
                        <span id="sse-course-info" style="margin-left: 20px; font-size: 14px; opacity: 0.8;"></span>
                    </div>
                    <div style="background: rgba(255,255,255,0.3); height: 30px; border-radius: 15px; overflow: hidden;">
                        <div id="sse-progress-bar" style="
                            height: 100%;
                            background: linear-gradient(90deg, #4caf50, #8bc34a);
                            width: 0%;
                            transition: width 0.5s ease;
                        "></div>
                    </div>

                    <!-- Student Entry Section -->
                    <div style="margin: 20px 0; padding: 25px; background: white; color: #333; border-radius: 10px; text-align: center;">
                        <div id="sse-student-name" style="font-size: 32px; font-weight: bold; color: #667eea; margin-bottom: 20px;">
                            Select course and component, then click Load Students
                        </div>

                        <div id="sse-score-section" style="display: none;">
                            <label style="display: block; font-size: 18px; color: #555; margin-bottom: 10px;">
                                Enter Score (0-100):
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
                                ">← Previous</button>

                                <button type="button" id="sse-skip" style="
                                    padding: 12px 24px;
                                    background: #ffc107;
                                    color: #333;
                                    border: none;
                                    border-radius: 5px;
                                    cursor: pointer;
                                    font-size: 16px;
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
                                ">Save & Next →</button>
                            </div>
                        </div>

                        <!-- Completion Message -->
                        <div id="sse-completion" style="display: none;">
                            <p style="font-size: 18px; color: #666; margin: 20px 0;">
                                All students completed! 🎉
                            </p>
                            <button onclick="location.reload()" style="
                                padding: 15px 30px;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                border: none;
                                border-radius: 8px;
                                font-size: 18px;
                                cursor: pointer;
                            ">Start New Session</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('body').prepend(interfaceHTML);
        SSE.setupEventHandlers();
    };

    SSE.setupEventHandlers = function() {
        // Toggle sequential mode
        $('#sse-toggle').on('change', function() {
            SSE.sequentialMode = $(this).is(':checked');
            if (SSE.sequentialMode) {
                SSE.enableSequential();
            } else {
                SSE.disableSequential();
            }
        });

        // Course selection change
        $('#sse-course-select').on('change', function() {
            var courseId = $(this).val();
            if (courseId) {
                SSE.currentCourseId = parseInt(courseId);
                var course = SSE.courses.find(c => c.CourseID == courseId);
                if (course) {
                    SSE.currentCourseText = course.CourseName;
                }

                // Load components for selected course
                SSE.loadComponents(courseId);
            } else {
                SSE.currentCourseId = null;
                SSE.currentCourseText = '';
                // Clear components dropdown
                $('#sse-component-select').empty().append('<option value="">First select a course</option>');
                SSE.components = [];
            }
        });

        // Refresh components button
        $('#sse-refresh-components-btn').on('click', function() {
            var courseId = $('#sse-course-select').val();
            if (courseId) {
                SSE.loadComponents(courseId);
            } else {
                alert('Please select a course first');
            }
        });

        // Component selection change
        $('#sse-component-select').on('change', function() {
            var componentId = $(this).val();
            if (componentId) {
                SSE.currentComponentId = parseInt(componentId);
                var component = SSE.components.find(c => c.ComponentID == componentId);
                if (component) {
                    SSE.currentComponentText = component.ComponentName;
                }
            } else {
                SSE.currentComponentId = null;
                SSE.currentComponentText = '';
            }
        });

        // Load students button
        $('#sse-load-students-btn').on('click', function() {
            SSE.validateAndLoadStudents();
        });

        SSE.setupButtonHandlers();
    };

    SSE.validateAndLoadStudents = function() {
        var courseId = $('#sse-course-select').val();
        var componentId = $('#sse-component-select').val();

        if (!courseId) {
            alert('Please select a course');
            $('#sse-course-select').focus();
            return;
        }

        if (!componentId) {
            alert('Please select a component');
            $('#sse-component-select').focus();
            return;
        }

        SSE.currentCourseId = parseInt(courseId);
        SSE.currentComponentId = parseInt(componentId);

        // Find course and component names for display
        var course = SSE.courses.find(c => c.CourseID == courseId);
        var component = SSE.components.find(c => c.ComponentID == componentId);

        if (course) SSE.currentCourseText = course.CourseName;
        if (component) SSE.currentComponentText = component.ComponentName;

        SSE.updateStatus('Loading students for ' + SSE.currentCourseText + ' - ' + SSE.currentComponentText);
        SSE.loadStudents();
    };

    SSE.setupButtonHandlers = function() {
        $('#sse-prev').on('click', function(e) {
            e.preventDefault();
            if (SSE.currentIndex > 0) {
                SSE.currentIndex--;
                SSE.loadCurrentStudent();
            }
        });

        $('#sse-skip').on('click', function(e) {
            e.preventDefault();
            if (SSE.currentIndex < SSE.students.length - 1) {
                SSE.currentIndex++;
                SSE.loadCurrentStudent();
            } else {
                SSE.showCompletion();
            }
        });

        $('#sse-save').on('click', function(e) {
            e.preventDefault();
            SSE.saveAndNext();
        });

        $('#sse-score-input').on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                SSE.saveAndNext();
            }
        });

        // Add input validation
        $('#sse-score-input').on('input', function() {
            var value = parseFloat($(this).val());
            if (value < 0) $(this).val(0);
            if (value > 100) $(this).val(100);
        });
    };

    SSE.enableSequential = function() {
        SSE.log('Enabling sequential mode');
        $('#sse-progress').slideDown();
        $('.wpda-pp-container').hide();

        // Update course info display
        if (SSE.currentCourseText && SSE.currentComponentText) {
            $('#sse-course-info').text(SSE.currentCourseText + ' - ' + SSE.currentComponentText);
        }

        // If students are loaded, show them
        if (SSE.studentsLoaded && SSE.students.length > 0) {
            SSE.loadCurrentStudent();
        }
    };

    SSE.disableSequential = function() {
        SSE.log('Disabling sequential mode');
        $('#sse-progress').slideUp();
        $('.wpda-pp-container').show();
    };

    SSE.loadStudents = function() {
        if (!SSE.currentCourseId) {
            SSE.updateStatus('Error: No course selected');
            return;
        }

        if (SSE.isLoading) {
            SSE.log('Already loading students, please wait...');
            return;
        }

        SSE.isLoading = true;
        $('#sse-load-students-btn').prop('disabled', true).text('Loading...');
        $('#sse-student-name').text('Loading students...');

        SSE.log('Loading students for course ID: ' + SSE.currentCourseId);

        $.ajax({
            url: sse_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'sse_get_students',
                course_id: SSE.currentCourseId,
                nonce: sse_ajax.nonce
            },
            timeout: 30000,
            success: function(response) {
                SSE.isLoading = false;
                $('#sse-load-students-btn').prop('disabled', false).text('Load Students');

                console.log('[SSE] Students response:', response);

                if (response.success && response.data) {
                    if (Array.isArray(response.data) && response.data.length > 0) {
                        SSE.students = response.data.map(function(s) {
                            return {
                                id: s.StudentID,
                                name: s.FullName,
                                firstName: s.FirstName,
                                lastName: s.LastName,
                                enrollmentStatus: s.EnrollmentStatus
                            };
                        });

                        SSE.currentIndex = 0;
                        SSE.studentsLoaded = true;
                        $('#sse-total').text(SSE.students.length);
                        $('#sse-score-section').show();
                        $('#sse-completion').hide();

                        // Update course info
                        $('#sse-course-info').text(SSE.currentCourseText + ' - ' + SSE.currentComponentText);

                        SSE.updateStatus('Loaded ' + SSE.students.length + ' students successfully');
                        SSE.log('Loaded ' + SSE.students.length + ' students');

                        // Auto-enable sequential mode if not already enabled
                        if (!SSE.sequentialMode) {
                            $('#sse-toggle').prop('checked', true).trigger('change');
                        } else {
                            SSE.loadCurrentStudent();
                        }
                    } else {
                        var errorMsg = 'No students found for this course';
                        $('#sse-student-name').text(errorMsg);
                        $('#sse-score-section').hide();
                        SSE.updateStatus(errorMsg);
                        SSE.log('No students found in response');
                    }
                } else {
                    var errorMsg = response.data || 'No students found for this course';
                    $('#sse-student-name').text(errorMsg);
                    $('#sse-score-section').hide();
                    SSE.updateStatus(errorMsg);
                    SSE.log('Error in response:', response);
                }
            },
            error: function(xhr, status, error) {
                SSE.isLoading = false;
                $('#sse-load-students-btn').prop('disabled', false).text('Load Students');

                SSE.error('Students AJAX error:', { status: status, error: error });
                console.error('[SSE] AJAX Response:', xhr.responseText);

                var errorMsg = 'Error loading students: ' + error;
                $('#sse-student-name').text(errorMsg);
                $('#sse-score-section').hide();
                SSE.updateStatus(errorMsg);
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

        $('#sse-current').text(SSE.currentIndex + 1);
        $('#sse-student-name').text(student.name);
        $('#sse-score-input').val('').focus();

        var progress = ((SSE.currentIndex + 1) / SSE.students.length) * 100;
        $('#sse-progress-bar').css('width', progress + '%');

        $('#sse-prev').prop('disabled', SSE.currentIndex === 0);

        if (SSE.currentIndex === SSE.students.length - 1) {
            $('#sse-skip').text('Finish →');
        } else {
            $('#sse-skip').text('Skip →');
        }

        SSE.log('Current student:', student);
    };

    SSE.saveAndNext = function() {
        if (SSE.isSaving) {
            SSE.log('Already saving, please wait...');
            return;
        }

        var score = $('#sse-score-input').val();
        if (!score || score === '') {
            alert('Please enter a score');
            $('#sse-score-input').focus();
            return;
        }

        // Validate score range
        score = parseFloat(score);
        if (score < 0 || score > 100) {
            alert('Score must be between 0 and 100');
            $('#sse-score-input').focus();
            return;
        }

        var student = SSE.students[SSE.currentIndex];

        SSE.isSaving = true;
        $('#sse-save').prop('disabled', true).text('Saving...');

        $.ajax({
            url: sse_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'sse_save_score',
                student_id: student.id,
                component_id: SSE.currentComponentId,
                course_id: SSE.currentCourseId,
                score: score,
                notes: '',
                nonce: sse_ajax.nonce
            },
            timeout: 30000,
            success: function(response) {
                SSE.isSaving = false;
                $('#sse-save').prop('disabled', false).text('Save & Next →');

                console.log('[SSE] Save response:', response);

                if (response.success) {
                    SSE.log('Score saved successfully for student ' + student.name + ': ' + score);

                    if (SSE.currentIndex < SSE.students.length - 1) {
                        SSE.currentIndex++;
                        SSE.loadCurrentStudent();
                    } else {
                        SSE.showCompletion();
                    }
                } else {
                    var errorMsg = response.data || 'Unknown error';
                    alert('Error saving score: ' + errorMsg);
                    SSE.error('Save error:', errorMsg);
                }
            },
            error: function(xhr, status, error) {
                SSE.isSaving = false;
                $('#sse-save').prop('disabled', false).text('Save & Next →');

                var errorMsg = 'Failed to save score: ' + error;
                alert(errorMsg);
                SSE.error('Save error:', { status: status, error: error });
                console.error('[SSE] AJAX Response:', xhr.responseText);
            }
        });
    };

    SSE.showCompletion = function() {
        $('#sse-student-name').text('All students completed! 🎉');
        $('#sse-score-section').hide();
        $('#sse-completion').show();
        $('#sse-progress-bar').css('width', '100%');
        SSE.updateStatus('Session complete - all ' + SSE.students.length + ' students have been scored');
        SSE.log('Session completed successfully');
    };

})(jQuery);