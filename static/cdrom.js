// cdrom.js
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


function fetchCdRomData() {
    fetch('/api/cdrom-data')
        .then(response => response.json())
        .then(data => {
            const cdromData = document.getElementById('cdrom-data');
            cdromData.innerHTML = ''; // Clear any existing data

            // Check if all values are unavailable
            const allUnavailable = data.every(cdrom => {
                return (
                    cdrom['Drive Letter'] === 'Unavailable' &&
                    cdrom['Name'] === 'Unavailable' &&
                    cdrom['Manufacturer'] === 'Unavailable' &&
                    cdrom['Media Loaded'] === 'Unavailable' &&
                    cdrom['Media Type'] === 'Unavailable' &&
                    cdrom['Volume Name'] === 'Unavailable'
                );
            });

            if (allUnavailable) {
                // If all values are unavailable, display a message
                cdromData.innerHTML = '<tr><td colspan="6">No CD/DVD-ROM drives found.</td></tr>';
            } else {
                // Otherwise, populate the table with CD/DVD-ROM drive data
                data.forEach(cdrom => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${cdrom['Drive Letter']}</td>
                        <td>${cdrom['Name']}</td>
                        <td>${cdrom['Manufacturer']}</td>
                        <td>${cdrom['Media Loaded']}</td>
                        <td>${cdrom['Media Type']}</td>
                        <td>${cdrom['Volume Name']}</td>
                    `;
                    cdromData.appendChild(row);
                });
            }
        })
        .catch(error => console.error('Error fetching CD/DVD-ROM drive info:', error));
}

// Call the fetchCdRomData() function when your page loads or as needed
window.onload = fetchCdRomData;
