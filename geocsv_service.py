'''
Created on 04.05.2015

@author: faustos
'''
import csv
import os

from qgis.core import QgsVectorLayer, QgsFeature
from geocsv_model import *
from geocsv_exception import *

class CsvExcelSemicolonDialect(csv.excel):
    delimiter = ';'

class GeoCsvDataSourceHandler:
    
    def __init__(self, pathToCsvFile):
        csv.register_dialect('excel-semicolon', CsvExcelSemicolonDialect)
        try:
            self._fileContainer = GeoCsvFileContainer(pathToCsvFile)
            self._csvHasHeader = True
            self._csvDialect = 'excel-semicolon'
            self._csvtDialect = 'excel-semicolon'
            self._prjDialect = 'excel-semicolon'             
        except:
            raise InvalidDataSourceException()
        self._examineDataSource()
        
    def _examineDataSource(self):
        try :
            with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:
                self._csvHasHeader = csv.Sniffer().has_header(csvfile.read(4096))                        
        except:
            raise
                
    def hasCsvt(self):
        return self._fileContainer.hasCsvt()
    
    def getPathToCsvFile(self):
        return self._fileContainer.pathToCsvFile
        
    def createCsvVectorDescriptor(self):                 
        if not self.hasCsvt():
            raise MissingCsvtException()                          
        attributes = []
        try:
            attributes = self._extractGeoCsvAttributesFromCsvt()
        except GeoCsvUnknownAttributeException:
            raise
        except:
            raise FileIOException()                                                    
        try:                 
            attributeNames = self.extractAttributeNamesFromCsv()
        except:
            raise FileIOException()
                  
        if len(attributes) != len(attributeNames):
            raise CsvCsvtMissmatchException()
        
        for i, attribute in enumerate(attributes):
            attribute.name = attributeNames[i]
        
        descriptor = None            
        try:            
            descriptor = self.getDescriptorFromAttributesList(attributes)
            if descriptor and descriptor.descriptorType == CsvVectorLayerDescriptor.wktDescriptorType:
                firstRow = self.getSampleRowsFromCSV(1)
                if len(firstRow) == 0:
                    raise GeoCsvUnknownGeometryTypeException()                                    
                descriptor.determineWktGeometryTypeFromRow(firstRow[0])
            descriptor.layerName = self._fileContainer.fileName
        except GeoCsvMultipleGeoAttributeException:
            raise
        except GeoCsvMalformedGeoAttributeException:
            raise
        
        return descriptor
            
            
    def createFeaturesFromCsv(self, vectorLayerDescriptor):
        ':type vectorLayerDescriptor:CsvVectorLayerDescriptor'
        features = []
        with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:
                reader = csv.reader(csvfile, dialect=self._csvDialect)
                if self._csvHasHeader:
                    reader.next()                 
                for row in reader:
                    feature = QgsFeature()
                    geometry = vectorLayerDescriptor.getGeometryFromRow(row)
                    if geometry:
                        feature.setGeometry(geometry)
                        feature.setAttributes(row)
                        features.append(feature)
        return features
              
    def _extractGeoCsvAttributesFromCsvt(self):
        if not self.hasCsvt():
            raise MissingCsvtException()     
        attributes = []
        try:
            with open(self._fileContainer.pathToCsvtFile, 'rb') as csvfile:
                reader = csv.reader(csvfile, dialect=self._csvtDialect)                                
                typeRow = reader.next()
                for i, attributeType in enumerate(typeRow):
                    # ToDo extract precision and length information
                    if not attributeType.lower() in GeoCsvAttributeType.__dict__.values():
                        raise GeoCsvUnknownAttributeException(attributeType, i)  
                    attributes.append(GeoCSVAttribute(attributeType.lower()))  
        except:
            raise
        return attributes
        
    def extractAttributeNamesFromCsv(self):
        attributeNames = []
        try :
            with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:               
                reader = csv.reader(csvfile, dialect=self._csvDialect)
                firstRow = reader.next()
                for i, val in enumerate(firstRow):
                    if self._csvHasHeader:
                        attributeNames.append(val)
                    else:
                        attributeNames.append('field' + (i + 1))
        except:
            raise
        return attributeNames
        
    def getDescriptorFromAttributesList(self, attributes): 
        
        descriptor = None
        
        eastings = [i for i, v in enumerate(attributes) if v.type == GeoCsvAttributeType.easting]
        northings = [i for i, v in enumerate(attributes) if v.type == GeoCsvAttributeType.northing]
        wkts = [i for i, v in enumerate(attributes) if v.type == GeoCsvAttributeType.wkt]
                               
        if len(eastings) > 1 or len(northings) > 1 or len(wkts) > 1:
            raise GeoCsvMultipleGeoAttributeException()
        if (len(eastings) == 1 and len(northings) == 0) or (len(eastings) == 0 and len(northings) == 1):
            raise GeoCsvMalformedGeoAttributeException()
        
        if len(eastings) == 1 and len(northings) == 1:
            descriptor = PointCsvVectorLayerDescriptor(attributes, eastings[0], northings[0])
        elif len(wkts) == 1:
            descriptor = WktCsvVectorLayerDescriptor(attributes, wkts[0])
        
        return descriptor
        
    def getSampleRowsFromCSV(self, maxRows=3):
        try :
            with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:
                reader = csv.reader(csvfile, dialect=self._csvDialect)
                if self._csvHasHeader:
                    reader.next()                    
                rowCounter = 0   
                rows = [] 
                row = reader.next()                
                while row and rowCounter < maxRows:
                    rows.append(row)
                    rowCounter += 1
                    row = reader.next()
                return rows
        except:
            raise
            
        
    def syncFeaturesWithCsv(self, vectorLayerDescriptor, features):
        ':type vectorLayerDescriptor:CsvVectorLayerDescriptor'
        try:
            with open(self._fileContainer.pathToCsvFile, 'w') as csvfile:
                writer = csv.writer(csvfile, dialect=self._csvDialect)
                attributeNames = [attribute.name for attribute in vectorLayerDescriptor.attributes]
                # write header row
                writer.writerow(attributeNames)
                for feature in features:
                    row = []
                    for attribute in attributeNames:
                        row.append(feature[feature.fieldNameIndex(attribute)])
                    writer.writerow([unicode(s).encode("utf-8") for s in row])                
        except:
            raise       
                                            
    def guessTypesFromFirstRow(self, row):
        pass   
    

class GeoCsvFileContainer:
            
    def __init__(self, pathToCsvFile):
        if not os.path.isfile(pathToCsvFile):
            raise FileNotFoundException()
        self.rootPath, fileExtension = os.path.splitext(pathToCsvFile)
        if fileExtension == '.csv':
            self.pathToCsvFile = pathToCsvFile
            self._createPathToCSVT()
            self._createPathToPRJ()
            self._createFileName()
        elif fileExtension == '.csvz':
            pass
        else:
            raise UnknownFileFormatException()
    
    def hasCsvt(self):
        return self.pathToCsvtFile != ''
    
    def hasPrj(self):
        return self.pathToPrj != ''
    
    def _createPathToCSVT(self):
        self.pathToCsvtFile = ""
        if os.path.exists(self.rootPath + '.csvt'):
            self.pathToCsvtFile = self.rootPath + '.csvt'
    
    def _createPathToPRJ(self):
        self.pathToPrj = ""
        if os.path.exists(self.rootPath + '.prj'):
            self.pathToPrj = self.rootPath + '.prj'    
            
    def _createFileName(self): 
        self.fileName = os.path.basename(self.rootPath)  

class GeoCsvVectorLayerFactory:
     
    @staticmethod
    def createVectorLayer(dataSourceHandler, vectorLayerDescriptor=None):                
        ':type dataSourceHandler:GeoCsvDataSourceHandler'
        ':type vectorLayerDescriptor: CsvVectorLayerDescriptor'
        if not vectorLayerDescriptor:
            try:
                vectorLayerDescriptor = dataSourceHandler.createCsvVectorDescriptor()
            except:
                raise                
        # create VectorLayer using memory provider
        vectorLayer = QgsVectorLayer(vectorLayerDescriptor.geometryType, vectorLayerDescriptor.layerName, "memory")
        # : :type dataProvider: QgsVectorDataProvider
        dataProvider = vectorLayer.dataProvider() 
        dataProvider.addAttributes(vectorLayerDescriptor.getAttributesAsQgsFields())
        vectorLayer.updateFields()
        dataProvider.addFeatures(dataSourceHandler.createFeaturesFromCsv(vectorLayerDescriptor))                
        vectorLayer.updateExtents()
        vectorLayer.setCustomProperty("csv_filepath", dataSourceHandler.getPathToCsvFile())
        return CsvVectorLayer(dataSourceHandler, vectorLayer, vectorLayerDescriptor)        
        
