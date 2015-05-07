'''
Created on 05.05.2015

@author: faustos
'''

from qgis.core import QgsMapLayerRegistry


from PyQt4.QtGui import QFileDialog

from geocsv_ui import GeoCsvDialogNew
from geocsv_service import GeoCsvVectorLayerFactory, GeoCsvDataSourceHandler

from geocsv_exception import *

class GeoCsvNewController:
    
    def __init__(self, vectorLayers):
        self.newDialog = GeoCsvDialogNew()        
        self.initConnections()
        self.initVisibility()
        self.vectorLayers = vectorLayers
        self.dataSourceHandler = None
        self.vectorDescriptor = None
    
    def initConnections(self):
        self.newDialog.fileBrowserButton.clicked.connect(self.onFileBrowserButton)
        self.newDialog.filePath.textChanged.connect(self.onFilePathChange)
        self.newDialog.acceptButton.clicked.connect(self.newDialog.accept)
        self.newDialog.rejectButton.clicked.connect(self.newDialog.reject)
        self.newDialog.pointGeometryTypeRadio.toggled.connect(self.toggleGeometryType)
        self.newDialog.wktGeometryTypeRadio.toggled.connect(self.toggleGeometryType)
        
    def initVisibility(self):
        self.hideManualGeometryTypeWidget() 
        self.toggleGeometryType()       
            
            
    def createCsvVectorLayer(self):                        
        self.newDialog.show()
        result = self.newDialog.exec_()
        if result:
            if self.dataSourceHandler and self.vectorDescriptor:                
                csvVectorLayer = GeoCsvVectorLayerFactory.createVectorLayer(self.dataSourceHandler, self.vectorDescriptor)                                
                QgsMapLayerRegistry.instance().addMapLayer(csvVectorLayer.vectorLayer)
                self.vectorLayers.append(csvVectorLayer)     
        
         
    def onFileBrowserButton(self):        
        csvFilePath = QFileDialog.getOpenFileName()
        if csvFilePath:
            self.newDialog.filePath.setText(csvFilePath)            
            
    def onFilePathChange(self):
        csvFilePath = self.newDialog.filePath.text()
        if csvFilePath:
            self.initCsvDataSourceHandler(csvFilePath)
            
    def initCsvDataSourceHandler(self, csvFilePath):
        try:        
            self.dataSourceHandler = GeoCsvDataSourceHandler(csvFilePath)
            try:
                self.vectorDescriptor = self.dataSourceHandler.createCsvVectorDescriptor()
                self.newDialog.filePathErrorLabel.setText("")
                self.hideManualGeometryTypeWidget()
            except GeoCsvUnknownAttributeException as e:
                self.newDialog.filePathErrorLabel.setText("unknown csvt attribute {} at index {}".format(e.attributeName, e.attributeIndex))
                self.showManualGeometryTypeWidget()
            except CsvCsvtMissmatchException:
                self.newDialog.filePathErrorLabel.setText("csv<->csvt missmatch")
                self.showManualGeometryTypeWidget()
            except:
                self.newDialog.filePathErrorLabel.setText("no csvt file found")
                self.showManualGeometryTypeWidget()
        except:
            self.newDialog.filePathErrorLabel.setText("invalid file path")
            self.hideManualGeometryTypeWidget()
            
    def toggleGeometryType(self):
        if self.newDialog.pointGeometryTypeRadio.isChecked():
             self.newDialog.wktTypeWidget.hide()
             self.newDialog.pointTypeWidget.show()
        else:
            self.newDialog.pointTypeWidget.hide()
            self.newDialog.wktTypeWidget.show()
    
    def showManualGeometryTypeWidget(self):
        self.newDialog.manualGeometryWidget.show()
    
    def hideManualGeometryTypeWidget(self):
        self.newDialog.manualGeometryWidget.hide()               
         
