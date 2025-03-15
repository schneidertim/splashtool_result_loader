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
        # Get system locale using QLocale instead of QApplication
        locale = QLocale().name()  # This will return e.g. "de_DE"
        locale_path = os.path.join(os.path.dirname(__file__), 'i18n', f"{locale}.qm")
    
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.instance().installTranslator(self.translator)

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

    def run(self):
        input_folder = QFileDialog.getExistingDirectory(None, self.tr("Select Input Folder"))
        if not input_folder:
            QgsMessageLog.logMessage("No folder selected", "SplashTool Result Loader", Qgis.Info)
            return

        QgsMessageLog.logMessage(f"Selected folder: {input_folder}", "SplashTool Result Loader", Qgis.Info)
        
        file_types = {
            "wd": "_wd_out.tif",
            "flow_xy": "flow_xy_out.tif",
            "flowvectors": "flowvectors_\\d+.shp"
        }
        latest_files = {}

        # Updated pattern to match your file naming convention
        pattern = re.compile(r"(\d+)(flow_xy_out\.tif|_wd_out\.tif|flowvectors_\d+\.shp)$")
        
        files_in_dir = os.listdir(input_folder)
        QgsMessageLog.logMessage(f"Found {len(files_in_dir)} files in directory", "SplashTool Result Loader", Qgis.Info)

        for file in files_in_dir:
            match = pattern.match(file)
            if match:
                counter, file_suffix = match.groups()
                counter = int(counter)
                
                # Determine the file type based on the suffix
                if file_suffix.endswith("_wd_out.tif"):
                    ftype = "wd"
                elif file_suffix.endswith("flow_xy_out.tif"):
                    ftype = "flow_xy"
                elif "flowvectors_" in file_suffix:
                    ftype = "flowvectors"
                
                if ftype not in latest_files or latest_files[ftype]["counter"] < counter:
                    latest_files[ftype] = {"filename": file, "counter": counter}
                    QgsMessageLog.logMessage(f"Found matching file: {file} (type: {ftype}, counter: {counter})", 
                                          "SplashTool Result Loader", Qgis.Info)

        QgsMessageLog.logMessage(f"Latest files found: {latest_files}", "SplashTool Result Loader", Qgis.Info)

        for ftype, data in latest_files.items():
            file_path = os.path.join(input_folder, data["filename"])
            QgsMessageLog.logMessage(f"Attempting to load: {file_path}", "SplashTool Result Loader", Qgis.Info)
            self.load_layer(file_path, ftype)

    def load_layer(self, file_path, ftype):
        if file_path.endswith(".tif"):
            layer = QgsRasterLayer(file_path, ftype)
        elif file_path.endswith(".shp"):
            layer = QgsVectorLayer(file_path, ftype, "ogr")
        else:
            QgsMessageLog.logMessage(f"Unsupported file type: {file_path}", "SplashTool Result Loader", Qgis.Warning)
            return

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load layer: {file_path}", "SplashTool Result Loader", Qgis.Critical)
            QMessageBox.critical(None, self.tr("Error"), self.tr("Failed to load {}").format(file_path))
            return

        QgsProject.instance().addMapLayer(layer)
        QgsMessageLog.logMessage(f"Successfully loaded layer: {file_path}", "SplashTool Result Loader", Qgis.Info)
        
        self.apply_symbology(layer, ftype)

    def apply_symbology(self, layer, ftype):
        # Map layer types to their style file names
        style_files = {
            "wd": "wd.qml",
            "flow_xy": "flow.qml",  # Changed from flow_xy.qml to flow.qml
            "flowvectors": "flowvectors.qml"
        }
        
        style_file = style_files.get(ftype)
        if not style_file:
            QgsMessageLog.logMessage(f"No style mapping for layer type: {ftype}", 
                                   "SplashTool Result Loader", Qgis.Warning)
            return
        
        qml_path = os.path.join(self.plugin_dir, "styles", style_file)
        QgsMessageLog.logMessage(f"Attempting to apply style from: {qml_path}", 
                               "SplashTool Result Loader", Qgis.Info)
        
        if os.path.exists(qml_path):
            success = layer.loadNamedStyle(qml_path)
            if success[1]:  # loadNamedStyle returns a tuple (bool, str)
                QgsMessageLog.logMessage(f"Successfully applied style to {layer.name()}", 
                                       "SplashTool Result Loader", Qgis.Info)
            else:
                QgsMessageLog.logMessage(f"Failed to apply style to {layer.name()}", 
                                       "SplashTool Result Loader", Qgis.Warning)
            layer.triggerRepaint()
        else:
            QgsMessageLog.logMessage(f"Style file not found: {qml_path}", 
                                   "SplashTool Result Loader", Qgis.Warning)
            QMessageBox.warning(None, self.tr("Warning"), 
                              self.tr("QML file not found for {}: {}").format(ftype, qml_path))
