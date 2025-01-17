const ctx = document.getElementById('expenseChart').getContext('2d');
const loadingSpinner = document.getElementById('loadingSpinner');
let expenseChart;

// Create Chart Function
function createChart(chartType) {
    const labels = {{ category_labels | tojson | default('[]') }};
    const data = {{ category_data | tojson | default('[]') }};

    loadingSpinner.style.display = 'block'; // Show loading spinner

    if (expenseChart) {
        expenseChart.destroy(); // Destroy previous chart instance
    }

    let chartOptions = {
        type: chartType,
        data: {
            labels: labels,
            datasets: [{
                label: 'Expenses by Category',
                data: data,
                backgroundColor: [
                    '#FF6384',
                    '#1877F2',
                    '#FFCE56',
                    '#4caf50',
                    '#ff9800',
                    '#9c27b0',
                    '#d9b6a3',
                    '#b88e27',
                    '#f3bf97',
                    '#872419',
                    '#c4ac8d',
                    '#ccb49c',
                ],
                hoverOffset: 10,
                borderColor: '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                        },
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.raw;
                            return label;
                        },
                        title: function (tooltipItems) {
                            return tooltipItems[0].label;
                        }
                    },
                },
            },
            animation: {
                animateScale: true,
                animateRotate: true,
            }
        }
    };

    if (chartType === 'line') {
        chartOptions.data.datasets[0].borderColor = '#4caf50';
        chartOptions.data.datasets[0].backgroundColor = 'rgba(76, 175, 80, 0.2)';
        chartOptions.data.datasets[0].borderWidth = 3;
        chartOptions.options.elements = {
            line: {
                tension: 0.4
            }
        };
    }

    expenseChart = new Chart(ctx, chartOptions);
    loadingSpinner.style.display = 'none'; // Hide loading spinner
}

// Particles.js configuration function
function initParticles() {
    const isDarkMode = document.body.classList.contains('dark-mode');
    const particleColor = isDarkMode ? "#ffffff" : "#000000"; // White for dark mode, black for light mode

    particlesJS("particles-js", {
        "particles": {
            "number": {
                "value": 120,
                "density": {
                    "enable": true,
                    "value_area": 800
                }
            },
            "color": {
                "value": particleColor
            },
            "shape": {
                "type": "circle",
                "stroke": {
                    "width": 0,
                    "color": "#000000"
                },
                "polygon": {
                    "nb_sides": 5
                }
            },
            "opacity": {
                "value": 0.5,
                "random": false,
                "anim": {
                    "enable": false,
                    "speed": 1,
                    "opacity_min": 0.1,
                    "sync": false
                }
            },
            "size": {
                "value": 3,
                "random": true,
                "anim": {
                    "enable": false,
                    "speed": 40,
                    "size_min": 0.1,
                    "sync": false
                }
            },
            "line_linked": {
                "enable": true,
                "distance": 150,
                "color": particleColor,
                "opacity": 0.4,
                "width": 1
            },
            "move": {
                "enable": true,
                "speed": 6,
                "direction": "none",
                "random": false,
                "straight": false,
                "out_mode": "out",
                "bounce": false,
                "attract": {
                    "enable": false,
                    "rotateX": 600,
                    "rotateY": 1200
                }
            }
        },
        "interactivity": {
            "detect_on": "canvas",
            "events": {
                "onhover": {
                    "enable": true,
                    "mode": "repulse"
                },
                "onclick": {
                    "enable": true,
                    "mode": "push"
                },
                "resize": true
            },
            "modes": {
                "grab": {
                    "distance": 400,
                    "line_linked": {
                        "opacity": 1
                    }
                },
                "bubble": {
                    "distance": 400,
                    "size": 40,
                    "duration": 2,
                    "opacity": 8,
                    "speed": 3
                },
                "repulse": {
                    "distance": 200,
                    "duration": 0.4
                },
                "push": {
                    "particles_nb": 4
                },
                "remove": {
                    "particles_nb": 2
                }
            }
        },
        "retina_detect": true
    });
}

// Dark Mode toggle
const darkModeToggle = document.getElementById('toggleDarkMode');
const darkModeIcon = document.getElementById('darkModeIcon');
const toggleText = document.getElementById('toggleText');

darkModeToggle.addEventListener('click', function () {
    document.body.classList.toggle('dark-mode');
    initParticles(); // Re-initialize particles on dark mode toggle

    if (document.body.classList.contains('dark-mode')) {
        darkModeIcon.classList.remove('fa-moon');
        darkModeIcon.classList.add('fa-sun');
        toggleText.textContent = 'Switch to Light Mode';
    } else {
        darkModeIcon.classList.remove('fa-sun');
        darkModeIcon.classList.add('fa-moon');
        toggleText.textContent = 'Switch to Dark Mode';
    }

    const chartType = document.querySelector('.dropdown-item.active') ? document.querySelector('.dropdown-item.active').dataset.value : 'pie';
    createChart(chartType);
});

// Dropdown selection
document.addEventListener('DOMContentLoaded', function () {
    const dropdownToggle = document.getElementById('dropdownMenuButton');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    dropdownToggle.addEventListener('click', function () {
        dropdownMenu.classList.toggle('show');
        dropdownToggle.setAttribute('aria-expanded', dropdownMenu.classList.contains('show'));
    });

    // Close the dropdown when clicking outside of it
    window.addEventListener('click', function (event) {
        if (!dropdownToggle.contains(event.target) && !dropdownMenu.contains(event.target)) {
            dropdownMenu.classList.remove('show');
            dropdownToggle.setAttribute('aria-expanded', 'false');
        }
    });

    // Handle selection of dropdown items
    document.querySelectorAll('.dropdown-item').forEach(item => {
        item.addEventListener('click', function () {
            const chartType = this.dataset.value;
            createChart(chartType);
            dropdownMenu.classList.remove('show');
            dropdownToggle.setAttribute('aria-expanded', 'false');
        });
    });
});

initParticles(); // Initialize particles on page load
