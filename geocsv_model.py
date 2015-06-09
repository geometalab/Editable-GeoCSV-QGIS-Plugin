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

from geocsv_exception import GeoCsvUnknownGeometryTypeException,GeoCsvUnknownAttributeException, GeoCsvMalformedGeoAttributeException
from PyQt4.Qt import QMetaType, QMessageBox, QApplication

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
    dateTime = "dateTime"
    easting = "easting"
    northing = "northing"
    wkt = "wkt"
    
    #aliases
    attributeTypes = {
        integer:["Integer"],
        real: ["Real"],
        string:["String"],
        date: ["Date"],
        time: ["Time"],
        dateTime: ["DateTime"],        
        easting: ["CoordX","Easting","Point"],        
        northing: ["CoordY","Northing","Point"],
        wkt: ["WKT"]            
    }
                            
    def __init__(self, attributeType, length=0, precision=0):
        _attributeType = None
        for keyType, valueList in self.attributeTypes.iteritems():
            if attributeType.lower() in [s.lower() for s in valueList]:
                _attributeType = keyType
        if not _attributeType:
            raise GeoCsvUnknownAttributeException(attributeType)  
        self.attributeType = _attributeType
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
                    raise GeoCsvMalformedGeoAttributeException()                                                        
                attributeType = csvtString[0:openBracketIndex]
                additionalInfo = csvtString[openBracketIndex+1:closingBracketIndex]                
                splittedAddionalInfo = additionalInfo.split('.')
                try:
                    if splittedAddionalInfo[0]:
                        if attributeType.lower() == "point":
                            if splittedAddionalInfo[0].lower() == "x":
                                attributeType = 'coordx'
                            elif splittedAddionalInfo[0].lower() == "y":
                                attributeType = 'coordy'
                            else:
                                raise GeoCsvUnknownAttributeException()                                
                        else:
                            length = int(splittedAddionalInfo[0])
                    if len(splittedAddionalInfo) == 2:
                        precision = int(splittedAddionalInfo[1])
                except ValueError:
                    #if it cant't be parsed into an int, it is probably another csvt subtype. 
                    pass
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
        return GeoCsvAttributeType.attributeTypes[self.attributeType][0] + additionalInfo        
                            
class GeoCSVAttribute:
    def __init__(self, attributeType, attributeName):        
        self.name = attributeName        
        self.type = attributeType
        
    @staticmethod
    def createFromQgsField(qgsField):
        ':type qgsField:QgsField'
        attributeType = None
        if qgsField.type() == QMetaType.Int:
            attributeType = GeoCsvAttributeType.integer
        elif qgsField.type() == QMetaType.Double:
            attributeType = GeoCsvAttributeType.real
        else:
            attributeType = GeoCsvAttributeType.string
        geoCsvAttributeType = GeoCsvAttributeType(attributeType, qgsField.length(), qgsField.precision())        
        return GeoCSVAttribute(geoCsvAttributeType, qgsField.name())
        
            
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
    
    #ToDo Typo
    def indexIsGeometryIndex(self, attributeIndex):
        raise NotImplementedError("must be implemented")
    
    def getAttributeTypes(self):
        attributeTypes = []
        for attribute in self.attributes:
            if attribute is not None:
                attributeTypes.append(attribute.type)
        return attributeTypes
    
    def getAttributesAsQgsFields(self):
        fields = []
        # : :type attribute: GeoCSVAttribute
        for attribute in self.attributes: 
            if attribute is not None:           
                fields.append(attribute.createQgsField())
        return fields
    
    def addAttribute(self, geoCsvAttribute):
        # : :type geoCsvAttribute: GeoCSVAttribute
        self.attributes.append(geoCsvAttribute)
        
    def deleteAttributeAtIndex(self, index):                
        try:
            if not self.indexIsGeometryIndex(index):
                self.attributes[index] = None
        except:
            raise
        
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
    
    def indexIsGeometryIndex(self, attributeIndex):
        return (attributeIndex == self.wktIndex)
             
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
        
    def indexIsGeometryIndex(self, attributeIndex):
        return (attributeIndex == self.eastingIndex or attributeIndex == self.northingIndex)
        

class CsvVectorLayer():    
    def __init__(self, qgsVectorLayer, vectorLayerDescriptor):           
        ':type qgsVectorLayer: QgsVectorLayer'
        ':type vectorLayerDescriptor CsvVectorLayerDescriptor'        
        self._initConnections(qgsVectorLayer)                
        self.qgsVectorLayer = qgsVectorLayer        
        self.vectorLayerDescriptor = vectorLayerDescriptor         
        self.dirty = False
        
    def initController(self, vectorLayerController):
        ':type vectorLayerController VectorLayerController'
        self.vectorLayerController = vectorLayerController
                                  
    def _initConnections(self, qgsVectorLayer):
        ':type qgsVectorLayer: QgsVectorLayer'        
        qgsVectorLayer.editingStarted.connect(self.editingDidStart)
        qgsVectorLayer.editingStopped.connect(self.editingDidStop) 
        qgsVectorLayer.featureAdded.connect(self.featureAdded)               
        qgsVectorLayer.committedFeaturesRemoved.connect(self.featuresRemoved)
        qgsVectorLayer.geometryChanged.connect(self.geometryChanged)
        qgsVectorLayer.layerCrsChanged.connect(self.layerCrsDidChange)
        qgsVectorLayer.attributeDeleted.connect(self.checkAttributeDeleted)
        qgsVectorLayer.committedAttributesAdded.connect(self.attributesAdded)
        qgsVectorLayer.committedAttributesDeleted.connect(self.attributesDeleted)
        qgsVectorLayer.committedAttributeValuesChanges.connect(self.attributesValueChanged)
        qgsVectorLayer.screenUpdateRequested.connect(self.reloadFromDataSource)
        
    def editingDidStart(self):
        self.qgsVectorLayer.editBuffer().committedAttributesAdded.connect(self.attributesAdded)
        self.qgsVectorLayer.editBuffer().committedAttributesDeleted.connect(self.attributesDeleted)
        self.qgsVectorLayer.editBuffer().committedAttributeValuesChanges.connect(self.attributesValueChanged)
    
    def editingDidStop(self):
        if self.dirty:
            features = self.qgsVectorLayer.getFeatures()
            if self.vectorLayerController.syncFeatures(features, self.vectorLayerDescriptor):
                self.dirty = False
                                
    def featureAdded(self, featureId):
        self.geometryChanged(featureId, None)      
    
    def featuresRemoved(self, layer, featureIds):
        self.dirty = True
        
    def attributesValueChanged(self, layerId, changedValues):
        self.dirty = True
        
    def attributesAdded(self, layerId, attributes):
        self.vectorLayerController.addAttributes(attributes, self.vectorLayerDescriptor)
        self.dirty = True
        
    def attributesDeleted(self, layerId, attributeIds):
        self.vectorLayerController.deleteAttributes(attributeIds, self.vectorLayerDescriptor) 
        self.dirty = True
        
    def reloadFromDataSource(self):
        self.qgsVectorLayer.reload()
        test = ""
            
    def checkAttributeDeleted(self, attributeId):
        if not self.vectorLayerController.checkDeleteAttribute(attributeId, self.vectorLayerDescriptor):
            pass
#             self.qgsVectorLayer.rollBack()
                            
    def geometryChanged(self, featureId, geometry):
        feature = self.qgsVectorLayer.getFeatures(QgsFeatureRequest(featureId)).next()
        self.vectorLayerDescriptor.updateGeoAttributes(self.qgsVectorLayer, feature)
        self.dirty = True
    
    def layerCrsDidChange(self):
        self.vectorLayerController.updateLayerCrs(self.qgsVectorLayer.crs().toWkt())
        
    def updateGeoCsvPath(self, path):
        self.qgsVectorLayer.setDataUrl(path)        
        self.qgsVectorLayer.setCustomProperty("editablegeocsv_path", path)
        
    def getGeoCsvPath(self):
        return self.qgsVectorLayer.customProperty('editablegeocsv_path')
