# LibreHardwareMonitor

This directory contains the LibreHardwareMonitor library files used by the IP Manager application for hardware monitoring functionality.

## What is LibreHardwareMonitor?

LibreHardwareMonitor is free and open source software that can monitor the temperature sensors, fan speeds, voltages, load and clock speeds of your computer. It is a fork of OpenHardwareMonitor with improved hardware support and active development.

## Files Included

- `LibreHardwareMonitorLib.dll` - Core library for hardware monitoring
- `LibreHardwareMonitor.exe` - Executable for WMI service
- `Aga.Controls.dll` - UI controls library
- `OxyPlot.dll` - Charting library
- `OxyPlot.WindowsForms.dll` - Windows Forms charting components
- `System.CodeDom.dll` - .NET Framework component
- `Microsoft.Win32.TaskScheduler.dll` - Task scheduling library
- `Newtonsoft.Json.dll` - JSON processing library
- `HidSharp.dll` - HID device communication library

## License

LibreHardwareMonitor is licensed under the Mozilla Public License Version 2.0 (MPL 2.0). See the [LICENSE](LICENSE) file for full details.

## Usage in IP Manager

The IP Manager application uses LibreHardwareMonitor to:
- Monitor CPU and GPU temperatures
- Monitor fan speeds
- Display hardware information in a user-friendly interface
- Provide real-time hardware monitoring with color-coded badges

## Integration

The application integrates LibreHardwareMonitor through:
- Direct DLL loading via pythonnet
- WMI (Windows Management Instrumentation) interface
- Custom sensor data processing and display

## More Information

- **GitHub Repository**: https://github.com/LibreHardwareMonitor/LibreHardwareMonitor
- **License**: Mozilla Public License Version 2.0
- **Version**: Latest stable release

## Requirements

- Windows 10/11 (64-bit)
- .NET Framework 4.7.2 or later
- Administrator privileges (for some hardware sensors)

---
*最后更新: 2025-08-20 23:54*
*维护者: AI Assistant* 