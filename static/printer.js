// Get the printer data from the server (you can use an API endpoint to fetch this data)
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

function getPrinterData() {
    fetch('/api/printer-data')  // Replace '/get_printer_data' with your Flask endpoint
        .then(response => response.json())
        .then(data => {
            // Get the table body element
            const tableBody = document.getElementById('printer-data');

            // Loop through the printer data and create rows
            data.forEach(printer => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${printer['Printer Name']}</td>
                    <td>${printer['Default Status']}</td>
                    <td>${printer['Network Status']}</td>
                    <td>${printer['Port Number']}</td>
                `;
                tableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching printer data:', error));
}

// Call the function to populate printer data when the page loads
window.onload = getPrinterData;
