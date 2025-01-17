// Example: Simple animation on page load
window.onload = () => {
    const container = document.querySelector('.container');
    container.style.opacity = 0;
    setTimeout(() => {
        container.style.transition = 'opacity 1s ease';
        container.style.opacity = 1;
    }, 100);
};
