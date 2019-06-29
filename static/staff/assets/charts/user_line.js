$(document).ready(function() {
    var endpoint = '/staff/get-user-activities/';
    var defaultData = [];
    var labels = [];
    $.ajax({
        method: "GET",
        url: endpoint,
        success: function (data) {
            // labels = data.labels;
            // defaultData = data.default;


            for(var i in data) {
                labels.push(data[i].action_date);
                defaultData.push(data[i].action_count);
            }

            var ctx = $("#activities-line");
            var lineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: defaultData,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(255, 159, 64, 0.2)'
                        ],
                        borderColor: [
                            'rgba(255,99,132,1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    legend: {
                        display: false,
                    },
                    scales: {
                        yAxes: [{
                            ticks: {
                                beginAtZero: true
                            }
                        }]
                    },
                    tooltips: {
                        callbacks: {
                            label: function (tooltipItem, chartData) {
                                return ' Count of Activities: ' + chartData.datasets[0].data[tooltipItem.index];
                            }
                        }
                    },
                }
            });
        },
        error: function (error_data) {
            console.log("error");
            console.log(error_data)
        }
    });
});