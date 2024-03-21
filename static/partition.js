// Get the partition data from the server (replace '/api/partition-data' with your Flask endpoint)
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

function getPartitionData() {
    fetch('/api/partition-data')
        .then(response => response.json())
        .then(data => {
            const tableBody = document.getElementById('partition-data');

            // Loop through the partition data and create table rows
            for (const driveLetter in data) {
                if (data.hasOwnProperty(driveLetter)) {
                    const partition = data[driveLetter];
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${driveLetter}</td>
                        <td>${partition['Total Space']}</td>
                        <td>${partition['Free Space']}</td>
                    `;
                    tableBody.appendChild(row);
                }
            }
        })
        .catch(error => console.error('Error fetching partition data:', error));
}

// Call the function to populate partition data when the page loads
window.onload = getPartitionData;
