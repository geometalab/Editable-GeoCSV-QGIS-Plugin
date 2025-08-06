import sys
import unittest
from unittest.mock import MagicMock

# Mock the qgis and PyQt5 modules
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['qgis.gui'] = MagicMock()
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()
sys.modules['PyQt5.QtGui'] = MagicMock()
sys.modules['PyQt5.QtWidgets'] = MagicMock()

class QgsWkbTypes:
    class Type:
        Point = 1
        LineString = 2
        Polygon = 3

sys.modules['qgis.core'].QgsWkbTypes = QgsWkbTypes

# Configure the mock QgsGeometry
mock_geom = MagicMock()
mock_geom.type.return_value = QgsWkbTypes.Type.Point
sys.modules['qgis.core'].QgsGeometry.fromWkt.return_value = mock_geom


# Discover and run tests
if __name__ == '__main__':
    # Add the project root to the python path
    sys.path.insert(0, '.')

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('test')
    runner = unittest.TextTestRunner()
    runner.run(suite)
