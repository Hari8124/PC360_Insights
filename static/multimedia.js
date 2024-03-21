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

document.addEventListener("DOMContentLoaded", function () {
    // Fetch multimedia device data from the Flask route
    fetch('/api/multimedia-data')
        .then(response => response.json())
        .then(data => {
            // Call a function to populate the table with the received data
            populateMultimediaTable(data);
        })
        .catch(error => {
            console.error('Error fetching multimedia device data:', error);
        });

    // Function to populate the multimedia device table
    function populateMultimediaTable(data) {
        const tableBody = document.getElementById('multimedia-data');

        // Clear existing table rows
        tableBody.innerHTML = '';

        // Iterate through the multimedia device data and create table rows
        data.forEach(device => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${device.Name}</td>
                <td>${device.Manufacturer}</td>
            `;
            tableBody.appendChild(row);
        });
    }
});
