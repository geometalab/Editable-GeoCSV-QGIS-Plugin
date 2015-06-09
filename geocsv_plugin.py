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
 
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QIcon, QAction
import resources_rc
from geocsv_controller import GeoCsvNewController, GeoCsvReconnectController
from geocsv_service import NotificationHandler

# import sys;
# sys.path.append(r'/Applications/liclipse/plugins/org.python.pydev_3.9.2.201502042042/pysrc')
# import pydevd

class EditableGeoCsv:

    def __init__(self, iface):          
#         pydevd.settrace()                                
        self._iface = iface        
        self.plugin_dir = os.path.dirname(__file__)        
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n','geocsv_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        NotificationHandler.configureIface(iface)
        #container for all csv vector layers                        
        self.csvVectorLayers = []          
        #if the project file is successfully read, reconnect all CsvVectorLayers with its datasource
        self._iface.projectRead.connect(lambda: GeoCsvReconnectController.getInstance().reconnectCsvVectorLayers(self.csvVectorLayers))
        #connect to the qgis refresh button
        self._connectToRefreshAction()
        
    
                                                      
    def initGui(self):
        addGeoCsvLayerIcon = QIcon(':/plugins/editablegeocsv/geocsv.png')
        addGeoCsvLayerText = QCoreApplication.translate('EditableGeoCsv', 'Add GeoCSV layer')        
        self.addGeoCsvLayerAction = QAction(addGeoCsvLayerIcon, addGeoCsvLayerText, self._iface.mainWindow())
        self.addGeoCsvLayerAction.triggered.connect(lambda: GeoCsvNewController.getInstance().createCsvVectorLayer(self.csvVectorLayers))
        self._iface.addToolBarIcon(self.addGeoCsvLayerAction)
        self._iface.addPluginToMenu(QCoreApplication.translate('EditableGeoCsv', 'Editable GeoCSV'), self.addGeoCsvLayerAction)
                        
    def unload(self):        
        self._iface.removePluginMenu(
            QCoreApplication.translate('EditableGeoCsv', 'Editable GeoCSV'),
            self.addGeoCsvLayerAction)
        self._iface.removeToolBarIcon(self.addGeoCsvLayerAction)
        
    def _connectToRefreshAction(self):
        for action in self._iface.mapNavToolToolBar().actions():
            if action.objectName() == "mActionDraw":
                action.triggered.connect(lambda: self._refreshCsvVectorLayers())                                              
    
    def _refreshCsvVectorLayers(self):
        newCsvVectorLayers = []
        GeoCsvReconnectController.getInstance().reconnectCsvVectorLayers(newCsvVectorLayers)
        self.csvVectorLayers = newCsvVectorLayers
        self._iface.mapCanvas().refresh()