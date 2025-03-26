$(document).ready(function() {
    // Initialize date pickers
    if ($('#allocation_date').length) {
        $('#allocation_date').val(new Date().toISOString().substr(0, 10));
    }
    
    // Assignment page - Delete button functionality
    $('.delete-btn').click(function() {
        if (confirm('Are you sure you want to delete this assignment?')) {
            const id = $(this).data('id');
            $.ajax({
                url: '/api/assignment/' + id,
                type: 'DELETE',
                success: function(result) {
                    alert('Assignment deleted successfully');
                    location.reload();
                },
                error: function(error) {
                    alert('Error deleting assignment: ' + error.responseText);
                }
            });
        }
    });
    
    // Assignment page - Edit button functionality
    $('.edit-btn').click(function() {
        const id = $(this).data('id');
        $.ajax({
            url: '/api/assignment/' + id,
            type: 'GET',
            success: function(data) {
                $('#subject_id').val(data.subject_id);
                $('#teacher_id').val(data.teacher_id);
                $('#days').val(data.days);
                $('#time_slot').val(data.time_slot);
                
                // Change form action to update instead of create
                $('#assignmentForm').attr('action', '/course-faculty/assign/' + id + '/update');
                $('.box-title').html('<i class="fa fa-edit"></i> Edit Faculty Assignment');
                $('button[type="submit"]').html('<i class="fa fa-save"></i> Update Assignment');
            },
            error: function(error) {
                alert('Error loading assignment data: ' + error.responseText);
            }
        });
    });
    
    // Schedules page - Generate weekly schedule view
    if ($('#scheduleBody').length) {
        generateWeeklySchedule();
        
        // Filter schedules by class and section
        $('#filter_class, #filter_section').change(function() {
            generateWeeklySchedule();
        });
    }
    
    // Resources page - Add new resource modal
    $('#addResourceBtn').click(function() {
        $('#resourceModal').modal('show');
    });
    
    // Resources page - Save new resource
    $('#saveResourceBtn').click(function() {
        const resourceName = $('#resource_name').val();
        const totalQuantity = $('#total_quantity').val();
        
        if (!resourceName || !totalQuantity) {
            alert('Please fill all required fields');
            return;
        }
        
        $.ajax({
            url: '/api/resources',
            type: 'POST',
            data: {
                name: resourceName,
                total_quantity: totalQuantity
            },
            success: function(result) {
                alert('Resource added successfully');
                $('#resourceModal').modal('hide');
                location.reload();
            },
            error: function(error) {
                alert('Error adding resource: ' + error.responseText);
            }
        });
    });
    
    // Resource allocation - Edit functionality
    $('.edit-allocation-btn').click(function() {
        const id = $(this).data('id');
        $.ajax({
            url: '/api/allocation/' + id,
            type: 'GET',
            success: function(data) {
                $('#resource_id').val(data.resource_id);
                $('#subject_id').val(data.subject_id);
                $('#quantity').val(data.quantity);
                $('#allocation_date').val(data.allocation_date);
                $('#return_date').val(data.return_date || '');
                
                // Change form action to update instead of create
                $('#resourceForm').attr('action', '/course-faculty/resources/' + id + '/update');
                $('.box-title').html('<i class="fa fa-edit"></i> Edit Resource Allocation');
                $('button[type="submit"]').html('<i class="fa fa-save"></i> Update Allocation');
            },
            error: function(error) {
                alert('Error loading allocation data: ' + error.responseText);
            }
        });
    });
});

// Function to generate weekly schedule view
function generateWeeklySchedule() {
    const classId = $('#filter_class').val();
    const sectionId = $('#filter_section').val();
    
    $.ajax({
        url: '/api/schedules',
        type: 'GET',
        data: {
            class_id: classId,
            section_id: sectionId
        },
        success: function(schedules) {
            renderWeeklySchedule(schedules);
        },
        error: function(error) {
            console.error('Error fetching schedules:', error);
        }