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

// Function to fetch and populate Antivirus information
function fetchAntivirusInformation() {
    fetch('/api/antivirus-data')  // Replace '/api/antivirus-data' with your Flask endpoint
        .then(response => response.json())
        .then(data => {
            // Get the elements by their IDs
            const statusElement = document.getElementById('antivirus-status');
            const nameElement = document.getElementById('antivirus-name');
            const versionElement = document.getElementById('antivirus-version');
            const publisherElement = document.getElementById('antivirus-publisher');
            const installDateElement = document.getElementById('antivirus-install-date');

            // Populate the elements with data
            statusElement.textContent = data.AntivirusStatus;
            nameElement.textContent = data.AntivirusName;
            versionElement.textContent = data.AntivirusVersion;
            publisherElement.textContent = data.AntivirusPublisher;
            installDateElement.textContent = data.AntivirusInstallDate;
        })
        .catch(error => console.error('Error fetching Antivirus information:', error));
}

// Call the function to populate Antivirus information when the page loads
window.onload = fetchAntivirusInformation;
