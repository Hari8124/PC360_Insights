// sysprofile.js
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


function fetchSystemProfileData() {
    fetch('/api/system-profile-arch-data')
        .then(response => response.json())
        .then(data => {
            document.getElementById('computer-id').textContent = data.ComputerID;
            document.getElementById('hostname').textContent = data.Hostname;
            document.getElementById('username').textContent = data.Username;
            document.getElementById('uptime').textContent = data.Uptime;
            document.getElementById('computer-age').textContent = data.ComputerAge;

            // Display monitor information
            document.getElementById('monitor-name').textContent = data.MonitorName;
            document.getElementById('monitor-manufacturer').textContent = data.MonitorManufacturer;
            document.getElementById('monitor-product-code').textContent = data.MonitorProductCode;
            document.getElementById('monitor-serial-number').textContent = data.MonitorSerialNumber;
            
            // Display monitor information
            document.getElementById('cpu-model').textContent = data.CpuModel;
            document.getElementById('system-type').textContent = data.SystemType;
            document.getElementById('os-name').textContent = data.OsName;
            document.getElementById('os-version').textContent = data.OsVersion;
            document.getElementById('os-manufacturer').textContent = data.OsManufacturer;
            document.getElementById('os-configuration').textContent = data.OsConfiguration;
            document.getElementById('os-build-type').textContent = data.OsBuildType;
            document.getElementById('os-install-date').textContent = data.OsInstallDate;
            document.getElementById('product-id').textContent = data.ProductId;
            document.getElementById('product-key').textContent = data.ProductKey;
            document.getElementById('processor').textContent = data.Processor;

            // Display Motherboard information
            document.getElementById('motherboard-manufacturer').textContent = data.MotherboardManufacturer;
            document.getElementById('motherboard-product').textContent = data.MotherboardProduct;
            document.getElementById('motherboard-version').textContent = data.MotherboardVersion;

            // Display Memory Information
            document.getElementById('total-memory').textContent = data.TotalMemory;
            document.getElementById('available-memory').textContent = data.AvailableMemory;
            document.getElementById('used-memory').textContent = data.UsedMemory;
            document.getElementById('memory-usage-percentage').textContent = data.MemoryUsagePercentage;
        })
        .catch(error => console.error('Error fetching system profile arch data:', error));
}

// Call the fetchSystemProfileData() function when your page loads or as needed
window.onload = fetchSystemProfileData;
