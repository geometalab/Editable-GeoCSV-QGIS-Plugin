'''
Created on 04.05.2015

@author: faustos
'''
import csv
import os
import shutil

from qgis.core import QgsVectorLayer, QgsFeature, QgsCoordinateReferenceSystem
from geocsv_exception import *
from geocsv_model import CsvVectorLayer, GeoCsvAttributeType, PointCsvVectorLayerDescriptor, WktCsvVectorLayerDescriptor, GeoCSVAttribute
import geocsv_controller

class GeoCsvVectorLayerFactory:
     
    @staticmethod
    def createCsvVectorLayer(dataSourceHandler, vectorLayerDescriptor, qgsVectorLayer=None):                
        ':type dataSourceHandler:GeoCsvDataSourceHandler'
        ':type vectorLayerDescriptor: CsvVectorLayerDescriptor'                     
        if not qgsVectorLayer:
            # create VectorLayer using memory provider
            _path = vectorLayerDescriptor.geometryType
            if vectorLayerDescriptor.crs:
                _path += "?crs="+vectorLayerDescriptor.crs.toWkt()            
            qgsVectorLayer = QgsVectorLayer(_path, vectorLayerDescriptor.layerName, "memory")
        # : :type dataProvider: QgsVectorDataProvider                
        dataProvider = qgsVectorLayer.dataProvider() 
        dataProvider.addAttributes(vectorLayerDescriptor.getAttributesAsQgsFields())        
        qgsVectorLayer.updateFields()
        dataProvider.addFeatures(dataSourceHandler.createFeaturesFromCsv(vectorLayerDescriptor))                
        qgsVectorLayer.updateExtents()
        qgsVectorLayer.setCustomProperty("csv_filepath", dataSourceHandler.getPathToCsvFile())
        csvVectorLayer = CsvVectorLayer(qgsVectorLayer, vectorLayerDescriptor) 
        vectorLayerController = geocsv_controller.VectorLayerController(csvVectorLayer, dataSourceHandler)
        csvVectorLayer.initController(vectorLayerController)        
        return csvVectorLayer 
        

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
        except (FileNotFoundException, UnknownFileFormatException):
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
        
    def createCsvVectorDescriptorFromCsvt(self):                 
        if not self.hasCsvt():
            raise MissingCsvtException()                          
        attributeTypes = None
        try:
            attributeTypes = self._extractGeoCsvAttributeTypesFromCsvt()
        except (GeoCsvUnknownAttributeException, FileIOException):
            raise
        attributes = None            
        try:
            attributes = self._createGeoCSVAttributes(attributeTypes)
        except (CsvCsvtMissmatchException, FileIOException):
            raise                
        descriptor = None
        firstDataRow = None
        try:
            firstRow = self.getSampleRowsFromCSV(1)
            if len(firstRow) == 0:
                raise GeoCsvUnknownGeometryTypeException()
            firstDataRow = firstRow[0]
        except (GeoCsvUnknownGeometryTypeException, FileIOException):
            raise 
        try:
            descriptor = self._createAndConfigureDescriptorFromAttributesList(attributes, firstDataRow)        
        except (GeoCsvMultipleGeoAttributeException,
                GeoCsvMalformedGeoAttributeException,
                GeoCsvUnknownGeometryTypeException,
                FileIOException):
            raise
        return descriptor                                                             
    
    def manuallyCreateCsvPointVectorDescriptor(self, eastingIndex, northingIndex):                                
        firstDataRow = None
        try:
            firstRow = self.getSampleRowsFromCSV(1)
            if len(firstRow) == 0:
                raise GeoCsvUnknownGeometryTypeException()
            firstDataRow = firstRow[0]
        except (GeoCsvUnknownGeometryTypeException, FileIOException):
            raise         
        
        attributeTypes = self._extractGeoCsvAttributeTypesFromFirstDataRow(firstDataRow)
        if not eastingIndex < len(attributeTypes) or not northingIndex < len(attributeTypes):
            raise GeoCsvUnknownGeometryTypeException()                
        attributeTypes[eastingIndex] = GeoCsvAttributeType(GeoCsvAttributeType.easting)
        attributeTypes[northingIndex] = GeoCsvAttributeType(GeoCsvAttributeType.northing)   
        
        attributes = None
        try:
            attributes = self._createGeoCSVAttributes(attributeTypes)
        except CsvCsvtMissmatchException, FileIOException:
            raise
        
        descriptor = None
        try:
            descriptor = self._createAndConfigureDescriptorFromAttributesList(attributes, firstDataRow)        
        except (GeoCsvMultipleGeoAttributeException,
                GeoCsvMalformedGeoAttributeException,
                GeoCsvUnknownGeometryTypeException,
                FileIOException):
            raise
        try:
            self._updateCsvtFile(attributeTypes)
        except FileIOException:
            raise
        return descriptor         
          
    
    def manuallyCreateCsvWktVectorDescriptor(self, wktIndex):
        firstDataRow = None
        try:
            firstRow = self.getSampleRowsFromCSV(1)
            if len(firstRow) == 0:
                raise GeoCsvUnknownGeometryTypeException()
            firstDataRow = firstRow[0]
        except (GeoCsvUnknownGeometryTypeException, FileIOException):
            raise         
        
        attributeTypes = self._extractGeoCsvAttributeTypesFromFirstDataRow(firstDataRow)
        if not wktIndex < len(attributeTypes):
            raise GeoCsvUnknownGeometryTypeException()                
        attributeTypes[wktIndex] = GeoCsvAttributeType(GeoCsvAttributeType.wkt)
        
        attributes = None
        try:
            attributes = self._createGeoCSVAttributes(attributeTypes)
        except CsvCsvtMissmatchException, FileIOException:
            raise
        
        descriptor = None
        try:
            descriptor = self._createAndConfigureDescriptorFromAttributesList(attributes, firstDataRow)        
        except (GeoCsvMultipleGeoAttributeException,
                GeoCsvMalformedGeoAttributeException,
                GeoCsvUnknownGeometryTypeException,
                FileIOException):
            raise
        try:
            self._updateCsvtFile(attributeTypes)
        except FileIOException:
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
    
    def syncFeaturesWithCsv(self, vectorLayerDescriptor, features, alternativeSavePath=None):
        ':type vectorLayerDescriptor:CsvVectorLayerDescriptor'
        try:
            _path = self._fileContainer.pathToCsvFile if not alternativeSavePath else alternativeSavePath
            with open(_path, 'w+') as csvfile:                
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
            raise FileIOException()      
                            
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
            raise FileIOException()
        return attributeNames
        
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
                    try:
                        row = reader.next()
                    except StopIteration:
                        pass
                return rows
        except:                      
            raise FileIOException()


    def updatePrjFile(self, crsWkt):
        with open(self._fileContainer.constructPrjPath(), 'w+') as prjfile:
            prjfile.write(unicode(crsWkt+"\n").encode("utf-8"))
            
    def moveDataSourcesToPath(self, newPath):
        try:
            self._fileContainer.moveToNewPath(newPath)
        except UnknownFileFormatException:
            raise 
                      
    def _extractGeoCsvAttributeTypesFromCsvt(self):
        if not self.hasCsvt():
            raise MissingCsvtException()             
        try:
            attributeTypes = []
            with open(self._fileContainer.pathToCsvtFile, 'rb') as csvfile:
                reader = csv.reader(csvfile, dialect=self._csvtDialect)                                
                typeRow = reader.next()
                for csvtString in typeRow:
                    attributeTypes.append(GeoCsvAttributeType.fromCsvtString(csvtString))
            return attributeTypes      
        except GeoCsvUnknownAttributeException:
            raise        
        except:
            raise FileIOException()
        
    def _extractGeoCsvAttributeTypesFromFirstDataRow(self, row):
        attributeTypes = []
        for value in row:
            attributeType = None
            if value.isdigit():
                attributeType = GeoCsvAttributeType.integer
            else:
                try:
                    float(value)
                    attributeType = GeoCsvAttributeType.real
                except:
                    attributeType = GeoCsvAttributeType.string
            attributeTypes.append(GeoCsvAttributeType(attributeType))                        
        return attributeTypes
    
    def _extractCrsFromPrj(self):
        crs = None
        if self._fileContainer.hasPrj():
            with open(self._fileContainer.pathToPrj) as prjfile:
                crsWkt = prjfile.readline()
                _crs =  QgsCoordinateReferenceSystem()
                if _crs.createFromWkt(crsWkt):
                    crs = _crs
        return crs
        
    
    def _createGeoCSVAttributes(self, attributeTypes):
        attributes = []
        try:                 
            attributeNames = self.extractAttributeNamesFromCsv()
        except:
            raise FileIOException()                  
        if len(attributeTypes) != len(attributeNames):
            raise CsvCsvtMissmatchException()        
        for i, attributeType in enumerate(attributeTypes):
            attributes.append(GeoCSVAttribute(attributeType, attributeNames[i]))            
        return attributes
        
        
    def _createAndConfigureDescriptorFromAttributesList(self, attributes, firstDataRow):
        descriptor = None
        try:
            descriptor = self._getDescriptorFromAttributesList(attributes)                                                                                                                
            descriptor.layerName = self._fileContainer.fileName            
        except (GeoCsvMultipleGeoAttributeException,
                GeoCsvMalformedGeoAttributeException):
            raise                                           
        try:            
            descriptor.configureAndValidateWithSampleRow(firstDataRow)
        except GeoCsvUnknownGeometryTypeException:
            raise
        crs = self._extractCrsFromPrj()        
        if crs:            
            descriptor.addCRS(crs)        
        return descriptor


    def _getDescriptorFromAttributesList(self, attributes): 
        
        descriptor = None
        
        eastings = [i for i, v in enumerate(attributes) if v.type.attributeType == GeoCsvAttributeType.easting]
        northings = [i for i, v in enumerate(attributes) if v.type.attributeType == GeoCsvAttributeType.northing]
        wkts = [i for i, v in enumerate(attributes) if v.type.attributeType == GeoCsvAttributeType.wkt]
                               
        if len(eastings) > 1 or len(northings) > 1 or len(wkts) > 1:
            raise GeoCsvMultipleGeoAttributeException()
        if (len(eastings) == 1 and len(northings) == 0) or (len(eastings) == 0 and len(northings) == 1):
            raise GeoCsvMalformedGeoAttributeException()
        if (len(eastings) == 1 and len(wkts) == 1) or (len(northings) == 1 and len(wkts) == 1):
            raise GeoCsvMultipleGeoAttributeException()        
        if len(eastings) == 1 and len(northings) == 1:
            descriptor = PointCsvVectorLayerDescriptor(attributes, eastings[0], northings[0])
        elif len(wkts) == 1:
            descriptor = WktCsvVectorLayerDescriptor(attributes, wkts[0])
        else:
            raise GeoCsvMalformedGeoAttributeException()
        return descriptor
    
    def _updateCsvtFile(self, attributeTypes):
        try: 
            with open(self._fileContainer.constructCsvtPath(), "w+") as csvtfile:                 
                writer = csv.writer(csvtfile, dialect=self._csvDialect)
                geoCsvAttributeTypes = [attributeType.toCsvtString() for attributeType in attributeTypes]
                writer.writerow([unicode(s).encode("utf-8") for s in geoCsvAttributeTypes])
        except:
            raise FileIOException()         
                                                                 
class GeoCsvFileContainer:
            
    def __init__(self, pathToCsvFile):
        self._initWithPath(pathToCsvFile)
        
    def _initWithPath(self, pathToCsvFile):
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
    
    def constructCsvtPath(self):
        return self.rootPath +'.csvt'
    
    def constructPrjPath(self):
        return self.rootPath +'.prj'
    
    def moveToNewPath(self, newPath):
        newRootPath, newFileExtension = os.path.splitext(newPath)
        if newFileExtension == '.csv':
            shutil.copy(self.pathToCsvFile, newPath)
            if self.hasCsvt():
                shutil.copy(self.pathToCsvtFile, newRootPath+'.csvt')
            if self.hasPrj():
                shutil.copy(self.pathToPrj, newRootPath+'.prj')
            self._initWithPath(newPath)                
        else:
            raise UnknownFileFormatException()
                        
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
        
