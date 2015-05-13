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

from qgis.core import QgsField, QgsGeometry, QgsPoint, QgsFeatureRequest
from PyQt4.QtCore import QVariant

from geocsv_exception import GeoCsvUnknownGeometryTypeException,GeoCsvUnknownAttributeException

class GeometryType:
    # Currently, QGis can only determine Point, LineString and Polygon geometry types
    # http://qgis.org/api/group__core.html#ga09947eb19394302eeeed44d3e81dd74b
    point = "Point"
    lineString = "LineString"
    polygon = "Polygon"    
#     multiPoint = "MultiPoint"
#     multiLineString = "MultiLineString"
#     multiPolygon = "MultiPolygon"
    
    # http://qgis.org/api/group__core.html#ga09947eb19394302eeeed44d3e81dd74b
    # Qgis::GeoemtryType    
    convertFromQgisGeometryType = {0:point, 1:lineString, 2:polygon}
    
class GeoCsvAttributeType:        
    integer = "integer"
    real = "real"
    string = "string"
    date = "date"
    time = "time"
    dateTime = "datetime"
    easting = "easting"
    northing = "northing"
    wkt = "wkt"
    
    def __init__(self, attributeType, length=0, precision=0):
        if not attributeType.lower() in GeoCsvAttributeType.__dict__.values():
            raise GeoCsvUnknownAttributeException(attributeType)  
        self.attributeType = attributeType
        self.length = length
        self.precision = precision
    
    @staticmethod    
    def fromCsvtString(csvtString):
        try:
            csvtString = csvtString.lower()
            openBracketIndex = csvtString.find('(')
            attributeType = None                        
            length = 0
            precision = 0                        
            if not openBracketIndex == -1:
                closingBracketIndex = csvtString.find(')')
                if closingBracketIndex == -1:
                    raise GeoCsvUnknownAttributeException                                                        
                attributeType = csvtString[0:openBracketIndex]
                additionalInfo = csvtString[openBracketIndex+1:closingBracketIndex]
                splittedAddionalInfo = additionalInfo.split('.')
                try:
                    if splittedAddionalInfo[0]:
                        length = int(splittedAddionalInfo[0])
                    if len(splittedAddionalInfo) == 2:
                        precision = int(splittedAddionalInfo[1])
                except ValueError:
                    raise GeoCsvUnknownAttributeException
            else:
                attributeType = csvtString 
            return GeoCsvAttributeType(attributeType, length, precision)
        except GeoCsvUnknownAttributeException:
            raise     
        
    def toCsvtString(self):
        additionalInfo = ''
        if not self.length == 0:
            additionalInfo = str(self.length)
        if not self.precision == 0:
            if additionalInfo:
                additionalInfo += '.'
            additionalInfo += str(self.precision)
        if additionalInfo:
            additionalInfo = '('+additionalInfo+')'
        return self.attributeType.capitalize() + additionalInfo        
                            
class GeoCSVAttribute:
    def __init__(self, attributeType, attributeName):        
        self.name = attributeName        
        self.type = attributeType
        
    def createQgsField(self):
        qgsField = None
        if self.type.attributeType == GeoCsvAttributeType.integer:
            qgsField = QgsField(self.name, QVariant.Int)
        elif self.type.attributeType == GeoCsvAttributeType.easting or self.type.attributeType == GeoCsvAttributeType.northing or self.type.attributeType == GeoCsvAttributeType.real:
            qgsField = QgsField(self.name, QVariant.Double)
        else:
            qgsField = QgsField(self.name, QVariant.String)
        if not self.type.length == 0:
            qgsField.setLength(self.type.length)
        if not self.type.precision == 0:
            qgsField.setPrecision(self.type.precision) 
        return qgsField     
            
class CsvVectorLayerDescriptor:
    
    pointDescriptorType = "pointdescriptor"
    wktDescriptorType = "wktdescriptor"
    
    def __init__(self, attributes):
        self.attributes = attributes
        self.geometryType = None
        self.descriptorType = None
        self.layerName = None
        self.fileContainer = None
        self.crs = None 
        
    def addCRS(self, crs):
        self.crs = crs
     
    def updateGeoAttributes(self, vectorLayer, feature):
        raise NotImplementedError("must be implemented")
    
    def getGeometryFromRow(self, row):
        raise NotImplementedError("must be implemented")

    def configureAndValidateWithSampleRow(self, row):
        raise NotImplementedError("must be implemented")
    
    def getAttributesAsQgsFields(self):
        fields = []
        # : :type attribute: GeoCSVAttribute
        for attribute in self.attributes:            
            fields.append(attribute.createQgsField())
        return fields
            
    def changeAttributeValue(self, vectorLayer, feature, attributeName, newValue):
        ':type qgsVectorLayer: QgsVectorLayer'
        ':type feature: QgsFeature'
        vectorLayer.changeAttributeValue(feature.id(), feature.fieldNameIndex(attributeName), newValue)
        
                
class WktCsvVectorLayerDescriptor(CsvVectorLayerDescriptor):
        
    def __init__(self, attributes, wktIndex):
        CsvVectorLayerDescriptor.__init__(self, attributes)
        self.descriptorType = CsvVectorLayerDescriptor.wktDescriptorType
        self.wktIndex = wktIndex        
    
    def configureAndValidateWithSampleRow(self, row):
        self.determineWktGeometryTypeFromRow(row)
    
    
    def determineWktGeometryTypeFromRow(self, row):
        wkt = row[self.wktIndex]
        qgsGeometry = QgsGeometry.fromWkt(wkt)  # : :type qgsGeometry: QgsGeometry
        qgsGeometryType = qgsGeometry.type()
        if qgsGeometryType in GeometryType.convertFromQgisGeometryType:
            self.geometryType = GeometryType.convertFromQgisGeometryType[qgsGeometryType]
        else:
            raise GeoCsvUnknownGeometryTypeException()
        
    def getGeometryFromRow(self, row):
        return QgsGeometry.fromWkt(row[self.wktIndex])
             
    def updateGeoAttributes(self, vectorLayer, feature):
        ':type qgsVectorLayer: QgsVectorLayer'
        ':type feature: QgsFeature'        
        self.changeAttributeValue(vectorLayer, feature, self.attributes[self.wktIndex].name, feature.geometry().exportToWkt())
        
class PointCsvVectorLayerDescriptor(CsvVectorLayerDescriptor):
    def __init__(self, attributes, eastingIndex, northingIndex):
        CsvVectorLayerDescriptor.__init__(self, attributes)
        self.descriptorType = CsvVectorLayerDescriptor.pointDescriptorType
        self.eastingIndex = eastingIndex
        self.northingIndex = northingIndex
        self.geometryType = GeometryType.point
    
    def getGeometryFromRow(self, row):
        geometry = None
        try:
            geometry = QgsGeometry.fromPoint(QgsPoint(float(row[self.eastingIndex]), float(row[self.northingIndex])))
        except:
            pass        
        return geometry
        
    def updateGeoAttributes(self, vectorLayer, feature):
        ':type qgsVectorLayer: QgsVectorLayer'
        ':type feature: QgsFeature'
        point = feature.geometry().asPoint()
        self.changeAttributeValue(vectorLayer, feature, self.attributes[self.eastingIndex].name, point.x())
        self.changeAttributeValue(vectorLayer, feature, self.attributes[self.northingIndex].name, point.y())
        
    def configureAndValidateWithSampleRow(self, row):
        try:
            float(row[self.eastingIndex])
            float(row[self.northingIndex])            
        except ValueError:
            raise GeoCsvUnknownGeometryTypeException()
        

class CsvVectorLayer():    
    def __init__(self, qgsVectorLayer, vectorLayerDescriptor):           
        ':type qgsVectorLayer: QgsVectorLayer'
        ':type vectorLayerDescriptor CsvVectorLayerDescriptor'        
        self.initConnections(qgsVectorLayer)                
        self.qgsVectorLayer = qgsVectorLayer        
        self.vectorLayerDescriptor = vectorLayerDescriptor         
        self.dirty = False
        
    def initController(self, vectorLayerController):
        ':type vectorLayerController VectorLayerController'
        self.vectorLayerController = vectorLayerController
                                  
    def initConnections(self, qgsVectorLayer):
        ':type qgsVectorLayer: QgsVectorLayer'        
        qgsVectorLayer.editingStarted.connect(self.editingDidStart)
        qgsVectorLayer.editingStopped.connect(self.editingDidStop)        
        qgsVectorLayer.committedFeaturesAdded.connect(self.featuresAdded)
        qgsVectorLayer.committedFeaturesRemoved.connect(self.featuresRemoved)
        qgsVectorLayer.geometryChanged.connect(self.geometryChanged)
        qgsVectorLayer.layerCrsChanged.connect(self.layerCrsDidChange)
        
        
    def editingDidStart(self):
        pass
    
    def editingDidStop(self):
        if self.dirty:
            features = self.qgsVectorLayer.getFeatures()
            if self.vectorLayerController.syncFeatures(features, self.vectorLayerDescriptor):
                self.dirty = False
                        
    def featuresAdded(self, layer, features):
        for feature in features:
            self.geometryChanged(feature.id(), feature.geometry())        
    
    def featuresRemoved(self, layer, featureIds):
        self.dirty = True
    
    def geometryChanged(self, featureId, geometry):
        feature = self.qgsVectorLayer.getFeatures(QgsFeatureRequest(featureId)).next()
        self.vectorLayerDescriptor.updateGeoAttributes(self.qgsVectorLayer, feature)
        self.dirty = True
    
    def layerCrsDidChange(self):
        self.vectorLayerController.updateLayerCrs(self.qgsVectorLayer.crs().toWkt())
