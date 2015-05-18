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
from PyQt4.Qt import QMessageBox, QApplication

from geocsv_ui import GeoCsvDialogNew, GeoCsvDialogConflict
from geocsv_service import GeoCsvDataSourceHandler, GeoCsvVectorLayerFactory
from geocsv_model import CsvVectorLayerDescriptor, GeoCSVAttribute
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
        
    def createCsvVectorLayer(self, vectorLayers, qgsVectorLayer=None, customTitle=None):         
        self.dataSourceHandler = None
        self.vectorDescriptor = None
        self.newDialog = GeoCsvDialogNew()        
        self.initConnections()
        self.initVisibility()
        if customTitle:
            self.newDialog.setWindowTitle(customTitle)
        if qgsVectorLayer:
            csvPath = qgsVectorLayer.customProperty('csv_filepath')
            if csvPath:
                self.newDialog.filePath.setText(csvPath)
        self._updateAcceptButton()
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
        self.newDialog.pointGeometryTypeRadio.toggled.connect(self._toggleGeometryType)
        self.newDialog.wktGeometryTypeRadio.toggled.connect(self._toggleGeometryType)
        self.newDialog.northingAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        self.newDialog.eastingAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        self.newDialog.wktAttributeDropDown.currentIndexChanged.connect(self._manualGeometryDropdownChanged)
        
    def initVisibility(self):
        self._hideManualGeometryTypeWidget() 
        self._toggleGeometryType()       
                     
    def onFileBrowserButton(self):        
        csvFilePath = QFileDialog.getOpenFileName()
        if csvFilePath:
            self.newDialog.filePath.setText(csvFilePath)            
            
    def onFilePathChange(self):
        self.dataSourceHandler = None
        self.vectorDescriptor = None
        csvFilePath = self.newDialog.filePath.text()
        if csvFilePath:                            
            self._updateDataSource(csvFilePath)
        else:            
            self.newDialog.filePathErrorLabel.setText("")
        self._updateAcceptButton()
                       
    def _updateDataSource(self, csvFilePath):
        try:        
            self.dataSourceHandler = GeoCsvDataSourceHandler(csvFilePath)            
        except InvalidDataSourceException:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','invalid file path'))            
            self._hideManualGeometryTypeWidget()   
        else:            
            self._createVectorDescriptorFromCsvt(csvFilePath)
                            
    def _createVectorDescriptorFromCsvt(self, csvFilePath):
        try:
            self.vectorDescriptor = self.dataSourceHandler.createCsvVectorDescriptorFromCsvt()
            self.newDialog.filePathErrorLabel.setText("")                
        except GeoCsvUnknownAttributeException as e:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','unknown csvt attribute: {}').format(e.attributeName))            
        except CsvCsvtMissmatchException:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','csv<->csvt missmatch'))        
        except GeoCsvUnknownGeometryTypeException:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','csvt geometry type exception'))            
        except:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','no csvt file found'))
        self._showManualGeometryTypeWidget()                                        
                               
    def _updateManualGeometryTypeLists(self):
        try:
            attributeNames = self.dataSourceHandler.extractAttributeNamesFromCsv()                    
        except:
            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','error while loading csv'))
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
        if not self.geometryFieldUpdate:
            self.vectorDescriptor = None
            self.newDialog.filePathErrorLabel.setText("")
            if not index == 0:
                if self.newDialog.pointGeometryTypeRadio.isChecked():
                    if not self.newDialog.eastingAttributeDropDown.currentIndex() == 0 and not self.newDialog.northingAttributeDropDown.currentIndex() == 0:
                        try:
                            self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvPointVectorDescriptor(self.newDialog.eastingAttributeDropDown.currentIndex() - 1, self.newDialog.northingAttributeDropDown.currentIndex() - 1)
                        except:
                            self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','error in geometry selection'))                             
                else:
                    try:
                        self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvWktVectorDescriptor(self.newDialog.wktAttributeDropDown.currentIndex() - 1)
                    except:
                        self.newDialog.filePathErrorLabel.setText(QApplication.translate('GeoCsvNewController','error in geometry selection')) 
        self._updateAcceptButton()
                
    def _toggleGeometryType(self):    
        if self.newDialog.pointGeometryTypeRadio.isChecked():
            self.newDialog.wktTypeWidget.hide()            
            self.newDialog.pointTypeWidget.show()        
        else:
            self.newDialog.pointTypeWidget.hide()                    
            self.newDialog.wktTypeWidget.show()
            
    def _showManualGeometryTypeWidget(self):
        self._updateManualGeometryTypeLists()
        self._toggleGeometryType()
        self.newDialog.manualGeometryWidget.show()        
    
    def _hideManualGeometryTypeWidget(self):
        self.newDialog.manualGeometryWidget.hide() 
           
    def _updateAcceptButton(self):
        self.newDialog.acceptButton.setEnabled(self._isValid())
                    
    def _isValid(self):
        return not self.dataSourceHandler == None and not self.vectorDescriptor == None    
        


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
                    GeoCsvNewController.getInstance().createCsvVectorLayer(csvVectorLayers, qgsLayer, QApplication.translate('GeoCsvReconnectController','Couldn\'t automatically restore csv layer "{}"').format(qgsLayer.name()))
                                
                                        
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
        
    def addAttributes(self, attributes, vectorLayerDescriptor):        
        for attribute in attributes:
            # : :type attribute: QgsField  
            vectorLayerDescriptor.addAttribute(GeoCSVAttribute.createFromQgsField(attribute))
        try:
            self.csvDataSourceHandler.updateCsvtFile(vectorLayerDescriptor.getAttributeTypes())
        except:
            QMessageBox.information(None, QApplication.translate('VectorLayerSaveConflictController','CSVT file could not be updated'), QApplication.translate('VectorLayerSaveConflictController','An error occured while trying to update the CSVT file according to the new attribute types. Please update the csvt file manually.'))

    def deleteAttributes(self, attributeIds, vectorLayerDescriptor):
        try:
            for attributeId in attributeIds:
                vectorLayerDescriptor.deleteAttributeAtIndex(attributeId)
        except:
            QMessageBox.information(None, QApplication.translate('VectorLayerSaveConflictController','Error while updating attributes happend'), QApplication.translate('VectorLayerSaveConflictController','An error occured while trying to update the attributes list. Nothing has been stored on disk.'))
        else:
            try:
                self.csvDataSourceHandler.updateCsvtFile(vectorLayerDescriptor.getAttributeTypes())
            except:
                QMessageBox.information(None, QApplication.translate('VectorLayerSaveConflictController','CSVT file could not be updated'), QApplication.translate('VectorLayerSaveConflictController','An error occured while trying to update the CSVT file according to the new attribute types. Please update the csvt file manually.'))
                
    def checkDeleteAttribute(self, attributeId, vectorLayerDescriptor):
        if vectorLayerDescriptor.indexIsGeoemtryIndex(attributeId):
            QMessageBox.information(None, QApplication.translate('VectorLayerSaveConflictController','Geometry index violation'), QApplication.translate('VectorLayerSaveConflictController','You tried to delete an attribute which is providing geometry information. The change will not be saved to disk.'))
                        
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
        filePath = QFileDialog.getSaveFileName(self.conflictDialog, QApplication.translate('VectorLayerSaveConflictController','Save File'), "", QApplication.translate('VectorLayerSaveConflictController','Files (*.csv)'));
        if filePath:
            self.conflictDialog.accept()
            try:
                self.csvDataSourceHandler.moveDataSourcesToPath(filePath)
                self.csvDataSourceHandler.syncFeaturesWithCsv(self.csvVectorLayer().vectorLayerDescriptor, self.features, filePath)
            except:
                QMessageBox.information(None, QApplication.translate('VectorLayerSaveConflictController','Invalid path'), QApplication.translate('VectorLayerSaveConflictController','An error occured while trying to save file on new location. Please try again.'))            
        
        
