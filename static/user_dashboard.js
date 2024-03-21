


function fetchSystemInformation() {
  fetch('/api/system-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('mac-info').textContent = data.MacAddress;
      })
      .catch(error => console.error('Error in fetchSystemInformation:', error));
}

function fetchSoftwareInformation() {
  fetch('/api/software-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-software-count').textContent = data.TotalInstalledSoftwares;
      })
      .catch(error => console.error('Error in fetchSoftwareInformation:', error));
}

function fetchBiosInformation() {
  fetch('/api/bios-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('bios-serial').textContent = data.BiosSerialNumber;
      })
      .catch(error => console.error('Error in fetchBiosInformation:', error));
}

function fetchLocalUsersInformation() {
  fetch('/api/local-users-info')
      .then(response => response.text()) // Parse response as text
      .then(data => {
          document.getElementById('total-local-users').textContent = data;
      })
      .catch(error => console.error('Error in fetchLocalUsersInformation:', error));
}

function fetchMemorySlotInformation() {
  fetch('/api/memory-slot-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-memory-slots').textContent = data.TotalMemorySlots;
      })
      .catch(error => console.error('Error in fetchMemorySlotInformation:', error));
}

function fetchMultimediaInformation() {
  fetch('/api/multimedia-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-multimedia-devices').textContent = data.TotalMultimediaDevices;
      })
      .catch(error => console.error('Error in fetchMultimediaInformation:', error));
}

function fetchCDRomInformation() {
  fetch('/api/cd-rom-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-cdroms').textContent = data.TotalCDROMs;
      })
      .catch(error => console.error('Error in fetchCDRomInformation:', error));
}

function fetchPrinterInformation() {
  fetch('/api/printer-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-printers').textContent = data.TotalPrinters;
      })
      .catch(error => console.error('Error in fetchPrinterInformation:', error));
}

function fetchSharedFolderInformation() {
  fetch('/api/shared-folder-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-shared-folders').textContent = data.TotalSharedFolders;
      })
      .catch(error => console.error('Error in fetchSharedFolderInformation:', error));
}

function fetchDiskInformation() {
  fetch('/api/disk-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-free-space-percentage').textContent = data.TotalFreeSpacePercentage;
      })
      .catch(error => console.error('Error in fetchDiskInformation:', error));
}

function fetchSystemProfileInformation() {
  fetch('/api/system-profile-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('hostname').textContent = data.Hostname;
      })
      .catch(error => console.error('Error in fetchSystemProfileInformation:', error));
}

function fetchNetworkAdapterInformation() {
  fetch('/api/network-adapter-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('ip-address').textContent = data.IPAddress;
      })
      .catch(error => console.error('Error in fetchNetworkAdapterInformation:', error));
}

function fetchStartupConfigInformation() {
  fetch('/api/startup-config-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-startup-apps').textContent = data.TotalStartupApplications;
      })
      .catch(error => console.error('Error in fetchStartupConfigInformation:', error));
}

function fetchSystemPatchHistory() {
  fetch('/api/system-patch-history')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-update-history').textContent = data.TotalUpdateHistory;
      })
      .catch(error => console.error('Error in fetchSystemPatchHistory:', error));
}

function fetchPartitionInformation() {
  fetch('/api/partition-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('total-partitions').textContent = data.TotalPartitions;
      })
      .catch(error => console.error('Error in fetchPartitionInformation:', error));
}

function fetchUpdateInformation() {
  fetch('/api/update-info')
      .then(response => response.json())
      .then(data => {
          document.getElementById('update-required').textContent = data.UpdateRequired;
      })
      .catch(error => console.error('Error in fetchUpdateInformation:', error));
}

function fetchSystemProfileHistory() {
  fetch('/api/system-profile-history')
      .then(response => response.json())
      .then(data => {
          document.getElementById('histories').textContent = data.Histories;
      })
      .catch(error => console.error('Error in fetchSystemProfileHistory:', error));
}

function fetchAntivirusStatus() {
  fetch('/api/antivirus-status')
      .then(response => response.json())
      .then(data => {
          document.getElementById('antivirus-installed').textContent = data.AntivirusInstalled;
      })
      .catch(error => console.error('Error in fetchAntivirusStatus:', error));
}

window.onload = function () {
  fetchSystemInformation();
  fetchSoftwareInformation();
  fetchBiosInformation();
  fetchLocalUsersInformation();
  fetchMemorySlotInformation();
  fetchMultimediaInformation();
  fetchCDRomInformation();
  fetchPrinterInformation();
  fetchSharedFolderInformation();
  fetchDiskInformation();
  fetchSystemProfileInformation();
  fetchNetworkAdapterInformation();
  fetchStartupConfigInformation();
  fetchSystemPatchHistory();
  fetchPartitionInformation();
  fetchUpdateInformation();
  fetchSystemProfileHistory();
  fetchAntivirusStatus();
};
