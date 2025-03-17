# SplashTool Result Loader QGIS Plugin

A QGIS plugin that automatically loads and symbolizes results from a SplashTool output directory. This plugin identifies the latest iteration results and adds them to your current QGIS project with appropriate styling.

## Features

- Automatically detects and loads the latest SplashTool result files
- Applies predefined symbology for flow accumulation paths and water depths
- Supports multiple languages through i18n
- Simple one-click operation through QGIS toolbar

## Installation

1. Download the plugin from the QGIS Plugin Repository
   - Open QGIS
   - Go to Plugins > Manage and Install Plugins
   - Search for "SplashTool Result Loader"
   - Click "Install Plugin"

2. Manual Installation
   - Download the latest release from the [GitHub repository](https://github.com/schneidertim/splashtool_result_loader)
   - Unzip the downloaded file
   - Copy the entire folder to your QGIS plugins directory:
     - Windows: `C:\Users\{username}\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
     - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
     - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## Usage

1. Click the SplashTool Result Loader icon in the QGIS toolbar
2. Select your SplashTool output directory
3. The plugin will automatically:
   - Find the latest iteration results
   - Load the flow paths and water depth layers
   - Apply appropriate symbology
   - Add the layers to your current project

## Requirements

- QGIS 3.0 or later
- SplashTool output directory with valid results

## Development

### Setup Development Environment

1. Clone the repository:
```bash
git clone https://github.com/schneidertim/splashtool_result_loader.git
```

2. Create a symbolic link from your development directory to the QGIS plugins folder:
```bash
# Windows (Run as Administrator)
mklink /D "%AppData%\QGIS\QGIS3\profiles\default\python\plugins\splashtool_result_loader" "path\to\your\cloned\repo"

# Linux/macOS
ln -s /path/to/your/cloned/repo ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/splashtool_result_loader
```

### Building Resources

If you modify the resources.qrc file, rebuild the resources.py file:
```bash
pyrcc5 -o resources.py resources.qrc
```

## Support

- Issue Tracker: [GitHub Issues](https://github.com/schneidertim/splashtool_result_loader/issues)
- Homepage: [www.splashtool.de](https://www.splashtool.de)

## License

This project is licensed under the GPL V3 License - see the [LICENSE](LICENSE) file for details.

## Author

Tim Schneider (t.schneider@splashtool.de)

## Changelog

### Version 0.1
- Initial release
- Basic functionality for loading SplashTool results
- Layer symbolization
- Multi-language support 