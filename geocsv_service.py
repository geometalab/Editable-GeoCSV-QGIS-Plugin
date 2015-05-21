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

import csv
import os
import shutil
import codecs
import cStringIO

from qgis.core import QgsVectorLayer, QgsFeature, QgsCoordinateReferenceSystem
from qgis.gui import QgsMessageBar
from geocsv_exception import *
from geocsv_model import CsvVectorLayer, GeoCsvAttributeType, PointCsvVectorLayerDescriptor, WktCsvVectorLayerDescriptor, GeoCSVAttribute

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
        csvVectorLayer = CsvVectorLayer(qgsVectorLayer, vectorLayerDescriptor)
        csvVectorLayer.updateGeoCsvPath(dataSourceHandler.getPathToCsvFile())                 
        return csvVectorLayer 
        

class CsvExcelSemicolonDialect(csv.excel):
    delimiter = ';'

class GeoCsvDataSourceHandler:    
         
    _csvDefaultEncoding = 'utf-8'  
    
    @staticmethod
    def convertFileToUTF8(pathToFile, sourceEncoding):
        csv.register_dialect('excel-semicolon', CsvExcelSemicolonDialect)
        with open(pathToFile, 'r+') as csvfile:
            queue = cStringIO.StringIO()
            reader = UnicodeReader(csvfile, dialect='excel-semicolon', encoding=sourceEncoding)
            queueWriter = UnicodeWriter(queue, dialect='excel-semicolon') 
            for row in reader:
                queueWriter.writerow(row)
            csvfile.seek(0)    
            csvfile.write(queue.getvalue())
            csvfile.truncate() 
      
    @staticmethod      
    def createBackupFile(pathToFile):        
        if os.path.isfile(pathToFile):
            root, ext = os.path.splitext(pathToFile)
            backupPath = root+'_backup'+ext
            shutil.copy(pathToFile, backupPath)
            
                                                                                            
    def __init__(self, pathToCsvFile, csvEncoding=_csvDefaultEncoding):
        csv.register_dialect('excel-semicolon', CsvExcelSemicolonDialect)
        try:
            self._fileContainer = GeoCsvFileContainer(pathToCsvFile)
            self._csvHasHeader = True
            self._csvDialect = 'excel-semicolon'
            self._csvtDialect = 'excel-semicolon'
            self._prjDialect = 'excel-semicolon'            
            self._examineDataSource()                                                                                            
        except (FileNotFoundException, UnknownFileFormatException):
            raise InvalidDataSourceException()
        except (InvalidDelimiterException, UnicodeDecodeError):
            raise        
        
        
    def _examineDataSource(self):
        try :
            with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:
                self._csvHasHeader = csv.Sniffer().has_header(csvfile.read(4096))
                csvfile.seek(0)                
                reader = UnicodeReader(csvfile, dialect=self._csvDialect, encoding=self._csvDefaultEncoding)
                for row in reader:
                    pass                                                
        except UnicodeDecodeError:
            raise
        except:
            raise InvalidDelimiterException()
        
                                
    def hasCsvt(self):
        return self._fileContainer.hasCsvt()
    
    def hasPrj(self):
        return self._fileContainer.hasPrj()
    
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
        return descriptor     
            
    def createFeaturesFromCsv(self, vectorLayerDescriptor):
        ':type vectorLayerDescriptor:CsvVectorLayerDescriptor'
        features = []
        with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:            
                reader = UnicodeReader(csvfile, dialect=self._csvDialect,encoding=self._csvDefaultEncoding)
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
                writer = UnicodeWriter(csvfile, dialect=self._csvDialect)
                attributeNames = [attribute.name for attribute in vectorLayerDescriptor.attributes if attribute is not None]
                # write header row
                writer.writerow(attributeNames)                
                for feature in features:
                    row = []
                    for attribute in attributeNames:                        
                        try:
                            row.append(feature[feature.fieldNameIndex(attribute)])
                        except KeyError:
                            #there is a qgis bug related to improper attribute deleteion
                            raise                                                                        
                    writer.writerow(row)                
        except Exception as e:            
            raise FileIOException()      
                            
    def extractAttributeNamesFromCsv(self):
        attributeNames = []
        try :
            with open(self._fileContainer.pathToCsvFile, 'rb') as csvfile:               
                reader = UnicodeReader(csvfile, dialect=self._csvDialect, encoding=self._csvDefaultEncoding)
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
                reader = UnicodeReader(csvfile, dialect=self._csvDialect, encoding=self._csvDefaultEncoding)
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
            self._fileContainer._createPathToPRJ()
            
    def moveDataSourcesToPath(self, newPath):
        try:
            self._fileContainer.moveToNewPath(newPath)
        except UnknownFileFormatException:
            raise 
        
    def updateCsvtFile(self, attributeTypes):
        try: 
            with open(self._fileContainer.constructCsvtPath(), "w+") as csvtfile:                 
                writer = UnicodeWriter(csvtfile, dialect=self._csvDialect)
                geoCsvAttributeTypes = [attributeType.toCsvtString() for attributeType in attributeTypes]
                writer.writerow([unicode(s).encode("utf-8") for s in geoCsvAttributeTypes])
                self._fileContainer._createPathToCSVT()
        except:
            raise FileIOException() 
                      
    def _extractGeoCsvAttributeTypesFromCsvt(self):
        if not self.hasCsvt():
            raise MissingCsvtException()             
        try:
            attributeTypes = []
            with open(self._fileContainer.pathToCsvtFile, 'rb') as csvfile:
                reader = UnicodeReader(csvfile, dialect=self._csvtDialect)                                
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
    
                                                                      
class GeoCsvFileContainer:
            
    def __init__(self, pathToCsvFile):
        self._initWithPath(pathToCsvFile)
        
    def _initWithPath(self, pathToCsvFile):
        if not os.path.isfile(pathToCsvFile):
            raise FileNotFoundException()
        self.rootPath, fileExtension = os.path.splitext(pathToCsvFile)
        if fileExtension == '.csvz':
            #ToDo
            pass
        else:
            self.pathToCsvFile = pathToCsvFile
            self._createPathToCSVT()
            self._createPathToPRJ()
            self._createFileName()
                    
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
        shutil.copyfile(self.pathToCsvFile, newPath)
        if self.hasCsvt():
            shutil.copyfile(self.pathToCsvtFile, newRootPath+'.csvt')
        if self.hasPrj():
            shutil.copyfile(self.pathToPrj, newRootPath+'.prj')
        self._initWithPath(newPath)                
                                
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
        
class NotificationHandler:
    
    _iface = None
    _duration = 4
    
    @classmethod
    def configureIface(cls, iface):        
        cls._iface = iface
    
    @classmethod    
    def pushError(cls, title, message, duration=None):
        cls._checkConfiguration()        
        cls._pushMessage(title, message, QgsMessageBar.CRITICAL, duration)
        
    @classmethod    
    def pushWarning(cls, title, message, duration=None):
        cls._checkConfiguration()
        cls._pushMessage(title, message, QgsMessageBar.WARNING, duration)
        
    @classmethod  
    def pushSuccess(cls, title, message, duration=None):
        cls._checkConfiguration()
        cls._pushMessage(title, message, QgsMessageBar.SUCCESS, duration)   
    
    @classmethod  
    def pushInfo(cls, title, message, duration=None):
        cls._checkConfiguration()
        cls._pushMessage(title, message, QgsMessageBar.INFO, duration)        
    
    @classmethod  
    def _pushMessage(cls, title, message, messageLevel, duration=None):
        duration = duration if duration is not None else cls._duration
        cls._iface.messageBar().pushMessage(title,message,level=messageLevel, duration=duration)
    
    @classmethod 
    def _checkConfiguration(cls):
        if not cls._iface:
            raise RuntimeError("iface is not configured")
        

class UTF8Recoder:

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):        
        return self.reader.next().encode("utf-8")
                          
class UnicodeReader:

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self._encoding = encoding 
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        try:
            row = self.reader.next()
        except UnicodeDecodeError:
            raise        
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    
    def __init__(self, f, dialect=csv.excel):                
        self.writer = csv.writer(f, dialect=dialect)        

    def writerow(self, row):        
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])        

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)                                        