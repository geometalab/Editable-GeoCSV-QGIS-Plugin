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
        newDialog = GeoCsvDialogNew()        
        self.initConnections(newDialog)
        self.newDialog = newDialog
        self.vectorLayers = vectorLayers
        self.dataSourceHandler = None
        self.vectorDescriptor = None
    
    def initConnections(self, newDialog):
        newDialog.fileBrowserButton.clicked.connect(self.onFileBrowserButton)
        newDialog.filePath.textChanged.connect(self.onFilePathChange)
        newDialog.acceptButton.clicked.connect(newDialog.accept)
        newDialog.rejectButton.clicked.connect(newDialog.reject)
            
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
            except GeoCsvUnknownAttributeException as e:
                self.newDialog.filePathErrorLabel.setText("unknown csvt attribute {} at index {}".format(e.attributeName, e.attributeIndex))
            except CsvCsvtMissmatchException:
                self.newDialog.filePathErrorLabel.setText("csv<->csvt missmatch")
            except:
                self.newDialog.filePathErrorLabel.setText("missing files")
        except:
            self.newDialog.filePathErrorLabel.setText("invalid file path")
         
