# PC360 Insights – Intelligent System Inventory & Diagnostics

**PC360 Insights** is a scalable system diagnostics and inventory tool built in Python, designed to gather detailed hardware, software, and network information from Windows machines and store it in a structured MySQL database. It was developed during a hands-on internship at Integral Coach Factory (ICF), under the IT Centre’s initiative to modernize asset tracking across departments.

## Why This Matters

Managing system infrastructure at scale demands automation, precision, and extensibility. PC360 automates comprehensive system audits, enabling IT teams to track, monitor, and manage PC assets efficiently — reducing downtime, enabling audits, and driving better infrastructure decisions.

## What It Does

- Collects deep system-level info: CPU, memory, OS, disk, BIOS, printers, users, apps, hotfixes, etc.
- Maps network segments to departments using IP subnet logic
- Stores data persistently in MySQL, with versioning and archival
- Ultra-fast using `wmi`, `psutil`, and native Windows APIs
- Easily extensible with modular Python functions and DB inserts

## Built With

| Stack       | Tech                     |
|-------------|---------------------------|
| Backend     | Python, Flask             |
| OS Access   | `wmi`, `psutil`, `subprocess`, `win32*` modules |
| DB Layer    | MySQL (`mysql.connector`) |
| Deployment  | Windows (ICF Internal Network) |

## Key Modules (Simplified)

- `gather_system_info()` – central pipeline that collects and structures 60+ data points
- `generate_computer_id()` – unique asset ID assignment based on MAC address
- `insert_*_to_db()` – individual handlers for inserting applications, partitions, printers, shared folders, and more into MySQL
- `fetch_department_counts()` – intelligently associates PCs with departments using IP segment mapping


## Example Use Case

```python
from PC360_Insights import gather_system_info
data = gather_system_info()
print(data["computer_id"], data["total_installed_applications"])
```

### Screenshots

Here are some screenshots of PC360 Insights in action:

![Image 1](https://drive.google.com/uc?export=view&id=1Nx1OysyqPuoJDAKKrLdaP_XZOVqb9TJD)  
![Image 2](https://drive.google.com/uc?export=view&id=1ZCQ62qPC-ce25lss_MWeWCs_J51WGxdT)  
![Image 3](https://drive.google.com/uc?export=view&id=1deMf5O5FHdqGJo2eHNNID9-rovbTcML9)  

## Why It Stands Out
- Parallelized registry parsing for faster app discovery
- Robust error handling for all hardware queries
- Automatic department classification via IP mapping
- Modular and scalable: built for easy integration with larger IT systems

## Potential Add-ons
- Real-time dashboard with Plotly/Chart.js
- Scheduled scans & automated reporting
- Role-based user access and admin tools
- Remote execution over enterprise LAN
