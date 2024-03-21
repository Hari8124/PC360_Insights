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
    // Fetch software data from the Flask route
    fetch('/api/software-data')
        .then(response => response.json())
        .then(data => {
            // console.log("Data received:", data); Log the data received from the fetch request
            // Call a function to populate the table with the received data
            populateSoftwareTable(data);
        })
        .catch(error => {
            console.error('Error fetching software data:', error); // Log any errors
        });

    // Function to populate the table
    function populateSoftwareTable(data) {
        const tableBody = document.getElementById('software-data');

        // Clear existing table rows
        tableBody.innerHTML = '';

        // Iterate through the software data and create table rows
        data.forEach(app => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${app.Name}</td>
                <td>${app.Version}</td>
                <td>${app.Publisher}</td>
                <td>${app.InstallDate}</td>
            `;
            tableBody.appendChild(row);
        });
    }
});
