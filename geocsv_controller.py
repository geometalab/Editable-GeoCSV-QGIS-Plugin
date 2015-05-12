'''
Created on 05.05.2015

@author: faustos
'''
import weakref


from qgis.core import QgsMapLayerRegistry


from PyQt4.QtGui import QFileDialog

from geocsv_ui import GeoCsvDialogNew
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
        
    def createCsvVectorLayer(self, vectorLayers):  
        self.dataSourceHandler = None
        self.vectorDescriptor = None
        self.newDialog = GeoCsvDialogNew()        
        self.initConnections()
        self.initVisibility()                      
        self.newDialog.show()
        result = self.newDialog.exec_()
        if result:
            if self.dataSourceHandler and self.vectorDescriptor:                                
                csvVectorLayer = GeoCsvVectorLayerFactory.createVectorLayer(self.dataSourceHandler, self.vectorDescriptor)                                            
                QgsMapLayerRegistry.instance().addMapLayer(csvVectorLayer.vectorLayer)                
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
            self.newDialog.filePathErrorLabel.setText("unknown csvt attribute {} at index {}".format(e.attributeName, e.attributeIndex))            
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
                    self.newDialog.eastingAttributeDropDown.setCurrentIndex(self.vectorDescriptor.eastingIndex+1)
                    self.newDialog.northingAttributeDropDown.setCurrentIndex(self.vectorDescriptor.northingIndex+1)
                else:
                    self.newDialog.wktGeometryTypeRadio.setChecked(True)
                    self.newDialog.wktAttributeDropDown.setCurrentIndex(self.vectorDescriptor.wktIndex+1)
            self.geometryFieldUpdate = False
                   
    def _manualGeometryDropdownChanged(self, index):
        if not self.geometryFieldUpdate and not index == 0:
            self.vectorDescriptor = None
            self.newDialog.filePathErrorLabel.setText("")
            if self.newDialog.pointGeometryTypeRadio.isChecked():
                if not self.newDialog.eastingAttributeDropDown.currentIndex() == 0 and not self.newDialog.northingAttributeDropDown.currentIndex() == 0:
                    try:
                        self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvPointVectorDescriptor(self.newDialog.eastingAttributeDropDown.currentIndex()-1, self.newDialog.northingAttributeDropDown.currentIndex()-1)
                    except:
                        self.newDialog.filePathErrorLabel.setText("error in geometry selection")                             
            else:
                try:
                    self.vectorDescriptor = self.dataSourceHandler.manuallyCreateCsvWktVectorDescriptor(self.newDialog.wktAttributeDropDown.currentIndex()-1)
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

        
class VectorLayerController:
    
    def __init__(self, csvVectorLayer, csvDataSourceHandler):        
        self.csvVectorLayer = weakref.ref(csvVectorLayer)
        self.csvDataSourceHandler = csvDataSourceHandler
            
    def syncFeatures(self, features, vectorLayerDescriptor):
        try:
            self.csvDataSourceHandler.syncFeaturesWithCsv(vectorLayerDescriptor, features)
            return True
        except:
            #ToDo Changes couldn't be saved
            return False