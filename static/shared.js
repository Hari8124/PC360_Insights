// Get the shared folder data from the server (use your Flask endpoint)
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

function getSharedFolderData() {
    fetch('/api/shared-data')  // Replace '/api/shared-data' with your Flask endpoint
        .then(response => response.json())
        .then(data => {
            // Get the table body element
            const tableBody = document.getElementById('shared-data');

            // Loop through the shared folder data and create rows
            data.forEach(folder => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${folder['Name']}</td>
                    <td>${folder['Caption']}</td>
                    <td>${folder['Path']}</td>
                    <td>${folder['Type']}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching shared folder data:', error));
}

// Call the function to populate shared folder data when the page loads
window.onload = getSharedFolderData;
