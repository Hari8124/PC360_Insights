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

function fetchComputerIdInformation() {
    fetch('/api/computer-id-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('computer-id').textContent = data.ComputerId;
        })
        .catch(error => console.error('Error in fetchComputerIdInformation:', error));
}

function fetchHostnameInformation() {
    fetch('/api/hostname-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('hostname').textContent = data.Hostname;
        })
        .catch(error => console.error('Error in fetchHostnameInformation:', error));
}

function fetchIpAddressInformation() {
    fetch('/api/ip-address-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('ip-address').textContent = data.IPAddress;
        })
        .catch(error => console.error('Error in fetchIpAddressInformation:', error));
}

function fetchDepartmentInformation() {
    fetch('/api/department-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('department').textContent = data.Department;
        })
        .catch(error => console.error('Error in fetchDepartmentInformation:', error));
}

function fetchOsInformation() {
    fetch('/api/os-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('os').textContent = data.OperatingSystem;
        })
        .catch(error => console.error('Error in fetchOsInformation:', error));
}

function fetchRamInformation() {
    fetch('/api/ram-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('ram').textContent = data.RAM;
        })
        .catch(error => console.error('Error in fetchRamInformation:', error));
}

function fetchMonitorInformation() {
    fetch('/api/monitor-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('monitor').textContent = data.Monitor;
        })
        .catch(error => console.error('Error in fetchMonitorInformation:', error));
}

function fetchMacAddressInformation() {
    fetch('/api/mac-address-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('mac-address').textContent = data.MacAddress;
        })
        .catch(error => console.error('Error in fetchMacAddressInformation:', error));
}

function fetchChassisInformation() {
    fetch('/api/chassis-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('chassis').textContent = data.Chassis;
        })
        .catch(error => console.error('Error in fetchChassisInformation:', error));
}

function fetchUptimeInformation() {
    fetch('/api/uptime-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('uptime').textContent = data.Uptime;
        })
        .catch(error => console.error('Error in fetchUptimeInformation:', error));
}

function fetchComputerAgeInformation() {
    fetch('/api/computer-age-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('computer-age').textContent = data.ComputerAge;
        })
        .catch(error => console.error('Error in fetchComputerAgeInformation:', error));
}

// Continue adding similar functions for other data points as needed

window.onload = function () {
    fetchComputerIdInformation();
    fetchHostnameInformation();
    fetchIpAddressInformation();
    fetchDepartmentInformation();
    fetchOsInformation();
    fetchRamInformation();
    fetchMonitorInformation();
    fetchMacAddressInformation();
    fetchChassisInformation();
    fetchUptimeInformation();
    fetchComputerAgeInformation();
    // Add calls to other functions for additional data points
};

