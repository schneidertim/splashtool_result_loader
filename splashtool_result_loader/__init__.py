from .splashtool_result_loader import SplashToolResultLoader

def classFactory(iface):
    return SplashToolResultLoader(iface)