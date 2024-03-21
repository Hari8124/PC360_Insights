// Function to fetch both disk information and mapped drive data from the server
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

function fetchData() {
    // Fetch disk information
    fetch('/api/disk-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-disk-space').textContent = data.TotalDiskSpace;
            document.getElementById('total-free-space').textContent = data.TotalFreeSpace;
            document.getElementById('total-partitions').textContent = data.TotalPartitions;
        })
        .catch(error => console.error('Error in fetchDiskInformation:', error));

    fetch('/api/disk-info')
        .then(response => response.json())
        .then(data => {
            const mappedDrivesElement = document.getElementById('mapped-data');
            mappedDrivesElement.innerHTML = ''; // Clear any existing data
    
            const mappedDrives = data['Mapped Network Drives'];
            if (mappedDrives && mappedDrives.length > 0) {
                mappedDrives.forEach(drive => {
                    if (drive['local'] === 'Unavailable' && drive['remote'] === 'Unavailable') {
                        // Both local and remote are 'Unavailable', do nothing
                    } else {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${drive['local']}</td>
                            <td>${drive['remote']}</td>
                        `;
                        mappedDrivesElement.appendChild(row);
                    }
                });
    
                // If all mapped drives had both local and remote as 'Unavailable', display a message
                if (mappedDrivesElement.childElementCount === 0) {
                    mappedDrivesElement.innerHTML = '<tr><td colspan="2">No mapped drives found.</td></tr>';
                }
            } else {
                // If no mapped drives are available, display a message
                mappedDrivesElement.innerHTML = '<tr><td colspan="2">No mapped drives found.</td></tr>';
            }
        })
        .catch(error => console.error('Error fetching Mapped drive info:', error));     
}

// Call the function to fetch data when the page loads
window.onload = fetchData;
