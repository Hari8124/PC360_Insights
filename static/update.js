document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    // Function to close the dropdown menu
    function closeDropdown() {
        dropdownMenu.style.display = 'none';
        menuToggle.checked = false; // Uncheck the checkbox
        // Remove the click event listener on the document
        document.removeEventListener('click', closeDropdown);
    }

    // Function to open the dropdown menu
    function openDropdown() {
        dropdownMenu.style.display = 'block';

        // Add a click event listener to the document to close the dropdown
        document.addEventListener('click', closeDropdown);
    }

    menuToggle.addEventListener('change', function() {
        if (menuToggle.checked) {
            openDropdown();
        } else {
            closeDropdown();
        }
    });

    // Prevent clicks inside the dropdown menu from closing it
    dropdownMenu.addEventListener('click', function(event) {
        event.stopPropagation();
    });

    // Close the dropdown when the cursor leaves the menu
    dropdownMenu.addEventListener('mouseleave', closeDropdown);
});

// Function to fetch and populate update status data
function fetchUpdateStatus() {
    fetch('/api/update-data')
        .then(response => response.json())
        .then(data => {
            // Get the elements to populate the data
            const updateRequiredElement = document.getElementById('update-required');
            const lastCheckedElement = document.getElementById('last-checked');

            // Populate the data into the elements
            updateRequiredElement.textContent = data.UpdateRequired;
            lastCheckedElement.textContent = data.LastChecked;
        })
        .catch(error => console.error('Error fetching update status data:', error));
}

// Call the function to populate update status data when the page loads
window.onload = function () {
    fetchUpdateStatus();
}
