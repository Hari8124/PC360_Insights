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

function fetchHostnameInformation() {
    fetch('/api/hostname-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('hostname').textContent = data.Hostname;
        })
        .catch(error => console.error('Error in fetchHostnameInformation:', error));
}

function fetchUsernameInformation() {
    fetch('/api/username-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('username').textContent = data.Username;
        })
        .catch(error => console.error('Error in fetchUsernameInformation:', error));
}

function fetchSystemTypeInformation() {
    fetch('/api/system-type-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('department').textContent = data.SystemType;
        })
        .catch(error => console.error('Error in fetchSystemTypeInformation:', error));
}

function fetchCpuModelInformation() {
    fetch('/api/cpu-model-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cpu-model').textContent = data.CpuModel;
        })
        .catch(error => console.error('Error in fetchCpuModelInformation:', error));
}

function fetchChassisInformation() {
    fetch('/api/chassis-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('chassis').textContent = data.Chassis;
        })
        .catch(error => console.error('Error in fetchChassisInformation:', error));
}

function fetchMacAddressInformation() {
    fetch('/api/mac-address-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('mac-address').textContent = data.MacAddress;
        })
        .catch(error => console.error('Error in fetchMacAddressInformation:', error));
}

function fetchOperatingSystemInformation() {
    fetch('/api/os-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('os').textContent = data.OperatingSystem;
        })
        .catch(error => console.error('Error in fetchOperatingSystemInformation:', error));
}

function fetchUptimeInformation() {
    fetch('/api/uptime-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('uptime').textContent = data.Uptime;
        })
        .catch(error => console.error('Error in fetchUptimeInformation:', error));
}

function fetchInstalledApplicationsInformation() {
    fetch('/api/software-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-software-count').textContent = data.TotalInstalledSoftwares;
        })
        .catch(error => console.error('Error in fetchInstalledApplicationsInformation:', error));
}

function fetchMonitorInformation() {
    fetch('/api/monitor-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('monitor').textContent = data.Monitor;
        })
        .catch(error => console.error('Error in fetchMonitorInformation:', error));
}

function fetchComputerAgeInformation() {
    fetch('/api/computer-age-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('computer-age').textContent = data.ComputerAge;
        })
        .catch(error => console.error('Error in fetchComputerAgeInformation:', error));
}

window.onload = function () {
    fetchHostnameInformation();
    fetchUsernameInformation();
    fetchSystemTypeInformation();
    fetchCpuModelInformation();
    fetchChassisInformation();
    fetchMacAddressInformation();
    fetchOperatingSystemInformation();
    fetchUptimeInformation();
    fetchInstalledApplicationsInformation();
    fetchMonitorInformation();
    fetchComputerAgeInformation();
};
