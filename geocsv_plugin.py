# -*- coding: utf-8 -*-
"""
/***************************************************************************
Editable GeoCSV
A QGIS plugin
                              -------------------
begin                : 2015-04-29        
copyright            : (C) 2015 by geometalab
email                : geometalab@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os.path

from qgis.core import QgsProject, QgsSettings
from qgis.gui import QgsMessageBar
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

from . import resources_rc
from .geocsv_controller import GeoCsvNewController, GeoCsvReconnectController
from .geocsv_service import NotificationHandler


class EditableGeoCsvPlugin:

    def __init__(self, iface):
        self._iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale', 'en')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'geocsv_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        NotificationHandler.configureIface(iface)
        self.settings = QSettings("Editable GeoCSV", "editablegeocsv")
        self.csvVectorLayers = []
        QgsProject.instance().readProject.connect(
            lambda: GeoCsvReconnectController.getInstance().reconnectCsvVectorLayers(self.csvVectorLayers)
        )
        self._connectToRefreshAction()

    def initGui(self):
        addGeoCsvLayerIcon = QIcon(':/plugins/editablegeocsv/geocsv.png')
        addGeoCsvLayerText = QCoreApplication.translate('EditableGeoCsvPlugin', 'Add GeoCSV layer')
        self.addGeoCsvLayerAction = QAction(addGeoCsvLayerIcon, addGeoCsvLayerText, self._iface.mainWindow())
        self.addGeoCsvLayerAction.triggered.connect(
            lambda: GeoCsvNewController(self.settings).createCsvVectorLayer(self.csvVectorLayers)
        )
        self._iface.addToolBarIcon(self.addGeoCsvLayerAction)
        self._iface.addPluginToVectorMenu(
            QCoreApplication.translate('EditableGeoCsvPlugin', 'Editable GeoCSV'), self.addGeoCsvLayerAction
        )

    def unload(self):
        self._iface.removePluginMenu(
            QCoreApplication.translate('EditableGeoCsvPlugin', 'Editable GeoCSV'),
            self.addGeoCsvLayerAction)
        self._iface.removeToolBarIcon(self.addGeoCsvLayerAction)

    def _connectToRefreshAction(self):
        for action in self._iface.mapNavToolBar().actions():
            if action.objectName() == "mActionDraw":
                action.triggered.connect(lambda: self._refreshCsvVectorLayers())
                break

    def _refreshCsvVectorLayers(self):
        newCsvVectorLayers = []
        GeoCsvReconnectController.getInstance().reconnectCsvVectorLayers(newCsvVectorLayers)
        self.csvVectorLayers = newCsvVectorLayers
        self._iface.mapCanvas().refreshAllLayers()