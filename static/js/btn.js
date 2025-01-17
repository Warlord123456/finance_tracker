document.addEventListener('DOMContentLoaded', function () {
            const toggleButton = document.getElementById('darkModeToggle');
            const toggleText = document.getElementById('toggleText');
            const moonIcon = document.getElementById('moon-icon');
            const sunIcon = document.getElementById('sun-icon');
            const fileInput = document.getElementById('file-upload');
            const fileNameDisplay = document.getElementById('file-name');
            const sideNav = document.getElementById('mySideNav');
            const overlay = document.getElementById('overlay');

            // Check if dark mode is enabled in local storage
            if (localStorage.getItem('dark-mode') === 'enabled') {
                document.body.classList.add('dark-mode');
                toggleText.textContent = 'Light Mode';
                moonIcon.classList.remove('fade-in');
                moonIcon.classList.add('fade-out');
                sunIcon.classList.remove('fade-out');
                sunIcon.classList.add('fade-in');
            }

            // File input change event to show selected file name
            fileInput.addEventListener('change', function () {
                const fileName = fileInput.files.length > 0 ? fileInput.files[0].name : '';
                fileNameDisplay.textContent = fileName ? `: ${fileName}` : '';
            });

            // Open side navigation
            document.querySelector('.nav-toggle').addEventListener('change', function () {
                if (this.checked) {
                    openNav();
                } else {
                    closeNav();
                }
            });

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
