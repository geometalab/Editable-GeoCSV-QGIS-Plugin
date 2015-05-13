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

import weakref

from qgis.core import QgsMapLayerRegistry

from PyQt4.QtGui import QFileDialog
from PyQt4.Qt import QMessageBox

from geocsv_ui import GeoCsvDialogNew, GeoCsvDialogConflict, QtHelper
from geocsv_service import GeoCsvDataSourceHandler, GeoCsvVectorLayerFactory
from geocsv_model import CsvVectorLayerDescriptor
from geocsv_exception import *


class GeoCsvNewController:

    _instance = None
    
    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = GeoCsvNewController()
        return cls._instance

    def __init__(self):                
        self.geometryFieldUpdate = False
        
    def createCsvVectorLayer(self, vectorLayers, qgsVectorLayer=None):         
        self.dataSourceHandler = None
        self.vectorDescriptor = None
        self.newDialog = GeoCsvDialogNew()        
        self.initConnections()
        self.initVisibility()
        if qgsVectorLayer:
            csvPath = qgsVectorLayer.customProperty('csv_filepath')
            if csvPath:
                self.newDialog.filePath.setText(csvPath)                     
        self.newDialog.show()
        result = self.newDialog.exec_()
        if result:
            if self.dataSourceHandler and self.vectorDescriptor:                                
                csvVectorLayer = GeoCsvVectorLayerFactory.createCsvVectorLayer(self.dataSourceHandler, self.vectorDescriptor, qgsVectorLayer)
                vectorLayerController = VectorLayerController(csvVectorLayer, self.dataSourceHandler)
                csvVectorLayer.initController(vectorLayerController)
                self.dataSourceHandler.updatePrjFile(csvVectorLayer.qgsVectorLayer.crs().toWkt())                                            
                QgsMapLayerRegistry.instance().addMapLayer(csvVectorLayer.qgsVectorLayer)                
                vectorLayers.append(csvVectorLayer)         
            
    def initConnections(self):
        self.newDialog.fileBrowserButton.clicked.connect(self.onFileBrowserButton)
        self.newDialog.filePath.textChanged.connect(self.onFilePathChange)
        self.newDialog.acceptButton.clicked.connect(self.newDialog.accept)
        self.newDialog.rejectButton.clicked.connect(self.newDialog.reject)
        self.newDialog.pointGeometryTypeRadio.toggled.connect(self.toggleGeometryType)
        self.newDialog.wktGeometryTypeRadio.toggled.connect(self.toggleGeometryType)
        self.newDialog.northingAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        self.newDialog.eastingAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        self.newDialog.wktAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        
    def initVisibility(self):
        self.hideManualGeometryTypeWidget() 
        self.toggleGeometryType()       
                     
    def onFileBrowserButton(self):        
        csvFilePath = QFileDialog.getOpenFileName()
        if csvFilePath:
            self.newDialog.filePath.setText(csvFilePath)            
            
    def onFilePathChange(self):
        csvFilePath = self.newDialog.filePath.text()
        if csvFilePath:                            
            self._updateDataSource(csvFilePath)
            
    def onCsvFileWritingError(self):
        pass
            
    def _updateDataSource(self, csvFilePath):
        try:        
            self.dataSourceHandler = GeoCsvDataSourceHandler(csvFilePath)            
        except InvalidDataSourceException:
            self.newDialog.filePathErrorLabel.setText("invalid file path")
            self.hideManualGeometryTypeWidget()   
        else:            
            self._createVectorDescriptorFromCsvt(csvFilePath)
                            
    def _createVectorDescriptorFromCsvt(self, csvFilePath):
        try:
            self.vectorDescriptor = self.dataSourceHandler.createCsvVectorDescriptorFromCsvt()
            self.newDialog.filePathErrorLabel.setText("")                
        except GeoCsvUnknownAttributeException as e:
            self.newDialog.filePathErrorLabel.setText("unknown csvt attribute: {}".format(e.attributeName))            
        except CsvCsvtMissmatchException:
            self.newDialog.filePathErrorLabel.setText("csv<->csvt missmatch")        
        except GeoCsvUnknownGeometryTypeException:
            self.newDialog.filePathErrorLabel.setText("csvt geometry type exception")            
        except:
            self.newDialog.filePathErrorLabel.setText("no csvt file found")
        self.showManualGeometryTypeWidget()                                        
            
    def _createVectorDescriptorFromManualGeometryDefinition(self):
        if self.newDialog.pointGeometryTypeRadio.isChecked():
            pass
        else:   
            pass     
                   
    def _updateManualGeometryTypeLists(self):
        try:
            attributeNames = self.dataSourceHandler.extractAttributeNamesFromCsv()                    
        except:
            pass
        else:
            self.geometryFieldUpdate = True
            self.newDialog.eastingAttributeDropDown.clear()
            self.newDialog.eastingAttributeDropDown.addItem("----")
            self.newDialog.eastingAttributeDropDown.addItems(attributeNames)
            self.newDialog.northingAttributeDropDown.clear()
            self.newDialog.northingAttributeDropDown.addItem("----")
            self.newDialog.northingAttributeDropDown.addItems(attributeNames)
            self.newDialog.wktAttributeDropDown.clear()
            self.newDialog.wktAttributeDropDown.addItem("----")
            self.newDialog.wktAttributeDropDown.addItems(attributeNames)
            if self.vectorDescriptor:
                if self.vectorDescriptor.descriptorType == CsvVectorLayerDescriptor.pointDescriptorType:
                    self.newDialog.pointGeometryTypeRadio.setChecked(True)
                    self.newDialog.eastingAttributeDropDown.setCurrentIndex(self.vectorDescriptor.eastingIndex + 1)
                    self.newDialog.northingAttributeDropDown.setCurrentIndex(self.vectorDescriptor.northingIndex + 1)
                else:
                    self.newDialog.wktGeometryTypeRadio.setChecked(True)
                    self.newDialog.wktAttributeDropDown.setCurrentIndex(self.vectorDescriptor.wktIndex + 1)
            self.geometryFieldUpdate = False
                   
    def _manualGeometryDropdownChanged(self, index):
        if not self.geometryFieldUpdate and not index == 0:
            self.vectorDescriptor = None
            self.newDialog.filePathErrorLabel.setText("")
            if self.newDialog.pointGeometryTypeRadio.isChecked():
                if not self.newDialog.eastingAttributeDropDown.currentIndex() == 0 and not self.newDialog.northingAttributeDropDown.currentIndex() == 0:
                    try:
                        self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvPointVectorDescriptor(self.newDialog.eastingAttributeDropDown.currentIndex() - 1, self.newDialog.northingAttributeDropDown.currentIndex() - 1)
                    except:
                        self.newDialog.filePathErrorLabel.setText("error in geometry selection")                             
            else:
                try:
                    self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvWktVectorDescriptor(self.newDialog.wktAttributeDropDown.currentIndex() - 1)
                except:
                    self.newDialog.filePathErrorLabel.setText("error in geometry selection") 
                
    def toggleGeometryType(self):    
        if self.newDialog.pointGeometryTypeRadio.isChecked():
            self.newDialog.wktTypeWidget.hide()            
            self.newDialog.pointTypeWidget.show()        
        else:
            self.newDialog.pointTypeWidget.hide()                    
            self.newDialog.wktTypeWidget.show()
            
    def showManualGeometryTypeWidget(self):
        self._updateManualGeometryTypeLists()
        self.toggleGeometryType()
        self.newDialog.manualGeometryWidget.show()        
    
    def hideManualGeometryTypeWidget(self):
        self.newDialog.manualGeometryWidget.hide()  
        
    def _reset(self):
        self.newDialog.filePathErrorLabel.setText("")    


class GeoCsvReconnectController:
    _instance = None
    
    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = GeoCsvReconnectController()
        return cls._instance
    
    def reconnectCsvVectorLayers(self, csvVectorLayers):
        layers = QgsMapLayerRegistry.instance().mapLayers()
        for qgsLayer in layers.itervalues():
            csvFilePath = qgsLayer.customProperty('csv_filepath', '') 
            if csvFilePath:                
                try:        
                    dataSourceHandler = GeoCsvDataSourceHandler(csvFilePath)
                    vectorLayerDescriptor = dataSourceHandler.createCsvVectorDescriptorFromCsvt()
                    csvVectorLayer = GeoCsvVectorLayerFactory.createCsvVectorLayer(dataSourceHandler, vectorLayerDescriptor, qgsLayer)
                    vectorLayerController = VectorLayerController(csvVectorLayer, dataSourceHandler)
                    csvVectorLayer.initController(vectorLayerController)                    
                    csvVectorLayers.append(csvVectorLayer)                                                    
                except:                  
                    GeoCsvNewController.getInstance().createCsvVectorLayer(csvVectorLayers, qgsLayer)
                                
                                        
class VectorLayerController:
    
    def __init__(self, csvVectorLayer, csvDataSourceHandler):        
        self.csvVectorLayer = weakref.ref(csvVectorLayer)
        self.csvDataSourceHandler = csvDataSourceHandler
            
    def syncFeatures(self, features, vectorLayerDescriptor):        
        try:
            self.csvDataSourceHandler.syncFeaturesWithCsv(vectorLayerDescriptor, features)            
            return True
        except:                       
            VectorLayerSaveConflictController(self.csvVectorLayer(), self.csvDataSourceHandler).handleConflict()
            return False
                        
    def updateLayerCrs(self, crsWkt):
        self.csvDataSourceHandler.updatePrjFile(crsWkt)
        
class VectorLayerSaveConflictController:
    def __init__(self, csvVectorLayer, csvDataSourceHandler):        
        self.csvVectorLayer = weakref.ref(csvVectorLayer)
        self.csvDataSourceHandler = csvDataSourceHandler
        self.conflictDialog = None
    
    def handleConflict(self):        
        self._initConflictDialog()
        self.features = self.csvVectorLayer().qgsVectorLayer.getFeatures()
        self.conflictDialog.show()
        self.conflictDialog.exec_()
    
    def _initConflictDialog(self):
        self.conflictDialog = GeoCsvDialogConflict() 
        self.conflictDialog.cancelButton.clicked.connect(self._onConflictCancelButton)
        self.conflictDialog.retryButton.clicked.connect(self._onConflictRetryButton)
        self.conflictDialog.saveAsButton.clicked.connect(self._onConflictSaveAsButton)   
        
    def _onConflictCancelButton(self):
        self.conflictDialog.accept()
    
    def _onConflictRetryButton(self):
        self.conflictDialog.accept()
        try:
            self.csvDataSourceHandler.syncFeaturesWithCsv(self.csvVectorLayer().vectorLayerDescriptor, self.features)
        except FileIOException:
            self.handleConflict()
    
    def _onConflictSaveAsButton(self):        
        filePath = QFileDialog.getSaveFileName(self.conflictDialog, QtHelper.translate("Save File"), "", QtHelper.translate("Files (*.csv)"));
        if filePath:
            self.conflictDialog.accept()
            try:
                self.csvDataSourceHandler.moveDataSourcesToPath(filePath)
                self.csvDataSourceHandler.syncFeaturesWithCsv(self.csvVectorLayer().vectorLayerDescriptor, self.features, filePath)
            except:
                QMessageBox.information(None, "Invalid path", "An error occured while trying to save file on new location. Please try again.")            
        
        
