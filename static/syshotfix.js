// Get the system hotfixes data from the server (replace '/api/hotfix-data' with your Flask endpoint)
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

function getHotfixData() {
    fetch('/api/hotfix-data')  // Replace '/api/hotfix-data' with your Flask endpoint
        .then(response => response.json())
        .then(data => {
            // Get the table body element
            const tableBody = document.getElementById('hotfix-data');

            // Loop through the hotfix data and create rows
            data.forEach(hotfix => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${hotfix['Description']}</td>
                    <td>${hotfix['Hotfix ID']}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching system hotfixes data:', error));
}

// Call the function to populate system hotfixes data when the page loads
window.onload = getHotfixData;
