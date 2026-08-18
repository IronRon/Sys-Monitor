import json
import subprocess


def _run_powershell_json(script):
    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        script,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=True,
    )

    output = result.stdout.strip()

    if not output:
        return None

    return json.loads(output)

def get_hardware_info():

    script = r"""
    $OutputEncoding =
        [Console]::OutputEncoding =
        [System.Text.UTF8Encoding]::new()

    $cpu =
        Get-CimInstance Win32_Processor |
        Select-Object `
            Name,
            Manufacturer,
            NumberOfCores,
            NumberOfLogicalProcessors,
            MaxClockSpeed,
            L2CacheSize,
            L3CacheSize

    $gpus = @(
        Get-CimInstance Win32_VideoController |
        Select-Object `
            Name,
            VideoProcessor,
            DriverVersion,
            AdapterRAM
    )

    $memory = @(
        Get-CimInstance Win32_PhysicalMemory |
        Select-Object `
            Manufacturer,
            PartNumber,
            Capacity,
            Speed,
            ConfiguredClockSpeed,
            DeviceLocator
    )

    $system =
        Get-CimInstance Win32_ComputerSystem |
        Select-Object `
            Manufacturer,
            Model,
            SystemType,
            TotalPhysicalMemory

    $board =
        Get-CimInstance Win32_BaseBoard |
        Select-Object `
            Manufacturer,
            Product,
            Version

    $bios =
        Get-CimInstance Win32_BIOS |
        Select-Object `
            Manufacturer,
            SMBIOSBIOSVersion,
            ReleaseDate

    $disks = @(
        Get-PhysicalDisk |
        ForEach-Object {
            [PSCustomObject]@{
                FriendlyName =
                    $_.FriendlyName

                Manufacturer =
                    $_.Manufacturer

                Model =
                    $_.Model

                MediaType =
                    $_.MediaType.ToString()

                BusType =
                    $_.BusType.ToString()

                HealthStatus =
                    $_.HealthStatus.ToString()

                Size =
                    $_.Size
            }
        }
    )

    [PSCustomObject]@{
        cpu = $cpu
        gpus = $gpus
        memory = $memory
        system = $system
        motherboard = $board
        bios = $bios
        disks = $disks
    } |
    ConvertTo-Json -Depth 6 -Compress
    """

    return _run_powershell_json(
        script
    )