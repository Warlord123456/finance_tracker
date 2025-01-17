document.addEventListener('DOMContentLoaded', function () {
    const toggleButton = document.getElementById('darkModeToggle');
    const toggleText = document.getElementById('toggleText');
    const moonIcon = document.getElementById('moon-icon');
    const sunIcon = document.getElementById('sun-icon');

    // Check if dark mode is enabled in local storage
    if (localStorage.getItem('dark-mode') === 'enabled') {
        document.body.classList.add('dark-mode');
        toggleText.textContent = 'Light Mode';
        moonIcon.classList.remove('fade-in');
        moonIcon.classList.add('fade-out');
        sunIcon.classList.remove('fade-out');
        sunIcon.classList.add('fade-in');
    }

    // Toggle button event listener for dark mode
    toggleButton.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');

        if (document.body.classList.contains('dark-mode')) {
            toggleText.textContent = 'Light Mode';
            localStorage.setItem('dark-mode', 'enabled');
            moonIcon.classList.remove('fade-in');
            moonIcon.classList.add('fade-out');
            sunIcon.classList.remove('fade-out');
            sunIcon.classList.add('fade-in');
        } else {
            toggleText.textContent = 'Dark Mode';
            localStorage.setItem('dark-mode', 'disabled');
            moonIcon.classList.remove('fade-out');
            moonIcon.classList.add('fade-in');
            sunIcon.classList.remove('fade-in');
            sunIcon.classList.add('fade-out');
        }
    });
});
