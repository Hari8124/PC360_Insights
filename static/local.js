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
    // Fetch local user account data from the Flask route
    fetch('/api/local-info')
        .then(response => response.json())
        .then(localUserData => {
            // Call a function to populate the local user accounts table with the received data
            populateLocalUserAccountsTable(localUserData);
        })
        .catch(error => {
            console.error('Error fetching local user accounts data:', error);
        });

    // Function to populate the local user accounts table
    function populateLocalUserAccountsTable(data) {
        const tableBody = document.getElementById('local-user-accounts-data');

        // Clear existing table rows
        tableBody.innerHTML = '';

        // Iterate through the local user accounts data and create table rows
        data.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.Name}</td>
                <td>${user.Domain}</td>
                <td>${user.Description}</td>
                <td>${user.Status}</td>
            `;
            tableBody.appendChild(row);
        });
    }
});
