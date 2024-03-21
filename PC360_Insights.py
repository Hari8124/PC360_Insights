import winreg
import datetime
import concurrent.futures
import win32com.client
import pytz
import wmi
import psutil
import subprocess
import win32net
import socket
import os
import mysql.connector
import win32print
import win32timezone
import ctypes
import ntplib
from flask import Flask, jsonify, render_template, send_file
import webbrowser

# Function to setup console
def setup_console():
    # Hide the console window
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    # Set the console title as early as possible
    ctypes.windll.kernel32.SetConsoleTitleW("PC360 Insights")

    # Show the console window again
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)

# Function to get installed applications and their versions
def get_installed_apps_with_versions():
    app={}
    try:    
        def process_subkey(asubkey):
            app = {}
            try:
                app['Name'] = winreg.QueryValueEx(asubkey, "DisplayName")[0]

                try:
                    app['Version'] = winreg.QueryValueEx(asubkey, "DisplayVersion")[0]
                except EnvironmentError:
                    app['Version'] = 'undefined'
                try:
                    app['Publisher'] = winreg.QueryValueEx(asubkey, "Publisher")[0]
                except EnvironmentError:
                    app['Publisher'] = 'undefined'

                try:
                    install_date_str = str(winreg.QueryValueEx(asubkey, "InstallDate")[0])
                    if install_date_str.strip():  # Check if the value is not empty or whitespace
                        app['InstallDate'] = datetime.datetime.strptime(install_date_str, "%Y%m%d").strftime("%Y-%m-%d")
                    else:
                        app['InstallDate'] = 'undefined'
                except (EnvironmentError, ValueError):
                    app['InstallDate'] = 'undefined'

                return app
            except EnvironmentError:
                return None
        
        def process_hive(hive, flag):
            aReg = winreg.ConnectRegistry(None, hive)
            aKey = winreg.OpenKey(aReg, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                                0, winreg.KEY_READ | flag)
            
            count_subkey = winreg.QueryInfoKey(aKey)[0]
            subkeys = [winreg.OpenKey(aKey, winreg.EnumKey(aKey, i)) for i in range(count_subkey)]
            
            apps = []
            
            # Use parallel processing to process subkeys concurrently
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = list(executor.map(process_subkey, subkeys))
            
            apps.extend(filter(None, results))  # Filter out None results
            
            return apps
        
        hive_32bit = winreg.HKEY_LOCAL_MACHINE
        hive_64bit = winreg.HKEY_LOCAL_MACHINE
        hive_current_user = winreg.HKEY_CURRENT_USER

        installed_apps_32bit = process_hive(hive_32bit, winreg.KEY_WOW64_32KEY)
        installed_apps_64bit = process_hive(hive_64bit, winreg.KEY_WOW64_64KEY)
        installed_apps_current_user = process_hive(hive_current_user, 0)

        installed_apps = installed_apps_32bit + installed_apps_64bit + installed_apps_current_user
        total_installed_apps = len(installed_apps)

        return installed_apps, total_installed_apps
    
    except Exception as e:
        print("Error in get_installed_apps_with_versions:", e)
        return [], 0 

# Function to get antivirus status
def get_antivirus_status():
    try:
        installed_apps, total_installed_apps = get_installed_apps_with_versions()
        #print("Total Installed Apps:", total_installed_apps)  # Debug print

        if installed_apps and isinstance(installed_apps, list):
            antivirus_status = {
                "Status": "Not Protected",  # Default status
                "Name": "Unavailable",
                "Version": "Unavailable",
                "Publisher": "Unavailable",
                "InstallDate": "Unavailable"
            }

            for app in installed_apps:
                if 'Chrome' in app['Name']:
                    antivirus_status["Status"] = 'Protected'
                    antivirus_status["Name"] = app['Name']
                    antivirus_status["Version"] = app['Version']
                    antivirus_status["Publisher"] = app['Publisher']
                    antivirus_status["InstallDate"] = app['InstallDate']

            return antivirus_status
        else:
            return None

    except Exception as e:
        print("Error in get_antivirus_status:", e)
        return None
       
# Function to insert application info to db
def insert_application_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        installed_apps, _ = get_installed_apps_with_versions()
        date = get_custom_date()
        
        for app in installed_apps:
            application_name = app["Name"]
            version = app["Version"]
            publisher = app["Publisher"]
            install_date = app["InstallDate"]

            insert_query = (
                "INSERT INTO app_catalog (computer_id, application_name, version, publisher, install_date, date) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            values = (comp_id, application_name, version, publisher, install_date, date)

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Installed applications details inserted into app_catalog table.")

    except Exception as e:
        print("Error in insert_application_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get BIOS information
def get_bios_info():
    try:    
        bios_info = {}
        c = wmi.WMI()
        bios = c.Win32_BIOS()[0]

        # Remove timezone offset and convert BIOS date to datetime object
        bios_date_str = bios.ReleaseDate.split('+')[0]
        bios_release_date = datetime.datetime.strptime(bios_date_str, "%Y%m%d%H%M%S.%f")

        # Convert BIOS release date to human-readable format
        bios_date = bios_release_date.strftime("%B %d, %Y")

        bios_info["Date"] = bios_date
        bios_info["Version"] = f"{bios.Version}"
        bios_info["Manufacturer"] = bios.Manufacturer
        bios_info["Serial Number"] = bios.SerialNumber

        # Calculate computer age based on BIOS release date
        today = datetime.datetime.strptime(get_custom_date(), "%d-%m-%Y %H:%M:%S.%f")
        computer_age = (today - bios_release_date).days // 365  # Calculate age in years
        bios_info["Computer Age"] = f"{computer_age} years"

        # Remove "Unavailable" entries from bios_info
        bios_info = {key: value for key, value in bios_info.items() if value != "Unavailable"}
        
        return bios_info
    
    except Exception as e:
        print("Error in get_bios_info:", e)
        # Use placeholders matching the format of actual values
        placeholder_values = {
            "Date": "January 01, 2000",
            "Version": "Unknown - 0000000",  # Format matches the actual value
            "Manufacturer": "Unknown",
            "Serial Number": "Unknown - 000000000",
            "Computer Age": "0 years"  # Format matches the actual value
        }
        return placeholder_values
    
# Function to check existing record
def check_existing_record(db_connection, mac_address):
    try:
        cursor = db_connection.cursor()

        check_query = "SELECT * FROM sys_profile WHERE pc_mac_address = %s"
        cursor.execute(check_query, (mac_address,))
        existing_record = cursor.fetchone()

        return existing_record

    except Exception as e:
        print("Error in check_existing_record:", e)
        return None
    finally:
        cursor.close()

# Generate a unique computer ID based on MAC address
def generate_computer_id(mac_address):
    db_host, db_user, db_password, db_name = connect_to_database()

    try:
        db_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = db_connection.cursor()

        # Check if MAC address already has a computer ID in sys_profile table
        select_query = "SELECT Computer_ID FROM sys_profile WHERE pc_mac_address = %s"
        cursor.execute(select_query, (mac_address,))
        result = cursor.fetchone()

        if result:
            return result[0]  # Return the existing computer ID

        # Generate a new computer ID
        base_id = "COMP_"
        available_id = 1

        while True:
            comp_id = f"{base_id}{available_id:04d}"
            # Check if the generated ID is already in use
            select_query = "SELECT COUNT(*) FROM sys_profile WHERE Computer_ID = %s"
            cursor.execute(select_query, (comp_id,))
            count = cursor.fetchone()[0]

            if count == 0:
                return comp_id

            available_id += 1

    except Exception as e:
        print("Error in generate_computer_id:", e)
    finally:
        if db_connection:
            db_connection.close()

    return None  # Return None if an error occurred

# Function to connect to database
def connect_to_database():
    db_host = "localhost"
    db_user = "db_pci"
    db_password = "db_pci_bd"
    db_name = "db_pci"

    return db_host, db_user, db_password, db_name

# Function to calculate department count
def fetch_department_counts(current_pc_department, current_comp_id):
    db_host, db_user, db_password, db_name = connect_to_database()

    department_count = 0  # Initialize the department count to 0

    try:
        db_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = db_connection.cursor()

        # Check if the current comp id is already present in the table
        comp_id_query = "SELECT department FROM sys_profile WHERE computer_id = %s"
        cursor.execute(comp_id_query, (current_comp_id,))
        existing_department = cursor.fetchone()

        # Fetch department-wise PC counts from sys_profile table
        select_query = "SELECT department, COUNT(*) as department_count FROM sys_profile GROUP BY department"
        cursor.execute(select_query)
        results = cursor.fetchall()

        # Process the results and update the department count
        for department, count in results:
            if department == current_pc_department:
                department_count = count
                break

        if not existing_department:
            # If the comp id is not present, increment the count for the department
            update_query = "UPDATE sys_profile SET department = %s WHERE computer_id = %s"
            cursor.execute(update_query, (current_pc_department, current_comp_id))
            db_connection.commit()
            department_count += 1

    except Exception as e:
        print("Error in fetch_department_counts:", e)
    finally:
        if db_connection:
            db_connection.close()

    return department_count

# Function to get disk information
def get_disk_info():
    try:
        disk_info =  {}
        partitions = psutil.disk_partitions()
        total_disk_size = 0
        total_free_space = 0
        total_partitions = 0

        def get_mapped_network_drives():
            try:
                drives = [{"local": "Unavailable", "remote": "Unavailable"}]
                resume = 0

                while True:
                    drive_info, total, resume = win32net.NetUseEnum(None, 0, resume, 65536)
                    for drive in drive_info:
                        if drive['remote']:
                            drives.append({
                                "local": drive['local'],
                                "remote": drive['remote']
                            })

                    if not resume:
                        return [{"local": "Unavailable", "remote": "Unavailable"}]

                # Remove "Unavailable" entries from the drives list
                drives = [drive for drive in drives if all(value != "Unavailable" for value in drive.values())]
                
                return drives

            except Exception as e:
                print("Error in get_mapped_network_drives:", e)
                return [{"local": "Unavailable", "remote": "Unavailable"}]


        mapped_network_drives = get_mapped_network_drives()
        disk_info["Mapped Network Drives"] = mapped_network_drives

        partition_info = {}

        for partition in partitions:
            if 'cdrom' not in partition.opts and 'removable' not in partition.opts:
                disk_usage = psutil.disk_usage(partition.mountpoint)

                partition_info[partition.device] = {
                    "Free Space": f"{disk_usage.free / (1024 ** 3):.2f} GB",
                    "Total Space": f"{disk_usage.total / (1024 ** 3):.2f} GB",
                }

                total_disk_size += disk_usage.total
                total_free_space += disk_usage.free
                total_partitions += 1

        disk_info["Partitions"] = partition_info  # Group partitions under "Partitions"

        def get_cdrom_info():
            try:
                cdrom_info = []

                c = wmi.WMI()

                for drive in c.Win32_CDROMDrive():
                    cdrom_info.append({
                        "Drive Letter": drive.Drive,
                        "Name": drive.Name,
                        "Manufacturer": drive.Manufacturer,
                        "Media Loaded": drive.MediaLoaded,
                        "Media Type": drive.MediaType,
                        "Volume Name": drive.VolumeName,
                    })

                # Check if there are any available CD-ROM drives
                if not cdrom_info:
                    cdrom_info.append({
                        "Drive Letter": "Unavailable",
                        "Name": "Unavailable",
                        "Manufacturer": "Unavailable",
                        "Media Loaded": "Unavailable",
                        "Media Type": "Unavailable",
                        "Volume Name": "Unavailable",
                    })
                
                total_cd_rom = str(len(cdrom_info) - 1)
                                
                return total_cd_rom, cdrom_info

            except Exception as e:
                print("Error in get_cdrom_info:", e)
                return [{
                    "Drive Letter": "Unavailable",
                    "Name": "Unavailable",
                    "Manufacturer": "Unavailable",
                    "Media Loaded": "Unavailable",
                    "Media Type": "Unavailable",
                    "Volume Name": "Unavailable",
                }]

        # Calculate the total free space percentage
        total_free_space_percentage = (total_free_space / total_disk_size) * 100
        
        disk_info["CD-ROM Count"] ,disk_info["CD-ROM Drives"] = get_cdrom_info()
        disk_info["Total Disk Size"] = f"{total_disk_size / (1024 ** 3):.2f} GB"
        disk_info["Total Free Space"] = f"{total_free_space / (1024 ** 3):.2f} GB"
        disk_info["Total Free Space Percentage"] = f"{total_free_space_percentage:.2f}%"
        disk_info["Total Partitions"] = total_partitions

        return disk_info

    except Exception as e:
        print("Error in get_disk_info:", e)
        return  {
            "Mapped Network Drives": "Unavailable",
            "Partitions": "Unavailable",
            "CD-ROM Count": "Unavailable",
            "CD-ROM Drives": "Unavailable",
            "Total Disk Size": "Unavailable",
            "Total Free Space": "Unavailable",
            "Total Partitions": "Unavailable",
        }

# Function to retrive previous history count
def get_previous_history_count():
    try:
        # Establish a database connection
        db_host, db_user, db_password, db_name = connect_to_database()
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )

        # Create a cursor object to interact with the database
        cursor = connection.cursor()

        # Define the MAC address
        mac_address = get_mac_address()

        # Define the SQL query to count the MAC addresses
        query = "SELECT COUNT(*) FROM sys_profile_archive WHERE pc_mac_address = %s"

        # Execute the query with the MAC address as a parameter
        cursor.execute(query, (mac_address,))

        # Fetch the result
        count = cursor.fetchone()[0]

        return count

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return None

    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()

# Function to insert partition into db
def insert_partition_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        partitions = gathered_info["partitions"]
        date = get_custom_date()

        for partition_device, partition_info in partitions.items():            
            partition_name = partition_device
            free_space = partition_info["Free Space"]
            total_space = partition_info["Total Space"]

            insert_query = (
                "INSERT INTO partition_registry (comp_id, partition_name, free_space, total_space, date) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, partition_name, free_space, total_space, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Partition information inserted into partition_registry table.")

    except Exception as e:
        print("Error in insert_partition_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to insert cd info into db
def insert_cd_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        cd_rom_drives = gathered_info["cd_rom_drives"]
        date = get_custom_date()

        for cd_drive in cd_rom_drives:
            cd_rom_drive = cd_drive["Drive Letter"]
            cd_rom_name = cd_drive["Name"]
            cd_rom_manufacturer = cd_drive["Manufacturer"]
            media_loaded = cd_drive["Media Loaded"]
            media_type = cd_drive["Media Type"]
            volume_name = cd_drive["Volume Name"]

            insert_query = (
                "INSERT INTO cd_rom_registry (comp_id, cd_rom_drive, cd_rom_name, cd_rom_manufacturer, media_loaded, media_type, volume_name, date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, cd_rom_drive, cd_rom_name, cd_rom_manufacturer, media_loaded, media_type, volume_name, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("CD-ROM drive information inserted into cd_rom_drives table.")

    except Exception as e:
        print("Error in insert_cd_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to insert mapped info into db
def insert_mapped_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        mapped_network_drives = gathered_info["mapped_drives"]
        date = get_custom_date()

        for mapped_drive in mapped_network_drives:
            mapped_local = mapped_drive["local"]
            mapped_remote = mapped_drive["remote"]

            insert_query = (
                "INSERT INTO mapped_drive_registry (comp_id, mapped_local, mapped_remote, date) "
                "VALUES (%s, %s, %s, %s)"
            )
            values = (
                comp_id, mapped_local, mapped_remote, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Mapped drive information inserted into mapped_drives table.")

    except Exception as e:
        print("Error in insert_mapped_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to gather system info
def gather_system_info():
    try:
        print("Debug: Gathering system information...")
        hostname = socket.gethostname()
        print("Debug: Hostname =", hostname)
        network_info = get_network_adapter_details()
        print("Debug: Network info =", network_info)
        mac_address = get_mac_address()
        print("Debug: MAC address =", mac_address)
        computer_id = generate_computer_id(mac_address)
        print("Debug: Computer ID =", computer_id)
        username = os.getlogin()
        print("Debug: Username =", username)
        system_info = get_system_info()
        print("Debug: System info =", system_info)
        local_user_accounts = get_local_user_accounts()
        print("Debug: Local user accounts=", local_user_accounts)
        startup_programs_info = get_and_print_startup_programs()
        print("Debug: Startup programs info =", startup_programs_info)
        shared_folders_info = get_and_print_shared_folders()
        print("Debug: Shared folders info =", shared_folders_info)
        ie_version = get_ie_version()
        print("Debug: Internet Explorer version =", ie_version)
        bios_info = get_bios_info()
        print("Debug: BIOS info =", bios_info)
        previous_count = get_previous_history_count()
        print("Debug: Previous history count =", previous_count)
        multimedia_info = get_multimedia_info()
        print("Debug: Multimedia info =", multimedia_info)
        printer_info_list = get_printer_details()
        print("Debug: Printer info =", printer_info_list)
        uptime_info = get_system_uptime()
        print("Debug: Uptime info =", uptime_info)
        system_hotfixes_info = get_and_print_system_hotfixes()
        print("Debug: System hotfixes info =", system_hotfixes_info)
        windows_update_status = get_windows_update_status()
        print("Debug: Windows update status =", windows_update_status)
        current_pc_department = network_info["Department"]
        print("Debug: Current PC department =", current_pc_department)
        current_comp_id = computer_id
        print("Debug: Current computer ID =", current_comp_id)
        department_count = fetch_department_counts(current_pc_department, current_comp_id)
        print("Debug: Department count =", department_count)
        motherboard_details = get_motherboard_info()
        print("Debug: Motherboard details =", motherboard_details)
        disk_info = get_disk_info()
        print("Debug: Disk info =", disk_info)
        memory_slot_details = get_memory_slot_details()
        print("Debug: Memory slot details =", memory_slot_details)
        memory_info = get_memory_info()
        print("Debug: Memory info =", memory_info)
        installed_apps, total_installed_apps = get_installed_apps_with_versions()
        print("Debug: Installed apps =", installed_apps)
        print("Debug: Total installed apps =", total_installed_apps)
        antivirus_status = get_antivirus_status()
        print("Debug: Antivirus Status =", antivirus_status)        
        monitor_info = get_monitor_info()
        print("Debug: Monitor info =", monitor_info)
        date = get_custom_date()
        print("Debug: Custom date =", date)

        gathered_info = {
            "computer_id": computer_id,
            "hostname": hostname,
            "username": username,
            "department": network_info["Department"],
            "department_count": department_count,
            "node_type": network_info["Node Type"],
            "ip_routing_status": network_info["IP Routing Status"],
            "wins_proxy_status": network_info["WINS Proxy Status"],
            "lan_interface": network_info["Interface"],
            "lan_description": network_info["Description"],
            "lan_speed": network_info["Network Speed"],
            "lan_mac_address": network_info["Physical Address"],
            "ipv4_address": network_info["IPv4 Address"],
            "ip_address": str(network_info["IPv4 Address"]),
            "ipv6_address": network_info["Link-local IPv6 Address"],
            "subnet_mask": network_info["Subnet Mask"],
            "default_gateway": network_info["Default Gateway"],
            "netbios_status": network_info["NetBIOS over Tcpip Status"],
            "autoconfiguration_status": network_info["Autoconfiguration Status"],
            "lease_obtained": network_info["Lease Obtained"],
            "lease_expiry": network_info["Lease Expires"],
            "dhcp_status": network_info["DHCP Status"],
            "dhcp_server": network_info["DHCP Server"],
            "dns_server": network_info["DNS Servers"],
            "internet_explorer_version": ie_version,
            "monitor_name": monitor_info[0]["Monitor Name"],
            "monitor_manufacturer": monitor_info[0]["Manufacturer"],
            "monitor_product_code": monitor_info[0]["Product Code"],
            "monitor_serial_number": monitor_info[0]["Serial Number"],
            "bios_version": bios_info["Version"],
            "bios_manufacturer": bios_info["Manufacturer"],
            "bios_date": bios_info["Date"],
            "bios_serial_number": bios_info["Serial Number"],
            "system_type": system_info["System Type"],
            "cpu_model": system_info["Model"],
            "pc_mac_address": mac_address,
            "os_name": system_info["OS Name"],
            "os_version": system_info["OS Version"],
            "os_manufacturer": system_info["OS Manufacturer"],
            "os_configuration": system_info["OS Configuration"],
            "os_build_type": system_info["OS Build Type"],
            "os_install_date": system_info["Original Install Date"],
            "product_id": system_info["Product ID"],
            "windows_product_key": system_info["Windows Product Key"],
            "processor": system_info["Processor"],
            "mapped_drives": disk_info["Mapped Network Drives"], 
            "partitions": disk_info["Partitions"],
            "cd_rom_drives": disk_info["CD-ROM Drives"],  
            "cd_rom_count": str(disk_info["CD-ROM Count"]),
            "total_disk_space": disk_info["Total Disk Size"],
            "total_free_space": disk_info["Total Free Space"],
            "total_free_space_percentage": disk_info["Total Free Space Percentage"],
            "total_partitions": disk_info["Total Partitions"],
            "motherboard_manufacturer": motherboard_details["Manufacturer"],
            "motherboard_product": motherboard_details["Product"],
            "motherboard_version": motherboard_details["Version"],
            "chassis": motherboard_details["Chassis"],
            "memory_slot_details": memory_slot_details,
            "memory_slot_count": str(len(memory_slot_details)),
            "total_memory": memory_info["Total Memory"],
            "available_memory": memory_info["Available Memory"],
            "used_memory": memory_info["Used Memory"],
            "memory_usage_percentage": memory_info["Memory Usage Percentage"],
            "multimedia_info": multimedia_info,
            "multimedia_count": str(len(multimedia_info)),
            "uptime": uptime_info,
            "update_required": windows_update_status["Update required"],
            "last_checked": windows_update_status["Last Checked"],
            "shared_folder": shared_folders_info,
            "shared_folder_count": str(len(shared_folders_info)),
            "startup": startup_programs_info,
            "startup_count": str(len(startup_programs_info)),
            "printer": printer_info_list,
            "printer_count": str(len(printer_info_list)),
            "system_hotfix": system_hotfixes_info,
            "system_hotflix_count": str(len(system_hotfixes_info)),
            "local_user_accounts_count": str(len(local_user_accounts) - 1),
            "user_accounts": local_user_accounts,
            "installed_apps": installed_apps,
            "total_installed_applications": total_installed_apps,
            "antivirus_status": antivirus_status["Status"],
            "antivirus_name": antivirus_status["Name"],
            "antivirus_version": antivirus_status["Version"],
            "antivirus_publisher": antivirus_status["Publisher"],
            "antivirus_install_date": antivirus_status["InstallDate"],
            "computer_age": bios_info["Computer Age"],
            "previous_count": previous_count,
            "date": date
        }

        return gathered_info

    except Exception as e:
        print("Error in gather_system_info:", e)
        return {
            "computer_id": "Unavailable",
            "hostname": "Unavailable",
            "username": "Unavailable",
            "department": "Unavailable",
            "department_count": "Unavailable",
            "node_type": "Unavailable",
            "ip_routing_status": "Unavailable",
            "wins_proxy_status": "Unavailable",
            "lan_interface": "Unavailable",
            "lan_description": "Unavailable",
            "lan_speed": "Unavailable",
            "lan_mac_address": "Unavailable",
            "ipv4_address": "Unavailable",
            "ip_address": "Unavailable",
            "ipv6_address": "Unavailable",
            "subnet_mask": "Unavailable",
            "default_gateway": "Unavailable",
            "netbios_status": "Unavailable",
            "autoconfiguration_status": "Unavailable",
            "lease_obtained": "Unavailable",
            "lease_expiry": "Unavailable",
            "dhcp_status": "Unavailable",
            "dhcp_server": "Unavailable",
            "dns_server": "Unavailable",
            "internet_explorer_version": "Unavailable",
            "monitor_name": "Unavailable",
            "monitor_manufacturer": "Unavailable",
            "monitor_product_code": "Unavailable",
            "monitor_serial_number": "Unavailable",
            "bios_version": "Unavailable",
            "bios_manufacturer": "Unavailable",
            "bios_date": "Unavailable",
            "bios_serial_number": "Unavailable",
            "system_type": "Unavailable",
            "cpu_model": "Unavailable",
            "pc_mac_address": "Unavailable",
            "os_name": "Unavailable",
            "os_version": "Unavailable",
            "os_manufacturer": "Unavailable",
            "os_configuration": "Unavailable",
            "os_build_type": "Unavailable",
            "os_install_date": "Unavailable",
            "product_id": "Unavailable",
            "windows_product_key": "Unavailable",
            "processor": "Unavailable",
            "mapped_drives": "Unavailable", 
            "partitions": "Unavailable",
            "cd_rom_drives": "Unavailable",  
            "cd_rom_count": "Unavailable",
            "total_disk_space": "Unavailable",
            "total_free_space": "Unavailable",
            "total_partitions": "Unavailable",
            "motherboard_manufacturer": "Unavailable",
            "motherboard_product": "Unavailable",
            "motherboard_version": "Unavailable",
            "chassis": "Unavailable",
            "memory_slot_details": "Unavailable",
            "memory_slot_count": "Unavailable",
            "total_memory": "Unavailable",
            "available_memory": "Unavailable",
            "used_memory": "Unavailable",
            "memory_usage_percentage": "Unavailable",
            "multimedia_info": "Unavailable",
            "multimedia_count": "Unavailable",
            "uptime": "Unavailable",
            "update_required": "Unavailable",
            "last_checked": "Unavailable",
            "shared_folder": "Unavailable",
            "shared_folder_count": "Unavailable",
            "startup": "Unavailable",
            "startup_count": "Unavailable",
            "printer": "Unavailable",
            "printer_count": "Unavailable",
            "system_hotfix": "Unavailable",
            "system_hotflix_count": "Unavailable",
            "local_user_accounts_count": "Unavailable",
            "user_accounts": "Unavailable",
            "installed_apps": "Unavailable",
            "total_installed_applications": "Unavailable",
            "antivirus_status": "Unavailable",
            "antivirus_name": "Unavailable",
            "antivirus_version": "Unavailable",
            "antivirus_publisher": "Unavailable",
            "antivirus_install_date": "Unavailable",
            "computer_age": "Unavailable",
            "previous_count": "Unavailable",
            "date": "Unavailable"
        }
    
# Function to get Internet Explorer version
def get_ie_version():
    try:
        reg_path = r"SOFTWARE\Microsoft\Internet Explorer"
        key = win32com.client.Dispatch("WScript.Shell").RegRead(f"HKLM\\{reg_path}\\svcVersion")
        return f"{key}"
    except Exception as e:
        print("Error retrieving Internet Explorer version:", e)
        return "Internet Explorer Not Available"

# Function to insert new data into db
def insert_new_data(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()
        date = get_custom_date()

        insert_query = (
            "INSERT INTO sys_profile ("
            "computer_id, hostname, username, department, department_count, node_type, ip_routing_status, wins_proxy_status,"
            "lan_interface, lan_description, lan_speed, lan_mac_address, ipv4_address, ipv6_address, subnet_mask, default_gateway,"
            "netbios_status, autoconfiguration_status, lease_obtained, lease_expiry, dhcp_status, dhcp_server, dns_server,"
            "internet_explorer_version, monitor_name, monitor_manufacturer, monitor_product_code, monitor_serial_number, bios_version,"
            "bios_manufacturer, bios_date, bios_serial_number, system_type, cpu_model, chassis, pc_mac_address, os_name, os_version,"
            "os_manufacturer, os_configuration, os_build_type, os_install_date, product_id, windows_product_key, processor,"
            "total_disk_space, total_free_space, total_partitions, motherboard_manufacturer, motherboard_product, motherboard_version,"
            "total_memory, available_memory, used_memory, memory_usage_percentage, uptime, update_required, last_checked, total_installed_applications,"
            "computer_age, date"
            ") VALUES ("
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," 
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s," 
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s" 
            ")"
        )

        insert_values = (
            gathered_info["computer_id"], gathered_info["hostname"], gathered_info["username"],
            gathered_info["department"], gathered_info["department_count"], gathered_info["node_type"],
            gathered_info["ip_routing_status"], gathered_info["wins_proxy_status"], gathered_info["lan_interface"],
            gathered_info["lan_description"], gathered_info["lan_speed"], gathered_info["lan_mac_address"],
            gathered_info["ipv4_address"], gathered_info["ipv6_address"], gathered_info["subnet_mask"],
            gathered_info["default_gateway"], gathered_info["netbios_status"], gathered_info["autoconfiguration_status"],
            gathered_info["lease_obtained"], gathered_info["lease_expiry"], gathered_info["dhcp_status"],
            gathered_info["dhcp_server"], gathered_info["dns_server"], gathered_info["internet_explorer_version"],
            gathered_info["monitor_name"], gathered_info["monitor_manufacturer"], gathered_info["monitor_product_code"],
            gathered_info["monitor_serial_number"], gathered_info["bios_version"], gathered_info["bios_manufacturer"],
            gathered_info["bios_date"], gathered_info["bios_serial_number"], gathered_info["system_type"],
            gathered_info["cpu_model"], gathered_info["chassis"], gathered_info["pc_mac_address"],
            gathered_info["os_name"], gathered_info["os_version"], gathered_info["os_manufacturer"],
            gathered_info["os_configuration"], gathered_info["os_build_type"], gathered_info["os_install_date"],
            gathered_info["product_id"], gathered_info["windows_product_key"], gathered_info["processor"],
            gathered_info["total_disk_space"], gathered_info["total_free_space"], gathered_info["total_partitions"],
            gathered_info["motherboard_manufacturer"], gathered_info["motherboard_product"],
            gathered_info["motherboard_version"], gathered_info["total_memory"], gathered_info["available_memory"],
            gathered_info["used_memory"], gathered_info["memory_usage_percentage"], gathered_info["uptime"],
            gathered_info["update_required"], gathered_info["last_checked"], gathered_info["total_installed_applications"], gathered_info["computer_age"],
            date
        )

        cursor.execute(insert_query, insert_values)

        db_connection.commit()

        #print("New data inserted into the sys_profile table.")

    except Exception as e:
        print("Error in insert_new_data:", e)
    finally:
        cursor.close()

# Function to get Local user account details
def get_local_user_accounts():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        user_accounts = wmi.ExecQuery("SELECT * FROM Win32_UserAccount WHERE LocalAccount=True")

        account_info_list = [{"Name": "Unavailable", "Domain": "Unavailable", "Description": "Unavailable"}]

        for account in user_accounts:
            account_info = {
                "Name": account.Name,
                "Domain": account.Domain,
                "Description": account.Description,
                "SID": account.SID,
                "Status": "Disabled" if account.Disabled else "Enabled"
            }
            account_info_list.append(account_info)

        # Remove "Unavailable" entries from account_info_list
        account_info_list = [info for info in account_info_list if all(value != "Unavailable" for value in info.values())]
        
        return account_info_list

    except Exception as e:
        print("Error in get_local_user_accounts:", e)
        return [{"Name": "Unavailable", "Domain": "Unavailable", "Description": "Unavailable"}] 
    
# Function to insert local user accounts to db
def insert_local_user_accounts_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        local_user_accounts = gathered_info["user_accounts"]
        date = get_custom_date()

        for account in local_user_accounts:
            name = account["Name"]
            domain = account["Domain"]
            description = account["Description"]
            sid = account["SID"]
            status = account["Status"]

            insert_query = (
                "INSERT INTO user_credentials (comp_id, name, domain, description, sid, status, date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            values = (comp_id, name, domain, description, sid, status, date)

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Local user account details inserted into user_credentials table.")

    except Exception as e:
        print("Error in insert_local_user_accounts_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get a fixed date
def get_custom_date():
    if not hasattr(get_custom_date, "cached_time"):
        try:
            # Synchronize time from NTP server
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request('time.google.com')  # Use a reliable NTP server
            synchronized_time = datetime.datetime.fromtimestamp(response.tx_time, pytz.utc)

            # Convert to desired time zone and format the date
            asia_timezone = pytz.timezone("Asia/Kolkata")  # Replace with the desired Asia time zone
            custom_time = synchronized_time.astimezone(asia_timezone)
            formatted_time = custom_time.strftime("%d-%m-%Y %H:%M:%S.%f")

            # Cache the formatted time value
            get_custom_date.cached_time = formatted_time
            
        except Exception as e:
            return "00-00-0000 00:00:00.000000"
    
    return get_custom_date.cached_time

# Function to get mac address
def get_mac_address():
    try:
        for addrs in psutil.net_if_addrs().values():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    return addr.address
        return "Not Found"
    except Exception as e:
        print("Error in get_mac_address:", e)
        return "Unavailable"  # Return an error message if an exception occurs

# Function to get memory info
def get_memory_info():
    try:
        memory = psutil.virtual_memory()
        memory_info = {
            "Total Memory": f"{memory.total / (1024 ** 3):.2f} GB",
            "Available Memory": f"{memory.available / (1024 ** 3):.2f} GB",
            "Used Memory": f"{memory.used / (1024 ** 3):.2f} GB",
            "Memory Usage Percentage": f"{memory.percent:.2f}%",
        }
        return memory_info
    except Exception as e:
        print("Error in get_memory_info:", e)
        return {
            "Total Memory": "Unavailable",
            "Available Memory": "Unavailable",
            "Used Memory": "Unavailable",
            "Memory Usage Percentage": "Unavailable"
        }

# Function to get memory slot info
def get_memory_slot_details():
    try:
        c = wmi.WMI()
        memory_slots = [{
                "Capacity": "Unavailable",
                "DeviceLocator": "Unavailable",
                "FormFactor": "Unavailable",
                "MemoryType": "Unavailable",
                "Manufacturer": "Unavailable",
                "Speed": "Unavailable",
                "MaxCapacity": "Unavailable",
            }]

        # Mapping of form factor codes to names
        form_factor_mapping = {
            1: "Other",
            2: "SIP",
            3: "DIP",
            4: "ZIP",
            5: "SOJ",
            6: "Proprietary",
            7: "SIMM",
            8: "DIMM",
            9: "TSOP",
            10: "PGA",
            11: "RIMM",
            12: "SODIMM",
            13: "SRIMM",
            14: "SMD",
            15: "SSMP",
            16: "QFP",
            17: "TQFP",
            18: "SOIC",
            19: "LCC",
            20: "PLCC",
            21: "BGA",
            22: "FPBGA",
            23: "LGA",
        }

        # Mapping of memory type codes to names
        memory_type_mapping = {
            0: "Unknown",
            1: "Other",
            2: "DRAM",
            3: "Synchronous DRAM",
            4: "Cache DRAM",
            5: "EDO",
            6: "EDRAM",
            7: "VRAM",
            8: "SRAM",
            9: "RAM",
            10: "ROM",
            11: "Flash",
            12: "EEPROM",
            13: "FEPROM",
            14: "EPROM",
            15: "CDRAM",
            16: "3DRAM",
            17: "SDRAM",
            18: "SGRAM",
            19: "RDRAM",
            20: "DDR",
            21: "DDR2",
            22: "DDR2 FB-DIMM",
            24: "DDR3",
            25: "FBD2",
            26: "DDR4",
            27: "LPDDR",
            28: "LPDDR2",
            29: "LPDDR3",
            30: "LPDDR4",
            31: "Logical non-volatile device",
        }

        for memory in c.Win32_PhysicalMemory():
            slot = {
                "Capacity": int(memory.Capacity) // (1024 ** 3),
                "DeviceLocator": memory.DeviceLocator.strip(),
                "FormFactor": form_factor_mapping.get(memory.FormFactor, "Unknown"),
                "MemoryType": memory_type_mapping.get(memory.MemoryType, "Unknown"),
                "Manufacturer": memory.Manufacturer,
                "Speed": memory.Speed,
                "MaxCapacity": int(memory.Capacity) // (1024 ** 3),
            }
            memory_slots.append(slot)

        # Remove "Unavailable" records from the list
        memory_slots = [slot for slot in memory_slots if slot["Capacity"] != "Unavailable"]

        return memory_slots  # Return the list of dictionaries

    except Exception as e:
        print("Error in get_memory_slot_details:", e)
        return [{
                "Capacity": "Unavailable",
                "DeviceLocator": "Unavailable",
                "FormFactor": "Unavailable",
                "MemoryType": "Unavailable",
                "Manufacturer": "Unavailable",
                "Speed": "Unavailable",
                "MaxCapacity": "Unavailable",
            }]
        
# Function to insert memory slot details to db 
def insert_memory_slot_details_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        memory_slots_data = gathered_info["memory_slot_details"]
        date = get_custom_date()

        for memory_slot_data in memory_slots_data:
            memory_slot = {
                "Index": memory_slot_data.get("Index", "N/A"),
                "DeviceLocator": memory_slot_data.get("DeviceLocator", "N/A"),
                "FormFactor": memory_slot_data.get("FormFactor", "N/A"),
                "MemoryType": memory_slot_data.get("MemoryType", "N/A"),
                "Manufacturer": memory_slot_data.get("Manufacturer", "N/A"),
                "Speed": memory_slot_data.get("Speed", "N/A"),
                "Capacity": memory_slot_data.get("Capacity", "N/A"),  # Add capacity
                "MaxCapacity": memory_slot_data.get("MaxCapacity", "N/A"),  # Add max_capacity
            }

            memory_slot_name = f"Memory Slot {memory_slot['Index']}"
            device_locator = memory_slot["DeviceLocator"]
            form_factor = memory_slot["FormFactor"]
            memory_type = memory_slot["MemoryType"]
            manufacturer = memory_slot["Manufacturer"]
            speed = memory_slot["Speed"]
            capacity = memory_slot["Capacity"]  # Retrieve capacity
            max_capacity = memory_slot["MaxCapacity"]  # Retrieve max_capacity

            insert_query = (
                "INSERT INTO memory_slot_inventory (comp_id, memory_slot, device_locator, form_factor, memory_type, manufacturer, speed, capacity, max_capacity, date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, memory_slot_name, device_locator, form_factor, memory_type, manufacturer, speed, capacity, max_capacity, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Memory slot details inserted into memory_slot_inventory table.")

    except Exception as e:
        print("Error in insert_memory_slot_details_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get monitor information
def get_monitor_info():
    try:
        monitor_info = []
        c = wmi.WMI(namespace="root\\wmi")
        monitors = c.WmiMonitorID()

        # Define the manufacturer code to manufacturer mapping within the function
        manufacturer_mapping = {
            "ACI": "Asus (ASUSTeK Computer Inc.)",
            "ACR": "Acer America Corp.",
            "ACT": "Targa",
            "ADI": "ADI Corporation",
            "AMW": "AMW",
            "AOC": "AOC International (USA) Ltd.",
            "API": "Acer America Corp.",
            "APP": "Apple Computer, Inc.",
            "ART": "ArtMedia",
            "AST": "AST Research",
            "AUO": "AU Optronics",
            "BMM": "BMM",
            "BNQ": "BenQ Corporation",
            "BOE": "BOE Display Technology",
            "CPL": "Compal Electronics, Inc. / ALFA",
            "CPQ": "COMPAQ Computer Corp.",
            "CTX": "CTX / Chuntex Electronic Co.",
            "DEC": "Digital Equipment Corporation",
            "DEL": "Dell Computer Corp.",
            "DPC": "Delta Electronics, Inc.",
            "DWE": "Daewoo Telecom Ltd",
            "ECS": "ELITEGROUP Computer Systems",
            "EIZ": "EIZO",
            "EPI": "Envision Peripherals, Inc.",
            "FCM": "Funai Electric Company of Taiwan",
            "FUS": "Fujitsu Siemens",
            "GSM": "LG Electronics Inc. (GoldStar Technology, Inc.)",
            "GWY": "Gateway 2000",
            "HEI": "Hyundai Electronics Industries Co., Ltd.",
            "HIQ": "Hyundai ImageQuest",
            "HIT": "Hitachi",
            "HSD": "Hannspree Inc",
            "HSL": "Hansol Electronics",
            "HTC": "Hitachi Ltd. / Nissei Sangyo America Ltd.",
            "HWP": "Hewlett Packard (HP)",
            "HPN": "Hewlett Packard (HP)",
            "IBM": "IBM PC Company",
            "ICL": "Fujitsu ICL",
            "IFS": "InFocus",
            "IQT": "Hyundai",
            "IVM": "Idek Iiyama North America, Inc.",
            "KDS": "KDS USA",
            "KFC": "KFC Computek",
            "LEN": "Lenovo",
            "LGD": "LG Display",
            "LKM": "ADLAS / AZALEA",
            "LNK": "LINK Technologies, Inc.",
            "LPL": "LG Philips",
            "LTN": "Lite-On",
            "MAG": "MAG InnoVision",
            "MAX": "Maxdata Computer GmbH",
            "MEI": "Panasonic Comm. & Systems Co.",
            "MEL": "Mitsubishi Electronics",
            "MIR": "Miro Computer Products AG",
            "MTC": "MITAC",
            "NAN": "NANAO",
            "NEC": "NEC Technologies, Inc.",
            "NOK": "Nokia",
            "NVD": "Nvidia",
            "OQI": "OPTIQUEST",
            "PBN": "Packard Bell",
            "PCK": "Daewoo",
            "PDC": "Polaroid",
            "PGS": "Princeton Graphic Systems",
            "PHL": "Philips Consumer Electronics Co.",
            "PRT": "Princeton",
            "REL": "Relisys",
            "SAM": "Samsung",
            "SEC": "Seiko Epson Corporation",
            "SMC": "Samtron",
            "SMI": "Smile",
            "SNI": "Siemens Nixdorf",
            "SNY": "Sony Corporation",
            "SPT": "Sceptre",
            "SRC": "Shamrock Technology",
            "STN": "Samtron",
            "STP": "Sceptre",
            "TAT": "Tatung Co. of America, Inc.",
            "TRL": "Royal Information Company",
            "TSB": "Toshiba, Inc.",
            "UNM": "Unisys Corporation",
            "VSC": "ViewSonic Corporation",
            "WTC": "Wen Technology",
            "ZCM": "Zenith Data Systems",
            "SHP": "Sharp Corporation",
            "SHR": "Shenzhen Sang Fei Consumer Communications Co., Ltd.",
            "SNM": "Siemens Nixdorf AG",
            "SND": "Sendo",
            "SNU": "Sony Ericsson Mobile Communications AB",
            "SSM": "Smart Storage Systems",
            "SUM": "Summit Microelectronics",
            "SUN": "Sun Microsystems, Inc.",
            "SUP": "Superior Electric",
            "SVA": "SVA-Group",
            "SVP": "Sampo Corporation",
            "SVM": "SGI",
            "TAI": "Tatung Co. of America, Inc.",
            "TCB": "Thomson Consumer Electronics / RCA",
            "TCM": "TECMAR",
            "TCO": "TCO Development",
            "TDC": "Tatung Co. of America, Inc.",
            "TDV": "TADIRAN DISPLAYS LTD",
            "TFT": "TPO Display Corporation",
            "TTI": "Taiwan Telecommunication Industry Co. Ltd.",
            "TXD": "Timecode Systems",
            "UNI": "Unisys Corporation",
            "USI": "USI Co., Ltd.",
            "VAD": "Vadem",
            "VDN": "Viden Systems",
            "VIT": "Viewtronix International Co., Ltd.",
            "VST": "ViewSonic Corporation",
            "VTB": "Video Technology Company Ltd.",
            "WDC": "Western Digital Corporation",
            "WDI": "Westinghouse Digital Electronics",
            "XRX": "Xerox Corporation",
            "YAM": "YAMAHA CORPORATION",
        }

        for monitor in monitors:
            manufacturer_code = ''.join([chr(c) for c in monitor.ManufacturerName if c != 0])
            product_code = ''.join([chr(c) for c in monitor.ProductCodeID if c != 0])
            serial_number = ''.join([chr(c) for c in monitor.SerialNumberID if c != 0])
            monitor_name = ''.join([chr(c) for c in monitor.UserFriendlyName if c != 0])

            # Get the corresponding manufacturer name from the mapping
            manufacturer_name = manufacturer_mapping.get(manufacturer_code, manufacturer_code)

            monitor_dict = {
                "Monitor Name": monitor_name,
                "Manufacturer": manufacturer_name,
                "Product Code": product_code,
                "Serial Number": serial_number
            }

            monitor_info.append(monitor_dict)
            
        if not monitor_info:
            default_monitor = {
                "Monitor Name": "Unavailable",
                "Manufacturer": "Unavailable",
                "Product Code": "Unavailable",
                "Serial Number": "Unavailable"
            }
            monitor_info.append(default_monitor)
        
        return monitor_info

    except Exception as e:
        print("Error in get_monitor_info:", e)
        return [{
                "Monitor Name": "Unavailable",
                "Manufacturer": "Unavailable",
                "Product Code": "Unavailable",
                "Serial Number": "Unavailable"
            }]

# Function to get Motherboard details
def get_motherboard_info():
    try:
        c = win32com.client.GetObject("winmgmts:root\cimv2")
        motherboard_info = {}

        # Mapping of chassis type codes to names
        chassis_type_mapping = {
            1: "Other",
            2: "Unknown",
            3: "Desktop",
            4: "Low Profile Desktop",
            5: "Pizza Box",
            6: "Mini Tower",
            7: "Tower",
            8: "Portable",
            9: "Laptop",
            10: "Notebook",
            11: "Hand Held",
            12: "Docking Station",
            13: "All in One",
            14: "Sub Notebook",
            15: "Space-Saving",
            16: "Lunch Box",
            17: "Main System Chassis",
            18: "Expansion Chassis",
            19: "SubChassis",
            20: "Bus Expansion Chassis",
            21: "Peripheral Chassis",
            22: "Storage Chassis",
            23: "Rack Mount Chassis",
            24: "Sealed-Case PC",
            25: "Multi-System Chassis",
            26: "CompactPCI",
            27: "AdvancedTCA",
            28: "Blade",
            29: "Blade Enclosure",
            30: "Tablet",
            31: "Convertible",
            32: "Detachable",
            33: "IoT Gateway",
            34: "Embedded PC",
            35: "Mini PC",
            36: "Stick PC",
            37: "Cluster",
            38: "Cloud",
            39: "IoT Edge",
            40: "Network Appliance",
            41: "Maximum",
            42: "Virtual Machine",
            43: "UCS Chassis",
            44: "Compact",
            45: "Nano",
            46: "Main Server Chassis",
            47: "Expansion Chassis",
            48: "SubChassis",
            49: "Bus Expansion Chassis",
            50: "Peripheral Chassis",
            51: "Memory Module",
            52: "System Board",
            53: "Processor Module",
            54: "Power Supply",
            55: "Add-in Card",
            56: "Front Panel Board",
            57: "Back Panel Board",
            58: "Power System Board",
            59: "Drive Backplane",
            60: "System Internal",
            61: "Fan",
            62: "Cooling Unit",
            63: "Cable",
            64: "Memory Device",
            65: "System Management Module",
            66: "Motherboard",
            67: "Processor/Memory Module",
            68: "Processor/IO Module",
            69: "Interconnect",
            70: "Memory Expansion Board",
            71: "Peripheral Bay",
            72: "Storage Bay",
            73: "Platform Management Software",
            74: "Processor",
            75: "IoT Sensor",
            76: "IoT Actuator",
            77: "IoT Communication Module",
            78: "IoT Communication Gateway",
            79: "IoT Device",
            80: "IoT Gateway",
            81: "IoT Network Gateway",
            82: "IoT Edge",
            83: "IoT Fog",
            84: "IoT Cloud",
            85: "IoT Fog Gateway",
            86: "IoT Fog Node",
            87: "IoT Fog Server",
            88: "IoT Fog Switch",
            89: "IoT Fog Rack",
            90: "IoT Edge Device",
            91: "IoT Edge Gateway",
            92: "IoT Edge Server",
            93: "IoT Edge Switch",
            94: "IoT Edge Rack",
            95: "IoT Edge Node",
            96: "IoT Edge Appliance",
            97: "Virtual System",
            98: "Virtual Machine",
            99: "Computer System",
            100: "Chassis Management Controller",
            # Add more mappings as needed
        }

        for board in c.ExecQuery("SELECT * FROM Win32_BaseBoard"):
            motherboard_info["Manufacturer"] = board.Manufacturer
            motherboard_info["Product"] = board.Product
            motherboard_info["Version"] = board.Version

        for chassis in c.ExecQuery("SELECT * FROM Win32_SystemEnclosure"):
            chassis_type = chassis.ChassisTypes[0]
            chassis_name = chassis_type_mapping.get(chassis_type, "Unknown")
            motherboard_info["Chassis"] = chassis_name

        return motherboard_info

    except Exception as e:
        print("Error in get_motherboard_info:", e)
        return {}
        
# Function to get multimedia information
def get_multimedia_info():
    try:
        device_info_list = []  # List to hold individual device information
        wmi = win32com.client.GetObject("winmgmts:")
        devices = wmi.ExecQuery("SELECT * FROM Win32_SoundDevice")

        for device in devices:
            device_info = {
                "Name": device.Name,
                "Manufacturer": device.Manufacturer,
                "Product Name": device.ProductName
            }
            device_info_list.append(device_info)

        return device_info_list

    except Exception as e:
        print("Error in get_multimedia_info:", e)
        return []
    
# Function to insert multimedia info to db 
def insert_multimedia_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        multimedia_devices = gathered_info["multimedia_info"]
        date = get_custom_date()

        for device in multimedia_devices:
            name = device["Name"]
            manufacturer = device["Manufacturer"]
            product_name = device["Product Name"]

            insert_query = (
                "INSERT INTO multimedia_repository (comp_id, name, manufacturer, product_name, date) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, name, manufacturer, product_name, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Multimedia information inserted into multimedia_repository table.")

    except Exception as e:
        print("Error in insert_multimedia_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get network adapter details
def get_network_adapter_details():
    # Function to get network speed
    def get_network_speed():
        try:
            network_speed = []

            for nic, addrs in psutil.net_if_stats().items():
                if nic != 'Loopback Pseudo-Interface 1' and addrs.isup and addrs.speed > 0:
                    network_speed.append(f"{addrs.speed} Mbps")

            network_speed_output = ', '.join(network_speed)
            return f"{network_speed_output}" if network_speed else "Unknown"

        except Exception as e:
            return f"Unknown (Error(network): {str(e)})"

    # Function to map the third octet to departments
    
    department_mapping = {
        "14": "Accounts/Fur",
        "10": "Accounts/Shell",
        "8": "Administration",
        "29": "Bio Readers",
        "12": "Design",
        "20": "Design",
        "21": "Design",
        "22": "Design",
        "23": "Design",
        "2": "Electrical Shell",
        "11": "Engineering",
        "1": "ERP Server",
        "26": "IT Centre",
        "4": "ITC Server",
        "5": "Mechanical Fur",
        "7": "Mechanical Shell",
        "9": "Medical",
        "15": "Network Switches",
        "19": "Officers",
        "6": "Personnel",
        "13": "Security",
        "3": "Stores/Shell",
        "17": "Telephone",
        "18": "Workshop/M/Fur",
        "16": "Workshop/M/Shell",
        "24": "WAP",
        "25": "Unix Server",
        "27": "LHB",
        "28": "Stores/Fur",
        "30": "Wireless device",
        "32": "IP Phone",
        "33": "CCTV",
        "34": "FTH",
        "35": "l$D",
        "192": "Others"
        # Add more mappings as needed
    }



    network_info = {
        "Node Type": "Unknown",
        "IP Routing Status": "Unknown",
        "WINS Proxy Status": "Unknown",
        "Interface": "Unknown",
        "IPv4 Address": "Unknown",
        "Department": "Unknown",
        "Description": "Unknown",
        "DHCP Status": "Unknown",
        "Autoconfiguration Status": "Unknown",
        "Link-local IPv6 Address": "Unknown",
        "Subnet Mask": "Unknown",
        "Lease Obtained": "Unknown",
        "Lease Expires": "Unknown",
        "Default Gateway": "Unknown",
        "DHCP Server": "Unknown",
        "DNS Servers": "Unknown",
        "NetBIOS over Tcpip Status": "Unknown",
        "Network Speed": "Unknown",
        "Physical Address": "Unknown"
    }

    try:
        ipconfig_output = subprocess.check_output(["ipconfig", "/all"], universal_newlines=True)
        adapters = ipconfig_output.split("\n\n")

        for adapter_info in adapters:
            lines = adapter_info.splitlines()

            # Process each line in the adapter info
            for line in lines:
                if "Ethernet adapter" in line:
                    network_info["Interface"] = line.split("adapter ")[1].strip(":")
                elif "Description" in line:
                    network_info["Description"] = line.split(":")[1].strip()
                elif "Physical Address" in line:
                    network_info["Physical Address"] = line.split(":")[1].strip()
                elif "DHCP Enabled" in line:
                    network_info["DHCP Status"] = "Enabled" if "Yes" in line else "Disabled"
                elif "Autoconfiguration Enabled" in line:
                    network_info["Autoconfiguration Status"] = "Enabled" if "Yes" in line else "Disabled"
                elif "Link-local IPv6 Address" in line:
                    ipv6_parts = line.split(":", 1)[1].strip().split("(")
                    ipv6_address_parts = ipv6_parts[0].strip().split(":")
                    ipv6_address = ":".join(ipv6_address_parts[:8])  # Limit to the first 8 segments
                    if len(ipv6_address_parts) > 8:
                        interface_and_status = ":".join(ipv6_address_parts[8:])
                        ipv6_address = f"{ipv6_address}%{interface_and_status}"
                    if len(ipv6_parts) > 1:
                        ipv6_status = ipv6_parts[1].strip(")")
                        network_info["Link-local IPv6 Address"] = f"{ipv6_address} ({ipv6_status})"
                    else:
                        network_info["Link-local IPv6 Address"] = ipv6_address
                elif "IPv4 Address" in line:
                    ipv4_address = line.split(":")[1].split("(")[0].strip()
                    network_info["IPv4 Address"] = ipv4_address
                    octet_parts = ipv4_address.split(".")
                    if len(octet_parts) == 4:
                        department = department_mapping.get(octet_parts[2], "Unknown")
                        network_info["Department"] = department  # Add department to network info
                elif "Subnet Mask" in line:
                    network_info["Subnet Mask"] = line.split(":")[1].strip()
                elif "Lease Obtained" in line:
                    network_info["Lease Obtained"] = ":".join(line.split(":")[1:]).strip()
                elif "Lease Expires" in line:
                    network_info["Lease Expires"] = ":".join(line.split(":")[1:]).strip()
                elif "Default Gateway" in line:
                    network_info["Default Gateway"] = line.split(":")[1].strip()
                elif "DHCP Server" in line:
                    network_info["DHCP Server"] = line.split(":")[1].strip()
                elif "DNS Servers" in line:
                    network_info["DNS Servers"] = line.split(":")[1].strip()
                elif "NetBIOS over Tcpip" in line:
                    network_info["NetBIOS over Tcpip Status"] = line.split(":")[1].strip()
                elif "Node Type" in line:
                    network_info["Node Type"] = line.split(":")[1].strip()
                elif "IP Routing Enabled" in line:
                    network_info["IP Routing Status"] = "Enabled" if "Yes" in line else "Disabled"
                elif "WINS Proxy Enabled" in line:
                    network_info["WINS Proxy Status"] = "Enabled" if "Yes" in line else "Disabled"

        # Retrieve network speed information using the inner get_network_speed() function
        network_speed_info = get_network_speed()

        # Add network speed information to the network_info dictionary
        network_info["Network Speed"] = network_speed_info

        # Check if all values are not 'Unknown' before returning
        if all(value != "Unknown" for value in network_info.values()):
            return network_info

    except subprocess.CalledProcessError as e:
        print("Error executing ipconfig:", e)

    return network_info

# Function to print categories
def print_categories(categories):
    try:
        for category, info in categories.items():
            if isinstance(info, list):
                print(f"\n{category}:")
                for item in info:
                    print(f"{item}")
            elif isinstance(info, dict):
                print(f"\n{category}:")
                for key, value in info.items():
                    print(f"{key}: {value}")
            else:
                print(f"\n{category}: {info}")
    except Exception as e:
        print("An error occurred while printing the information:", e)

# Function to get printer details
def get_printer_details():
    try:
        printer_info = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL, None, 2)
        default_printer_name = win32print.GetDefaultPrinter()

        printer_details_list = []

        for printer in printer_info:
            printer_name = printer['pPrinterName']
            is_default = "(Default printer)" if printer_name == default_printer_name else "(not default printer)"
            is_network = "(network printer)" if printer['pPortName'].startswith("\\") else "(not network printer)"
            port_number = printer['pPortName'].replace("\\", "")

            printer_details = {
                "Printer Name": printer_name,
                "Default Status": is_default,
                "Network Status": is_network,
                "Port Number": port_number
            }
            printer_details_list.append(printer_details)

        return printer_details_list

    except Exception as outer_error:
        print("Error retrieving printer details:", outer_error)
        return []

#Function to insert printer details to db
def insert_printer_details_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        printer_details = gathered_info["printer"]
        date = get_custom_date()

        for printer in printer_details:
            name = printer["Printer Name"]
            default_status = printer["Default Status"]
            network_status = printer["Network Status"]
            port_number = printer["Port Number"]

            insert_query = (
                "INSERT INTO printer_configurations (comp_id, name, default_status, network_status, port_number, date) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, name, default_status, network_status, port_number, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Printer details inserted into printer_configurations table.")

    except Exception as e:
        print("Error in insert_printer_details_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get windoes product key
def get_windows_product_key():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform", 0, winreg.KEY_READ)

        # Enumerate values and print their names and data
        for i in range(winreg.QueryInfoKey(key)[1]):
            _ = winreg.EnumValue(key, i)
            #print("Value Name:", value_name)
            #print("Value Data:", value_data)

        product_key, _ = winreg.QueryValueEx(key, "BackupProductKeyDefault")

        return product_key
    except Exception as e:
        print("Error in get_windows_product_key:", str(e))
        return "Not Found"

# Function to push old data to archive
def push_old_data_to_archive(db_connection, existing_record):
    try:
        cursor = db_connection.cursor()

        insert_old_query = (
            "INSERT INTO sys_profile_archive ("
            "computer_id, hostname, department, department_count, node_type, ip_routing_status, wins_proxy_status,"
            "lan_description, lan_interface, lan_speed, lan_mac_address, ipv4_address, ipv6_address,"
            "subnet_mask, default_gateway, netbios_status, autoconfiguration_status, lease_obtained, lease_expiry,"
            "dhcp_status, dhcp_server, dns_server, username, internet_explorer_version, monitor_name,monitor_manufacturer,"
            "monitor_product_code, monitor_serial_number, bios_date, bios_version,"
            "bios_manufacturer, bios_serial_number, system_type, cpu_model, chassis, pc_mac_address, os_name, os_version, os_manufacturer,"
            "os_configuration, os_build_type, os_install_date, product_id, windows_product_key, processor,"
            "total_disk_space, total_free_space, total_partitions, motherboard_manufacturer, motherboard_product,"
            "motherboard_version, total_memory, available_memory, used_memory, memory_usage_percentage,"
            "uptime, update_required, last_checked,total_installed_applications, computer_age, date"
            ") SELECT "
            "computer_id, hostname, department, department_count, node_type, ip_routing_status, wins_proxy_status,"
            "lan_description, lan_interface, lan_speed, lan_mac_address, ipv4_address, ipv6_address,"
            "subnet_mask, default_gateway, netbios_status, autoconfiguration_status, lease_obtained, lease_expiry,"
            "dhcp_status, dhcp_server, dns_server, username, internet_explorer_version, monitor_name,monitor_manufacturer,"
            "monitor_product_code, monitor_serial_number, bios_date, bios_version,"
            "bios_manufacturer, bios_serial_number, system_type, cpu_model, chassis, pc_mac_address, os_name, os_version, os_manufacturer,"
            "os_configuration, os_build_type, os_install_date, product_id, windows_product_key, processor,"
            "total_disk_space, total_free_space, total_partitions, motherboard_manufacturer, motherboard_product,"
            "motherboard_version, total_memory, available_memory, used_memory, memory_usage_percentage,"
            "uptime, update_required, last_checked, total_installed_applications, computer_age, date"
            " FROM sys_profile WHERE pc_mac_address = %s"
        )

        cursor.execute(insert_old_query, (existing_record[36],))
        #print("Existing record pushed to sys_profile_archive table.")

        db_connection.commit()

    except Exception as e:
        print("Error in push_old_data_to_archive:", e)
    finally:
        cursor.close()

# Function to get shared folder details
def get_and_print_shared_folders():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        shared_folders = wmi.ExecQuery("SELECT * FROM Win32_Share")

        shared_folder_details = []

        for folder in shared_folders:
            folder_info = {
                "Name": folder.Name,
                "Caption": folder.Caption,
                "Path": folder.Path,
                "Type": folder.Type
            }
            shared_folder_details.append(folder_info)

        return shared_folder_details

    except Exception as outer_error:
        print("Error retrieving shared folder details:", outer_error)
        return []
    
# Function to insert shared folder info to db 
def insert_shared_folder_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        shared_folders = gathered_info["shared_folder"]
        date = get_custom_date()

        for folder in shared_folders:
            name = folder["Name"]
            caption = folder["Caption"]
            path = folder["Path"]
            folder_type = folder["Type"]

            insert_query = (
                "INSERT INTO shared_directories (comp_id, name, caption, path, type, date) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, name, caption, path, folder_type, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Shared folder information inserted into shared_directories table.")

    except Exception as e:
        print("Error in insert_shared_folder_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get startup programs
def get_and_print_startup_programs():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        startup_programs = wmi.ExecQuery("SELECT * FROM Win32_StartupCommand")

        startup_programs_info = []

        for program in startup_programs:
            program_info = {
                "Name": program.Name,
                "Command": program.Command,
                "Location": program.Location,
                "User": program.User
            }
            startup_programs_info.append(program_info)

        return startup_programs_info

    except Exception as outer_error:
        print("Error retrieving startup program details:", outer_error)
        return []
    
# Function to insert startup programs info to db 
def insert_startup_programs_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        startup_programs = gathered_info["startup"]
        date = get_custom_date()

        for program in startup_programs:
            name = program["Name"]
            command = program["Command"]
            location = program["Location"]
            user = program["User"]

            insert_query = (
                "INSERT INTO startup_config (comp_id, name, command, location, user, date) "
                "VALUES (%s, %s, %s, %s, %s, %s)"
            )
            values = (
                comp_id, name, command, location, user, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("Startup program information inserted into startup_config table.")

    except Exception as e:
        print("Error in insert_startup_programs_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get system hotfix details
def get_and_print_system_hotfixes():
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        hotfixes = wmi.ExecQuery("SELECT * FROM Win32_QuickFixEngineering")

        system_hotfixes_info = []

        for hotfix in hotfixes:
            hotfix_info = {
                "Description": hotfix.Description,
                "Hotfix ID": hotfix.HotfixID
            }
            system_hotfixes_info.append(hotfix_info)

        return system_hotfixes_info

    except Exception as outer_error:
        print("Error retrieving hotfix details:", outer_error)
        return []
    
# Function to insert system hotflix info to db 
def insert_system_hotfixes_info_to_db(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()

        comp_id = gathered_info["computer_id"]
        hotfixes = gathered_info["system_hotfix"]
        date = get_custom_date()

        for hotfix in hotfixes:
            description = hotfix["Description"]
            hotfix = hotfix["Hotfix ID"]

            insert_query = (
                "INSERT INTO system_patch_history (comp_id, description, hotfix_id, date) "
                "VALUES (%s, %s, %s, %s)"
            )
            values = (
                comp_id, description, hotfix, date
            )

            cursor.execute(insert_query, values)
            db_connection.commit()

        #print("System hotfix details inserted into system_patch_history table.")

    except Exception as e:
        print("Error in insert_system_hotfixes_info_to_db:", e)
    finally:
        if cursor:
            cursor.close()

# Function to get system information
def get_system_info():
    try:
        system_info = {}
        c = wmi.WMI()

        try:
            # Gather Windows operating system details using systeminfo command
            result = subprocess.check_output("systeminfo", shell=True, text=True)
            os_name = os_version = os_manufacturer = os_configuration = os_build_type = original_install_date = product_id = "N/A"

            # Process the systeminfo output to extract relevant information
            for line in result.splitlines():
                if line.startswith("OS Name:"):
                    os_name = line.split(":")[1].strip()
                elif line.startswith("OS Version:"):
                    os_version = line.split(":")[1].strip()
                elif line.startswith("OS Manufacturer:"):
                    os_manufacturer = line.split(":")[1].strip()
                elif line.startswith("OS Configuration:"):
                    os_configuration = line.split(":")[1].strip()
                elif line.startswith("OS Build Type:"):
                    os_build_type = line.split(":")[1].strip()
                elif line.startswith("Original Install Date:"):
                    original_install_date_parts = line.split(":", 1)[1].strip().split(",", 1)
                    if len(original_install_date_parts) == 2:
                        original_install_date = original_install_date_parts[1].strip()
                elif line.startswith("Product ID:"):
                    product_id = line.split(":")[1].strip()

        except subprocess.CalledProcessError:
            pass

        # Get system information
        system = c.Win32_ComputerSystem()[0]
        system_info["System Type"] = system.SystemType
        system_info["Model"] = system.Model
        system_info["MAC Address"] = get_mac_address()

        # Get processor information
        processor = c.Win32_Processor()[0]
        system_info["Processor"] = processor.Name

        # Update system info with Windows details
        system_info["OS Name"] = os_name
        system_info["OS Version"] = os_version
        system_info["OS Manufacturer"] = os_manufacturer
        system_info["OS Configuration"] = os_configuration
        system_info["OS Build Type"] = os_build_type
        system_info["Original Install Date"] = original_install_date
        system_info["Product ID"] = product_id
        system_info["Windows Product Key"] = get_windows_product_key()

        return system_info

    except Exception as e:
        print("An error occurred:", str(e))
        return {}

# Function to update existing data
def update_existing_data(db_connection, gathered_info):
    try:
        cursor = db_connection.cursor()
        date = get_custom_date()

        update_query = (
            "UPDATE sys_profile SET "
            "computer_id = %s, hostname = %s, department = %s, department_count = %s, node_type = %s, ip_routing_status = %s, wins_proxy_status = %s,"
            "lan_interface = %s, lan_description = %s, lan_speed = %s, lan_mac_address = %s, ipv4_address = %s, ipv6_address = %s, "
            "subnet_mask = %s, default_gateway = %s, netbios_status = %s, autoconfiguration_status = %s, lease_obtained = %s, "
            "lease_expiry = %s, dhcp_status = %s, dhcp_server = %s, dns_server = %s, internet_explorer_version = %s, monitor_name = %s, "
            "monitor_manufacturer = %s, monitor_product_code = %s, monitor_serial_number = %s, bios_version = %s, bios_manufacturer = %s, "
            "bios_date = %s, bios_serial_number = %s, system_type = %s, cpu_model = %s, chassis = %s, pc_mac_address = %s, os_name = %s, "
            "os_version = %s, os_manufacturer = %s, os_configuration = %s, os_build_type = %s, os_install_date = %s, product_id = %s, "
            "windows_product_key = %s, processor = %s, total_disk_space = %s, total_free_space = %s, total_partitions = %s, "
            "motherboard_manufacturer = %s, motherboard_product = %s, motherboard_version = %s, total_memory = %s, available_memory = %s, "
            "used_memory = %s, memory_usage_percentage = %s, uptime = %s, update_required = %s, last_checked = %s, total_installed_applications = %s, "
            "computer_age = %s, date = %s "
            "WHERE pc_mac_address = %s AND computer_id = %s"
        )

        update_values = (
            gathered_info["computer_id"], gathered_info["hostname"], gathered_info["department"], gathered_info["department_count"], gathered_info["node_type"],
            gathered_info["ip_routing_status"], gathered_info["wins_proxy_status"], gathered_info["lan_interface"],
            gathered_info["lan_description"], gathered_info["lan_speed"], gathered_info["lan_mac_address"],
            gathered_info["ipv4_address"], gathered_info["ipv6_address"], gathered_info["subnet_mask"],
            gathered_info["default_gateway"], gathered_info["netbios_status"], gathered_info["autoconfiguration_status"],
            gathered_info["lease_obtained"], gathered_info["lease_expiry"], gathered_info["dhcp_status"],
            gathered_info["dhcp_server"], gathered_info["dns_server"], gathered_info["internet_explorer_version"],
            gathered_info["monitor_name"], gathered_info["monitor_manufacturer"], gathered_info["monitor_product_code"],
            gathered_info["monitor_serial_number"], gathered_info["bios_version"], gathered_info["bios_manufacturer"],
            gathered_info["bios_date"], gathered_info["bios_serial_number"], gathered_info["system_type"],
            gathered_info["cpu_model"], gathered_info["chassis"], gathered_info["pc_mac_address"],
            gathered_info["os_name"], gathered_info["os_version"], gathered_info["os_manufacturer"],
            gathered_info["os_configuration"], gathered_info["os_build_type"], gathered_info["os_install_date"],
            gathered_info["product_id"], gathered_info["windows_product_key"], gathered_info["processor"],
            gathered_info["total_disk_space"], gathered_info["total_free_space"], gathered_info["total_partitions"],
            gathered_info["motherboard_manufacturer"], gathered_info["motherboard_product"], gathered_info["motherboard_version"],
            gathered_info["total_memory"], gathered_info["available_memory"], gathered_info["used_memory"],
            gathered_info["memory_usage_percentage"], gathered_info["uptime"], gathered_info["update_required"], gathered_info["last_checked"],
            gathered_info["total_installed_applications"], gathered_info["computer_age"], date,
            gathered_info["pc_mac_address"], gathered_info["computer_id"]
        )

        cursor.execute(update_query, update_values)
        #print("Existing record updated with new values.")

        db_connection.commit()

    except Exception as e:
        print("Error in update_existing_data:", e)
    finally:
        cursor.close()

# Function to get system uptime information 
def get_system_uptime():
    boot_time = psutil.boot_time()
    current_time = psutil.time.time()
    uptime_seconds = current_time - boot_time
    
    uptime = datetime.timedelta(seconds=uptime_seconds)
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    formatted_uptime = f"{days} days, {hours:02}:{minutes:02}:{seconds:02}"
    
    boot_time_formatted = datetime.datetime.fromtimestamp(boot_time).strftime('%d-%m-%Y %H:%M:%S')
    
    uptime_info = f"Uptime : {formatted_uptime} (since {boot_time_formatted})"
    
    return uptime_info

# Function to get windows update status
def get_windows_update_status():
    try:
        wua = win32com.client.Dispatch("Microsoft.Update.Session")
        searcher = wua.CreateUpdateSearcher()

        try:
            search_result = searcher.Search("IsInstalled=0 and Type='Software'")
            update_count = search_result.Updates.Count
            history = searcher.QueryHistory(0, 1)
            last_check_timestamp = history.Item(0).Date
            local_timezone = pytz.timezone('Asia/Kolkata')
            last_check_local_time = last_check_timestamp.astimezone(local_timezone)
            
            # Format the time in AM/PM format
            formatted_time = last_check_local_time.strftime('%d %B %Y, %I:%M:%S %p')

            if update_count == 0:
                update_status = {
                    "Update required": "False",
                    "Last Checked": formatted_time
                }
            else:                
                update_status = {
                    "Update required": "True",
                    "Last Checked": formatted_time
                }

            return update_status
        except Exception as e:
            print("An error occurred inside winupdate:", str(e))
            return {
            "Update required": "Unknown",
            "Last Checked": "January 00, 2000, 00:00:00 AM"
        }

    except Exception as e:
        print("An error occurred:", str(e))
        return {
            "Update required": "Unknown",
            "Last Checked": "January 00, 2000, 00:00:00 AM"
        }

# Function to get sys profile archive details
def retrieve_sys_profile_arch():
    try:
        # Get the MAC address (replace this line with your actual MAC address retrieval logic)
        mac_address = get_mac_address()

        # Get database connection details
        db_host, db_user, db_password, db_name = connect_to_database()

        # Establish a connection to your MySQL database
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )

        cursor = conn.cursor()

        # SQL query to retrieve the latest record for the given MAC address
        query = """
        SELECT computer_id, hostname, username, uptime, computer_age, monitor_name, monitor_manufacturer,
        monitor_product_code, monitor_serial_number, system_type, cpu_model, os_name, os_version, os_manufacturer,
        os_configuration, os_build_type, os_install_date, product_id, windows_product_key, processor,
        motherboard_manufacturer, motherboard_product, motherboard_version, total_memory, available_memory,
        used_memory, memory_usage_percentage
        FROM sys_profile_archive
        WHERE pc_mac_address = %s
        ORDER BY date DESC
        LIMIT 1
        """

        cursor.execute(query, (mac_address,))
        row = cursor.fetchone()

        if row:
            # Convert the result into a dictionary
            column_names = [description[0] for description in cursor.description]
            result_dict = dict(zip(column_names, row))
            return result_dict
        else:
            # Return "Unavailable" as values for all fields
            return {
                "computer_id": "Unavailable",
                "hostname": "Unavailable",
                "username": "Unavailable",
                "uptime": "Unavailable",
                "computer_age": "Unavailable",
                "monitor_name": "Unavailable",
                "monitor_manufacturer": "Unavailable",
                "monitor_product_code": "Unavailable",
                "monitor_serial_number": "Unavailable",
                "system_type": "Unavailable",
                "cpu_model": "Unavailable",
                "os_name": "Unavailable",
                "os_version": "Unavailable",
                "os_manufacturer": "Unavailable",
                "os_configuration": "Unavailable",
                "os_build_type": "Unavailable",
                "os_install_date": "Unavailable",
                "product_id": "Unavailable",
                "windows_product_key": "Unavailable",
                "processor": "Unavailable",
                "motherboard_manufacturer": "Unavailable",
                "motherboard_product": "Unavailable",
                "motherboard_version": "Unavailable",
                "total_memory": "Unavailable",
                "available_memory": "Unavailable",
                "used_memory": "Unavailable",
                "memory_usage_percentage": "Unavailable",
            }

    except mysql.connector.Error as e:
        print("Error accessing the database:", e)
        return None

    finally:
        conn.close()

# Function to set up and run Flask app
def run_flask_app(gathered_info, gathered_arch_info):
    app = Flask(__name__)

    # Function to define html urlpath
    def urlpath():
        @app.route("/")
        def index():
            return send_file('templates/index.html')
        
        @app.route('/system')
        def system():
            return render_template('system.html')
        
        @app.route('/user_dashboard')
        def user_dashboard():
            return render_template('user_dashboard.html')
        
        @app.route('/software')
        def software():
            return render_template('software.html')
        
        @app.route('/bios')
        def bios():
            return render_template('bios.html')
        
        @app.route('/local')
        def local():
            return render_template('local.html')
        
        @app.route('/memory_slot')
        def memory_slot():
            return render_template('memory_slot.html')
        
        @app.route('/multimedia')
        def multimedia():
            return render_template('multimedia.html')
        
        @app.route('/cdrom')
        def cdrom():
            return render_template('cdrom.html')
        
        @app.route('/printer')
        def printer():
            return render_template('printer.html')
        
        @app.route('/shared')
        def shared():
            return render_template('shared.html')
        
        @app.route('/disk')
        def disk():
            return render_template('disk.html')
        
        @app.route('/sysprofile')
        def sysprofile():
            return render_template('sysprofile.html')
        
        @app.route('/network')
        def network():
            return render_template('network.html')
        
        @app.route('/startup')
        def startup():
            return render_template('startup.html')
        
        @app.route('/syshotfix')
        def syshotfix():
            return render_template('syshotfix.html')
        
        @app.route('/partition')
        def partition():
            return render_template('partition.html')
        
        @app.route('/update')
        def update():
            return render_template('update.html')
        
        @app.route('/sysprofilearch')
        def sysprofilearch():
            return render_template('sysprofilearch.html')
        
        @app.route('/antivirus')
        def antivirus():
            return render_template('antivirus.html')
    
    # Function for user dashboard html page
    def app_route():
        @app.route('/api/system-info')
        def get_system_info():
            # Return system information as JSON
            return jsonify({
                "MacAddress": gathered_info.get("pc_mac_address", "")
            })
        
        @app.route('/api/software-data')
        def software_info():
            software_data = gathered_info.get("installed_apps","")

            return jsonify(software_data)
        
        @app.route('/api/local-info')
        def local_info():
            local_data = gathered_info.get("user_accounts","")

            return jsonify(local_data)
        
        @app.route('/api/memory-slot-data')
        def get_memory_slot_data():
            memory_slot_data = gathered_info.get("memory_slot_details","")

            return jsonify(memory_slot_data)
        
        @app.route('/api/software-info')
        def get_software_info():
            # Get data from the gathered_info dictionary
            total_installed_softwares = gathered_info.get("total_installed_applications", "")

            # Return software information as JSON
            return jsonify({
                "TotalInstalledSoftwares": total_installed_softwares
            })

        @app.route('/api/bios-info')
        def get_bios_info():
            bios_version = gathered_info.get("bios_version", "")
            bios_manufacturer = gathered_info.get("bios_manufacturer", "")
            bios_date = gathered_info.get("bios_date", "")
            bios_serial_number = gathered_info.get("bios_serial_number", "")

            return jsonify({
                "BiosVersion": bios_version,
                "BiosManufacturer": bios_manufacturer,
                "BiosDate": bios_date,
                "BiosSerialNumber": bios_serial_number
            })

        @app.route('/api/local-users-info')
        def get_local_users_info():
            total_local_users = gathered_info.get("local_user_accounts_count", "")
            return str(total_local_users)

        @app.route('/api/memory-slot-info')
        def get_memory_slot_info():
            total_memory_slots = gathered_info.get("memory_slot_count", "")

            return jsonify({
                "TotalMemorySlots": total_memory_slots
            })
        
        @app.route('/api/multimedia-data')
        def get_multimedia_data():
            multimedia_data = gathered_info.get("multimedia_info","")

            return jsonify(multimedia_data)

        @app.route('/api/multimedia-info')
        def get_multimedia_info():
            total_multimedia_devices = gathered_info.get("multimedia_count", "")

            return jsonify({
                "TotalMultimediaDevices": total_multimedia_devices
            })
        
        @app.route('/api/cdrom-data')
        def get_cdrom_data():
            cdrom_data = gathered_info.get("cd_rom_drives","")

            return jsonify(cdrom_data)

        @app.route('/api/partition-data')
        def get_partition_data():
            partition_data = gathered_info.get("partitions","")

            return jsonify(partition_data)

        @app.route('/api/cd-rom-info')
        def get_cd_rom_info():
            total_cd_roms = gathered_info.get("cd_rom_count", "")

            return jsonify({
                "TotalCDROMs": total_cd_roms
            })

        @app.route('/api/printer-info')
        def get_printer_info():
            total_printers = gathered_info.get("printer_count", "")

            return jsonify({
                "TotalPrinters": total_printers
            })
        
        @app.route('/api/printer-data')
        def get_printer_data():
            printer_data = gathered_info.get("printer","")
            return jsonify(printer_data)
        
        @app.route('/api/startup-data')
        def get_startup_data():
            startup_data = gathered_info.get("startup","")
            return jsonify(startup_data)
        
        @app.route('/api/shared-data')
        def get_shared_data():
            shared_data = gathered_info.get("shared_folder","")
            return jsonify(shared_data)

        @app.route('/api/shared-folder-info')
        def get_shared_folder_info():
            total_shared_folders = gathered_info.get("shared_folder_count", "")

            return jsonify({
                "TotalSharedFolders": total_shared_folders
            })

        @app.route('/api/disk-info')
        def get_disk_info():
            mapped_drives = gathered_info.get("mapped_drives","")
            total_partitions = gathered_info.get("total_partitions","")
            total_disk_space = gathered_info.get("total_disk_space","")
            total_free_space = gathered_info.get("total_free_space", "")
            total_free_space_percentage = gathered_info.get("total_free_space_percentage", "")

            return jsonify({
                "MappedDrives": mapped_drives,
                "TotalPartitions": total_partitions,
                "TotalDiskSpace": total_disk_space,
                "TotalFreeSpace": total_free_space,
                "TotalFreeSpacePercentage": total_free_space_percentage
            })

        @app.route('/api/system-profile-info')
        def get_system_profile_info():
            hostname = gathered_info.get("hostname", "")

            return jsonify({
                "Hostname": hostname,\
            })
        
        @app.route('/api/system-profile-data')
        def get_system_profile_data():
            computer_id = gathered_info.get("computer_id","")
            hostname = gathered_info.get("hostname","")
            username = gathered_info.get("username","")
            uptime = gathered_info.get("uptime","")
            computer_age = gathered_info.get("computer_age","")
            monitor_name = gathered_info.get("monitor_name","")
            monitor_manufacturer = gathered_info.get("monitor_manufacturer","")
            monitor_product_code = gathered_info.get("monitor_product_code","")
            monitor_serial_number = gathered_info.get("monitor_serial_number","")
            system_type = gathered_info.get("system_type","")
            cpu_model = gathered_info.get("cpu_model","")
            os_name = gathered_info.get("os_name","")
            os_version = gathered_info.get("os_version","")
            os_manufacturer = gathered_info.get("os_manufacturer","")
            os_configuration = gathered_info.get("os_configuration","")
            os_build_type = gathered_info.get("os_build_type","")
            os_install_date = gathered_info.get("os_install_date","")
            product_id = gathered_info.get("product_id","")
            product_key = gathered_info.get("windows_product_key","")
            processor = gathered_info.get("processor","")
            
            # Add motherboard-related information
            motherboard_manufacturer = gathered_info.get("motherboard_manufacturer", "")
            motherboard_product = gathered_info.get("motherboard_product", "")
            motherboard_version = gathered_info.get("motherboard_version", "")
            
            # Add memory-related information
            total_memory = gathered_info.get("total_memory", "")
            available_memory = gathered_info.get("available_memory", "")
            used_memory = gathered_info.get("used_memory", "")
            memory_usage_percentage = gathered_info.get("memory_usage_percentage", "")



            return jsonify({"ComputerID": computer_id,
                            "Hostname": hostname,
                            "Username": username,
                            "Uptime": uptime,
                            "ComputerAge": computer_age,
                            "MonitorName": monitor_name,
                            "MonitorManufacturer": monitor_manufacturer,
                            "MonitorProductCode": monitor_product_code,
                            "MonitorSerialNumber": monitor_serial_number,
                            "SystemType": system_type,
                            "CpuModel": cpu_model,
                            "OsName": os_name,
                            "OsVersion": os_version,
                            "OsManufacturer": os_manufacturer,
                            "OsConfiguration": os_configuration,
                            "OsBuildType": os_build_type,
                            "OsInstallDate": os_install_date,
                            "ProductId": product_id,
                            "ProductKey": product_key,
                            "Processor": processor,
                            "MotherboardManufacturer": motherboard_manufacturer,
                            "MotherboardProduct": motherboard_product,
                            "MotherboardVersion": motherboard_version,
                            "TotalMemory": total_memory,
                            "AvailableMemory": available_memory,
                            "UsedMemory": used_memory,
                            "MemoryUsagePercentage": memory_usage_percentage
                            })
        
        @app.route('/api/system-profile-arch-data')
        def get_system_profile_arch_data():
            computer_id = gathered_arch_info.get("computer_id","")
            hostname = gathered_arch_info.get("hostname","")
            username = gathered_arch_info.get("username","")
            uptime = gathered_arch_info.get("uptime","")
            computer_age = gathered_arch_info.get("computer_age","")
            monitor_name = gathered_arch_info.get("monitor_name","")
            monitor_manufacturer = gathered_arch_info.get("monitor_manufacturer","")
            monitor_product_code = gathered_arch_info.get("monitor_product_code","")
            monitor_serial_number = gathered_arch_info.get("monitor_serial_number","")
            system_type = gathered_arch_info.get("system_type","")
            cpu_model = gathered_arch_info.get("cpu_model","")
            os_name = gathered_arch_info.get("os_name","")
            os_version = gathered_arch_info.get("os_version","")
            os_manufacturer = gathered_arch_info.get("os_manufacturer","")
            os_configuration = gathered_arch_info.get("os_configuration","")
            os_build_type = gathered_arch_info.get("os_build_type","")
            os_install_date = gathered_arch_info.get("os_install_date","")
            product_id = gathered_arch_info.get("product_id","")
            product_key = gathered_arch_info.get("windows_product_key","")
            processor = gathered_arch_info.get("processor","")
            
            # Add motherboard-related information
            motherboard_manufacturer = gathered_arch_info.get("motherboard_manufacturer", "")
            motherboard_product = gathered_arch_info.get("motherboard_product", "")
            motherboard_version = gathered_arch_info.get("motherboard_version", "")
            
            # Add memory-related information
            total_memory = gathered_arch_info.get("total_memory", "")
            available_memory = gathered_arch_info.get("available_memory", "")
            used_memory = gathered_arch_info.get("used_memory", "")
            memory_usage_percentage = gathered_arch_info.get("memory_usage_percentage", "")



            return jsonify({"ComputerID": computer_id,
                            "Hostname": hostname,
                            "Username": username,
                            "Uptime": uptime,
                            "ComputerAge": computer_age,
                            "MonitorName": monitor_name,
                            "MonitorManufacturer": monitor_manufacturer,
                            "MonitorProductCode": monitor_product_code,
                            "MonitorSerialNumber": monitor_serial_number,
                            "SystemType": system_type,
                            "CpuModel": cpu_model,
                            "OsName": os_name,
                            "OsVersion": os_version,
                            "OsManufacturer": os_manufacturer,
                            "OsConfiguration": os_configuration,
                            "OsBuildType": os_build_type,
                            "OsInstallDate": os_install_date,
                            "ProductId": product_id,
                            "ProductKey": product_key,
                            "Processor": processor,
                            "MotherboardManufacturer": motherboard_manufacturer,
                            "MotherboardProduct": motherboard_product,
                            "MotherboardVersion": motherboard_version,
                            "TotalMemory": total_memory,
                            "AvailableMemory": available_memory,
                            "UsedMemory": used_memory,
                            "MemoryUsagePercentage": memory_usage_percentage
                            })
        
        @app.route('/api/network-adapter-info')
        def get_network_adapter_info():
            ip_address = gathered_info.get("ipv4_address", "")

            return jsonify({
                "IPAddress": ip_address
            })

        @app.route('/api/network-info')
        def get_network_info():
            node_type = gathered_info.get("node_type", "")
            ip_routing_status = gathered_info.get("ip_routing_status", "")
            wins_proxy_status = gathered_info.get("wins_proxy_status", "")
            lan_interface = gathered_info.get("lan_interface", "")
            lan_description = gathered_info.get("lan_description", "")
            lan_speed = gathered_info.get("lan_speed", "")
            lan_mac_address = gathered_info.get("lan_mac_address", "")
            ipv4_address = gathered_info.get("ipv4_address", "")
            ipv6_address = gathered_info.get("ipv6_address", "")
            subnet_mask = gathered_info.get("subnet_mask", "")
            default_gateway = gathered_info.get("default_gateway", "")
            netbios_status = gathered_info.get("netbios_status", "")
            autoconfiguration_status = gathered_info.get("autoconfiguration_status", "")
            lease_obtained = gathered_info.get("lease_obtained", "")
            lease_expiry = gathered_info.get("lease_expiry", "")
            dhcp_status = gathered_info.get("dhcp_status", "")
            dhcp_server = gathered_info.get("dhcp_server", "")
            dns_server = gathered_info.get("dns_server", "")

            return jsonify({
                "NodeType": node_type,
                "IpRoutingStatus": ip_routing_status,
                "WinsProxyStatus": wins_proxy_status,
                "LanInterface": lan_interface,
                "LanDescription": lan_description,
                "LanSpeed": lan_speed,
                "LanMacAddress": lan_mac_address,
                "Ipv4Address": ipv4_address,
                "Ipv6Address": ipv6_address,
                "SubnetMask": subnet_mask,
                "DefaultGateway": default_gateway,
                "NetbiosStatus": netbios_status,
                "AutoconfigurationStatus": autoconfiguration_status,
                "LeaseObtained": lease_obtained,
                "LeaseExpiry": lease_expiry,
                "DhcpStatus": dhcp_status,
                "DhcpServer": dhcp_server,
                "DnsServer": dns_server
            })
    
        
        @app.route('/api/startup-config-info')
        def get_startup_config_info():
            total_startup_apps = gathered_info.get("startup_count", "")

            return jsonify({
                "TotalStartupApplications": total_startup_apps
            })

        @app.route('/api/system-patch-history')
        def get_system_patch_history():
            total_update_history = gathered_info.get("system_hotflix_count", "")

            return jsonify({
                "TotalUpdateHistory": total_update_history
            })

        @app.route('/api/partition-info')
        def get_partition_info():
            total_partitions = gathered_info.get("total_partitions", "")

            return jsonify({
                "TotalPartitions": total_partitions
            })

        @app.route('/api/update-info')
        def get_update_info():
            update_required = gathered_info.get("update_required", "")

            return jsonify({
                "UpdateRequired": update_required
            })
        
        @app.route('/api/update-data')
        def get_update_data():
            update_required = gathered_info.get("update_required", "")
            last_checked = gathered_info.get("last_checked","")

            return jsonify({
                "UpdateRequired": update_required,
                "LastChecked": last_checked
            })

        @app.route('/api/system-profile-history')
        def get_system_profile_history():
            histories = gathered_info.get("previous_count", "")

            return jsonify({
                "Histories": histories
            })

        @app.route('/api/antivirus-status')
        def get_antivirus_status():
            antivirus_installed = gathered_info.get("antivirus_status", "")

            return jsonify({
                "AntivirusInstalled": antivirus_installed
            })
        
        @app.route('/api/antivirus-data')
        def get_antivirus_data():
            antivirus_status = gathered_info.get("antivirus_status", "")
            antivirus_name = gathered_info.get("antivirus_name","")
            antivirus_version = gathered_info.get("antivirus_version","")
            antivirus_publisher = gathered_info.get("antivirus_publisher","")
            antivirus_install_date = gathered_info.get("antivirus_install_date","")

            return jsonify({
                "AntivirusStatus": antivirus_status,
                "AntivirusName": antivirus_name,
                "AntivirusVersion": antivirus_version,
                "AntivirusPublisher": antivirus_publisher,
                "AntivirusInstallDate": antivirus_install_date
            })
        
        @app.route('/api/computer-id-info')
        def get_computer_id_info():
            computer_id = gathered_info.get("computer_id", "")
            return jsonify({
                "ComputerId": computer_id
            })

        @app.route('/api/hostname-info')
        def get_hostname_info():
            hostname = gathered_info.get("hostname", "")
            return jsonify({
                "Hostname": hostname
            })

        @app.route('/api/department-info')
        def get_department_info():
            department = gathered_info.get("department", "")
            return jsonify({
                "Department": department
            })

        @app.route('/api/ram-info')
        def get_ram_info():
            ram = gathered_info.get("total_memory", "")
            return jsonify({
                "RAM": ram
            })

        @app.route('/api/monitor-info')
        def get_monitor_info():
            monitor = gathered_info.get("monitor_name", "")
            return jsonify({
                "Monitor": monitor
            })

        @app.route('/api/mac-address-info')
        def get_mac_address_info():
            mac_address = gathered_info.get("pc_mac_address", "")
            return jsonify({
                "MacAddress": mac_address
            })

        @app.route('/api/chassis-info')
        def get_chassis_info():
            chassis = gathered_info.get("chassis", "")
            return jsonify({
                "Chassis": chassis
            })

        @app.route('/api/uptime-info')
        def get_uptime_info():
            uptime = gathered_info.get("uptime", "")
            return jsonify({
                "Uptime": uptime
            })
        
        @app.route('/api/computer-age-info')
        def get_computer_age_info():
            computer_age = gathered_info.get("computer_age", "")

            return jsonify({
                "ComputerAge": computer_age
            })
        
        @app.route('/api/username-info')
        def get_username_info():
            username = gathered_info.get("username","")

            return jsonify({
                "Username": username
            })

        @app.route('/api/ip-address-info')
        def get_ip_address_info():
            ip_address = gathered_info.get("ip_address", "")
            return jsonify({
                "IPAddress": ip_address
            })

        @app.route('/api/os-info')
        def get_os_info():
            operating_system = gathered_info.get("os_name", "")
            return jsonify({
                "OperatingSystem": operating_system
            })
        
        @app.route('/api/system-type-info')
        def get_system_type_info():
            system_type = gathered_info.get("system_type", "")
            
            return jsonify({
                "SystemType": system_type
            })
        
        @app.route('/api/cpu-model-info')
        def get_cpu_model_info():
            cpu_model = gathered_info.get("cpu_model", "")
            
            return jsonify({
                "CpuModel": cpu_model
            })
        
        @app.route('/api/hotfix-data')
        def get_hotfix_data():
            system_hotfixes = gathered_info.get("system_hotfix","")
            return jsonify(system_hotfixes)
        


    urlpath()        
    app_route()  # Call the user_dashboard function to start the app
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=8080)

# Main function
def main():
    db_host, db_user, db_password, db_name = connect_to_database()
    # Call the combined function to suppress the warning and set up the console
    #setup_console()

    try:
        db_connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        #print("Connected to the database!")

        gathered_info = gather_system_info()
        gathered_arch_info = retrieve_sys_profile_arch()

        #print(gathered_arch_info)

        #print("about to insert datas into db")

        # Insert gathered data into corresponding tables
        insert_local_user_accounts_to_db(db_connection, gathered_info)
        insert_partition_info_to_db(db_connection, gathered_info)
        insert_cd_info_to_db(db_connection, gathered_info)
        insert_mapped_info_to_db(db_connection, gathered_info)
        insert_memory_slot_details_to_db(db_connection, gathered_info)
        insert_multimedia_info_to_db(db_connection, gathered_info)
        insert_shared_folder_info_to_db(db_connection, gathered_info)
        insert_startup_programs_info_to_db(db_connection, gathered_info)
        insert_printer_details_to_db(db_connection, gathered_info)
        insert_system_hotfixes_info_to_db(db_connection, gathered_info)
        insert_application_info_to_db(db_connection, gathered_info)

        mac_address = gathered_info["pc_mac_address"]
        existing_record = check_existing_record(db_connection, mac_address)
        #print("Checked existing record")

        #print("Existing Record:", existing_record)
        
        if existing_record:
            push_old_data_to_archive(db_connection, existing_record)
            update_existing_data(db_connection, gathered_info)
            
        else:
            insert_new_data(db_connection, gathered_info)
            

        db_connection.commit()

        #print_categories(gathered_info)  # Move this line inside the try block

    except Exception as e:
        print("Error in main function:", e)
    finally:
        if db_connection:
            db_connection.close()
            #print("Database connection closed.")
            welcome_message = """Welcome to PC360 Insights!
            
Greetings,

We extend a warm welcome to you as you embark on your journey with PC360 Insights. Our application has been meticulously designed to provide you with deep insights into your system's information, ensuring that you can make informed decisions based on accurate data.

As you navigate through the features and functionalities, we invite you to explore the capabilities that PC360 Insights offers. We are dedicated to empowering you with the knowledge you need to optimize your system's performance and enhance your overall experience.

Should you require any assistance or have any inquiries, please don't hesitate to reach out to our dedicated support team at support@pc360insights.com. Your satisfaction is our priority, and we are here to ensure your experience with PC360 Insights is seamless and productive.

Thank you for choosing PC360 Insights. We are excited to be part of your journey.

Best regards,
The PC360 Insights Team"""
            #input(welcome_message)

    # Open the default web browser and navigate to the app's URL
    webbrowser.open("http://127.0.0.1:8080/")
    
    # Run the Flask app
    run_flask_app(gathered_info, gathered_arch_info)

# Call the main function to start the process
if __name__ == "__main__":
    main()