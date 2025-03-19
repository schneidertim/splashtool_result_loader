# Qt imports
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QLocale
from qgis.PyQt.QtGui import QIcon

# QGIS imports
from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer, QgsMessageLog, Qgis
from qgis.gui import QgisInterface  # For type hinting the iface parameter

# Python standard library
import os
import re

# Local imports
from .resources import *

# This plugin is used to load the latest files from the SplashTool output folder
# It will load the files into the current QGIS project
# It will also apply the correct symbology to the layers

class SplashToolResultLoader:
    """QGIS Plugin Implementation."""
    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.init_locale() # load localisation
        self.iface = iface
        self.action = QAction(self.tr("Load Latest Files"), iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.plugin_dir = os.path.dirname(__file__)
                
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        :param message: String for translation.
        :type message: str
        :returns: Translated version of message.
        :rtype: str
        """
        return QCoreApplication.translate('SplashToolResultLoader', message)

    def init_locale(self):
        # Get system locale using QLocale
        locale = QLocale()
        locale_name = locale.name()  # This will return e.g. "de_DE"
        language = locale_name.split('_')[0]  # This will return e.g. "de"
        
        # Try both the full locale name and just the language code
        locale_paths = [
            os.path.join(os.path.dirname(__file__), 'i18n', f"{locale_name}.qm"),
            os.path.join(os.path.dirname(__file__), 'i18n', f"{language}.qm")
        ]
        
        for locale_path in locale_paths:
            if os.path.exists(locale_path):
                self.translator = QTranslator()
                if self.translator.load(locale_path):
                    QCoreApplication.instance().installTranslator(self.translator)
                    QgsMessageLog.logMessage(f"Successfully loaded translation from {locale_path}", 
                                          "SplashTool Result Loader", Qgis.Info)
                    break
                else:
                    QgsMessageLog.logMessage(f"Failed to load translation from {locale_path}", 
                                          "SplashTool Result Loader", Qgis.Warning)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        :type whats_this: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :return: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.tr('&SplashTool Result Loader'),
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.actions = []
        self.menu = self.tr('&SplashTool Result Loader')
        
        icon_path = ':/plugins/splashtool_result_loader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr('Load results from SplashTool'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

        # Will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&SplashTool Result Loader'),
                action)
            self.iface.removeToolBarIcon(action)
        self.iface.removePluginMenu(self.tr("Custom Plugins"), self.action)

    def get_next_group_name(self):
        """Find the next available group name."""
        root = QgsProject.instance().layerTreeRoot()
        base_name = "SplashTool"
        counter = 0
        while True:
            name = base_name if counter == 0 else f"{base_name}_{counter}"
            if not root.findGroup(name):
                return name
            counter += 1

    def run(self):
        input_folder = QFileDialog.getExistingDirectory(None, self.tr("Select Folder containing SplashTool results"))
        if not input_folder:
            QgsMessageLog.logMessage(self.tr("No folder selected"), "SplashTool Result Loader", Qgis.Info)
            return

        QgsMessageLog.logMessage(self.tr("Selected folder: {}").format(input_folder), "SplashTool Result Loader", Qgis.Info)
        
        file_types = {
            "wd": "_wd_out.tif",
            "flow_xy": "flow_xy_out.tif",
            "flowvectors": "flowvectors_\\d+.shp"
        }
        latest_files = {}
        all_flowvectors = []

        # Updated pattern to match your file naming convention
        pattern = re.compile(r"(\d+)(flow_xy_out\.tif|wd_out\.tif|flowvectors_\d+\.shp)$")
        
        files_in_dir = os.listdir(input_folder)
        QgsMessageLog.logMessage(self.tr("Found {} files in directory").format(len(files_in_dir)), 
                               "SplashTool Result Loader", Qgis.Info)

        for file in files_in_dir:
            match = pattern.match(file)
            if match:
                counter, file_suffix = match.groups()
                counter = int(counter)
                
                # Determine the file type based on the suffix
                if file_suffix.endswith("wd_out.tif"):
                    ftype = "wd"
                elif file_suffix.endswith("flow_xy_out.tif"):
                    ftype = "flow_xy"
                elif "flowvectors_" in file_suffix:
                    ftype = "flowvectors"
                    all_flowvectors.append({"filename": file, "counter": counter})
                    continue  # Skip adding to latest_files
                
                if ftype not in latest_files or latest_files[ftype]["counter"] < counter:
                    latest_files[ftype] = {"filename": file, "counter": counter}
                    QgsMessageLog.logMessage(self.tr("Found matching file: {} (type: {}, counter: {})").format(
                        file, ftype, counter), "SplashTool Result Loader", Qgis.Info)

        QgsMessageLog.logMessage(self.tr("Latest files found: {}").format(latest_files), 
                               "SplashTool Result Loader", Qgis.Info)

        # Create a new group
        root = QgsProject.instance().layerTreeRoot()
        group_name = self.get_next_group_name()
        group = root.addGroup(group_name)

        # Dictionary to store loaded layers
        loaded_layers = {
            'flowvectors': [],
            'wd': None,
            'flow_xy': None
        }

        # Load flowvectors layers
        all_flowvectors.sort(key=lambda x: x['counter'], reverse=True)  # Sort by counter in descending order
        for data in all_flowvectors:
            file_path = os.path.join(input_folder, data["filename"])
            suffix = re.search(r'flowvectors_(\d+)\.shp$', data["filename"]).group(1)
            layer_name = f"flowvectors_{suffix}"
            layer = self.load_layer(file_path, layer_name)
            if layer:
                loaded_layers['flowvectors'].append(layer)

        # Load wd and flow layers
        for ftype, data in latest_files.items():
            file_path = os.path.join(input_folder, data["filename"])
            layer = self.load_layer(file_path, ftype)
            if layer:
                loaded_layers[ftype] = layer

        # Add layers to group in specific order
        # First add flowvectors (they're already sorted in descending order)
        for layer in loaded_layers['flowvectors']:
            QgsProject.instance().addMapLayer(layer, False)
            group.addLayer(layer)

        # Add wd layer
        if loaded_layers['wd']:
            QgsProject.instance().addMapLayer(loaded_layers['wd'], False)
            group.addLayer(loaded_layers['wd'])

        # Add flow layer
        if loaded_layers['flow_xy']:
            QgsProject.instance().addMapLayer(loaded_layers['flow_xy'], False)
            group.addLayer(loaded_layers['flow_xy'])

    def load_layer(self, file_path, ftype):
        if file_path.endswith(".tif"):
            layer = QgsRasterLayer(file_path, ftype)
        elif file_path.endswith(".shp"):
            layer = QgsVectorLayer(file_path, ftype, "ogr")
        else:
            QgsMessageLog.logMessage(self.tr("Unsupported file type: {}").format(file_path), 
                                   "SplashTool Result Loader", Qgis.Warning)
            return None

        if not layer.isValid():
            QgsMessageLog.logMessage(self.tr("Failed to load layer: {}").format(file_path), 
                                   "SplashTool Result Loader", Qgis.Critical)
            QMessageBox.critical(None, self.tr("Error"), self.tr("Failed to load {}").format(file_path))
            return None

        QgsMessageLog.logMessage(self.tr("Successfully loaded layer: {}").format(file_path), 
                               "SplashTool Result Loader", Qgis.Info)
        
        # For style application, we need to use the generic "flowvectors" type if it's a flowvector layer
        style_type = "flowvectors" if "flowvectors_" in ftype else ftype
        self.apply_symbology(layer, style_type)
        
        return layer

    def apply_symbology(self, layer, ftype):
        # Map layer types to their style file names
        style_files = {
            "wd": "wd.qml",
            "flow_xy": "flow.qml",
        }
        
        if ftype == "flowvectors":
            # Extract the numeric value from the layer name
            match = re.search(r'flowvectors_(\d+)', layer.name())
            if match:
                value = int(match.group(1))
                # Choose style file based on thresholds
                if value <= 16:
                    style_file = "flowvectors_16.qml"
                elif value <= 32:
                    style_file = "flowvectors_32.qml"
                elif value <= 64:
                    style_file = "flowvectors_64.qml"
                else:  # value > 64, including > 128
                    style_file = "flowvectors_128.qml"
            else:
                # Fallback to default if no number found
                style_file = "flowvectors.qml"
                QgsMessageLog.logMessage(self.tr("No numeric value found in layer name, using default style"), 
                                       "SplashTool Result Loader", Qgis.Warning)
        else:
            style_file = style_files.get(ftype)
            if not style_file:
                QgsMessageLog.logMessage(self.tr("No style mapping for layer type: {}").format(ftype), 
                                       "SplashTool Result Loader", Qgis.Warning)
                return
        
        qml_path = os.path.join(self.plugin_dir, "styles", style_file)
        QgsMessageLog.logMessage(self.tr("Attempting to apply style from: {}").format(qml_path), 
                               "SplashTool Result Loader", Qgis.Info)
        
        if os.path.exists(qml_path):
            success = layer.loadNamedStyle(qml_path)
            if success[1]:  # loadNamedStyle returns a tuple (bool, str)
                QgsMessageLog.logMessage(self.tr("Successfully applied style to {}").format(layer.name()), 
                                       "SplashTool Result Loader", Qgis.Info)
            else:
                QgsMessageLog.logMessage(self.tr("Failed to apply style to {}").format(layer.name()), 
                                       "SplashTool Result Loader", Qgis.Warning)
            layer.triggerRepaint()
        else:
            QgsMessageLog.logMessage(self.tr("Style file not found: {}").format(qml_path), 
                                   "SplashTool Result Loader", Qgis.Warning)
            QMessageBox.warning(None, self.tr("Warning"), 
                              self.tr("QML file not found for {}: {}").format(ftype, qml_path))
