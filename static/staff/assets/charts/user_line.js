$(document).ready(function() {
    var endpoint = '/staff/get-user-activities/';
    var student = [];
    var teacher = [];
    var labels = [];
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function (data) {
            labels = data.date_label;
            student = data.student;
            teacher = data.teacher;

            var ctx = $("#activities-line");
            var lineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: teacher,
                        label: 'Teachers',
                        showLine: true,
                        borderColor: '#5DA2D5',
                        backgroundColor: 'rgba(93, 162, 213, 0.4)',
                        pointBorderColor: '#5DA2D5',
                        pointHoverBackgroundColor: 'rgba(255,255,255, 1)',
                        pointHoverBorderWidth: 2,
                        pointHoverRadius: 10,
                        borderWidth: 5,
                        yAxisID: 'teachers'
                    }, {
                        data: student,
                        label: 'Students',
                        showLine: true,
                        borderColor: '#F78888',
                        backgroundColor: 'rgba(247, 136, 136, 0.4)',
                        pointBorderColor: '#F78888',
                        pointHoverBackgroundColor: 'rgba(255,255,255, 1)',
                        pointHoverBorderWidth: 2,
                        pointHoverRadius: 10,
                        borderWidth: 5,
                        yAxisID: 'students'
                    }]
                },
                options: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            },
                            gridLines: {
                                color: 'rgba(0, 0, 0, 0)',
                            },
                            type: 'linear',
                            display: true,
                            position: 'left',
                            id: 'teachers'
                        }, {
                            ticks: {
                                beginAtZero: true
                            },
                            gridLines: {
                                color: 'rgba(0, 0, 0, 0)',
                            },
                            type: 'linear',
                            display: true,
                            position: 'right',
                            id: 'students'
                        }]
                    }
                }
            });
        },
        error: function (error_data) {
            console.log("error");
            console.log(error_data);
        }
    });
});