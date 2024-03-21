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

function fetchNetworkInfo() {
    fetch('/api/network-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('node-type').textContent = data.NodeType;
            document.getElementById('ip-routing-status').textContent = data.IpRoutingStatus;
            document.getElementById('wins-proxy-status').textContent = data.WinsProxyStatus;
            document.getElementById('lan-interface').textContent = data.LanInterface;
            document.getElementById('lan-description').textContent = data.LanDescription;
            document.getElementById('lan-speed').textContent = data.LanSpeed;
            document.getElementById('lan-mac-address').textContent = data.LanMacAddress;
            document.getElementById('ipv4-address').textContent = data.Ipv4Address;
            document.getElementById('ipv6-address').textContent = data.Ipv6Address;
            document.getElementById('subnet-mask').textContent = data.SubnetMask;
            document.getElementById('default-gateway').textContent = data.DefaultGateway;
            document.getElementById('netbios-status').textContent = data.NetbiosStatus;
            document.getElementById('autoconfiguration-status').textContent = data.AutoconfigurationStatus;
            document.getElementById('lease-obtained').textContent = data.LeaseObtained;
            document.getElementById('lease-expiry').textContent = data.LeaseExpiry;
            document.getElementById('dhcp-status').textContent = data.DhcpStatus;
            document.getElementById('dhcp-server').textContent = data.DhcpServer;
            document.getElementById('dns-server').textContent = data.DnsServer;
        })
        .catch(error => console.error('Error fetching network information:', error));
}

// Call the fetchNetworkInfo() function when your page loads or as needed
window.onload = fetchNetworkInfo;
