from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QCoreApplication, QTranslator, QgsProject, QgsRasterLayer, QgsVectorLayer
import os
import re

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
        self.action = QAction("Load Latest Files", iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.plugin_dir = os.path.dirname(__file__)
                
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    def init_locale(self):
            locale = QCoreApplication.instance().locale().name()  # z.B. "de_DE"
            locale_path = os.path.join(os.path.dirname(__file__), 'i18n', f"{locale}.qm")
    
            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)
                QCoreApplication.instance().installTranslator(self.translator)

    def initGui(self):        
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        
        icon_path = ':/plugins/splashtool_result_loader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Load results from SplashTool'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        self.iface.addPluginToMenu("Custom Plugins", self.action)

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SplashTool Result Loader'),
                action)
            self.iface.removeToolBarIcon(action)
        self.iface.removePluginMenu("Custom Plugins", self.action)

    def run(self):
        input_folder = QFileDialog.getExistingDirectory(None, "Select Input Folder")
        if not input_folder:
            return

        file_types = {"wd": ".tif", "flow_xy": ".tif", "flowvectors": ".shp"}
        latest_files = {}

        pattern = re.compile(r"(\\d+)(wd|flow_xy|flowvectors)([^\\\\/]*)(\\.tif|\\.shp)$")

        for file in os.listdir(input_folder):
            match = pattern.match(file)
            if match:
                counter, ftype, _, ext = match.groups()
                counter = int(counter)
                if ftype in file_types and ext == file_types[ftype]:
                    if ftype not in latest_files or latest_files[ftype]["counter"] < counter:
                        latest_files[ftype] = {"filename": file, "counter": counter}

        for ftype, data in latest_files.items():
            file_path = os.path.join(input_folder, data["filename"])
            self.load_layer(file_path, ftype)

    def load_layer(self, file_path, ftype):
        if file_path.endswith(".tif"):
            layer = QgsRasterLayer(file_path, ftype)
        elif file_path.endswith(".shp"):
            layer = QgsVectorLayer(file_path, ftype, "ogr")
        else:
            return

        if not layer.isValid():
            QMessageBox.critical(None, "Error", f"Failed to load {file_path}")
            return

        QgsProject.instance().addMapLayer(layer)
        self.apply_symbology(layer, ftype)

    def apply_symbology(self, layer, ftype):
        qml_path = os.path.join(self.plugin_dir, "styles", f"{ftype}.qml")
        if os.path.exists(qml_path):
            layer.loadNamedStyle(qml_path)
            layer.triggerRepaint()
        else:
            QMessageBox.warning(None, "Warning", f"QML file not found for {ftype}: {qml_path}")
