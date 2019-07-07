$(document).ready(function() {
    var course_status = [];
    var course_status_count = [];
    $.ajax({
        url: '/staff/get-course-status/',
        method: 'GET',
        success: function(data) {
            course_status = data.status_label;
            course_status_count = data.status_count;

            for (var i in course_status) {
                course_status[i] = course_status[i].charAt(0).toUpperCase() + course_status[i].slice(1);
            }

            console.log(course_status);

            var ctx = $("#course-status-donut");
            var donutChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: course_status,
                    datasets : [{
                        label: 'Course Status',
                        data: course_status_count,
                        // Course Status: , approved, deleted, pending, rejected
                        backgroundColor: [
                            '#5DA2D5',
                            '#ECECEC',
                            '#F3D250',
                            '#F78888'
                        ],
                        borderWidth: 1,
                        hoverBorderColor: 'rgba(0, 0, 0, 1)',
                        hoverBorderWidth: 4
                    }]
                },
                options: {
                    legend: {
                        position: 'bottom'
                    }
                }
            });
        },
        error: function(data) {
            console.log(data);
        }
    });
});
