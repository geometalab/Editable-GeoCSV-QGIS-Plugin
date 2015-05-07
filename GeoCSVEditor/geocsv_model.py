'''
Created on 04.05.2015

@author: faustos
'''

from qgis.core import QgsField, QgsGeometry, QgsPoint, QgsFeatureRequest
from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QFileDialog

from geocsv_exception import GeoCsvUnknownGeometryTypeException

class GeometryType:
    # Qgs memory provider currently only support Point, LineString and Polygon
    # http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/vector.html
    # search for memory provider
    point = "Point"
    lineString = "LineString"
    polygon = "Polygon"    
#     multiPoint = "MultiPoint"
#     multiLineString = "MultiLineString"
#     multiPolygon = "MultiPolygon"
    
    # http://qgis.org/api/group__core.html#ga09947eb19394302eeeed44d3e81dd74b
    # Qgis::GeoemtryType    
    convertFromQgisGemoetryType = {0:point, 1:lineString, 2:polygon}
    
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
            
class GeoCSVAttribute:
    def __init__(self, attributeType, length=0, precision=0, attributeName=''):
        self.name = attributeName
        self.type = attributeType
        self.length = length
        self.precision = precision
        
    def createQgsField(self):
        qgsField = None
        if self.type == GeoCsvAttributeType.integer:
            qgsField = QgsField(self.name, QVariant.Int)
        elif self.type == GeoCsvAttributeType.easting or self.type == GeoCsvAttributeType.northing or self.type == GeoCsvAttributeType.real:
            qgsField = QgsField(self.name, QVariant.Double)
        else:
            qgsField = QgsField(self.name, QVariant.String)
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
     
    def updateGeoAttributes(self, vectorLayer, feature):
        raise NotImplementedError("must be implemented")
    
    def getGeometryFromRow(self, row):
        raise NotImplementedError("must be implemented")
    
    def getAttributesAsQgsFields(self):
        fields = []
        # : :type attribute: GeoCSVAttribute
        for attribute in self.attributes:            
            fields.append(attribute.createQgsField())
        return fields
    
    
        
    def changeAttributeValue(self, vectorLayer, feature, attributeName, newValue):
        ':type vectorLayer: QgsVectorLayer'
        ':type feature: QgsFeature'
        vectorLayer.changeAttributeValue(feature.id(), feature.fieldNameIndex(attributeName), newValue)
                
        
class WktCsvVectorLayerDescriptor(CsvVectorLayerDescriptor):
        
    def __init__(self, attributes, wktIndex):
        CsvVectorLayerDescriptor.__init__(self, attributes)
        self.descriptorType = CsvVectorLayerDescriptor.wktDescriptorType
        self.wktIndex = wktIndex        
    
    def determineWktGeometryTypeFromRow(self, row):
        wkt = row[self.wktIndex]
        qgsGeometry = QgsGeometry.fromWkt(wkt)  # : :type qgsGeometry: QgsGeometry
        qgsGeometryType = qgsGeometry.type()
        if qgsGeometryType in GeometryType.convertFromQgisGemoetryType:
            self.geometryType = GeometryType.convertFromQgisGemoetryType[qgsGeometryType]
        else:
            raise GeoCsvUnknownGeometryTypeException()
        
    def getGeometryFromRow(self, row):
        return QgsGeometry.fromWkt(row[self.wktIndex])
             
    def updateGeoAttributes(self, vectorLayer, feature):
        ':type vectorLayer: QgsVectorLayer'
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
        ':type vectorLayer: QgsVectorLayer'
        ':type feature: QgsFeature'
        point = feature.geometry().asPoint()
        self.changeAttributeValue(vectorLayer, feature, self.attributes[self.eastingIndex].name, point.x())
        self.changeAttributeValue(vectorLayer, feature, self.attributes[self.northingIndex].name, point.y())       
                
class CsvVectorLayer():    
    def __init__(self, dataSourceHandler, vectorLayer, vectorLayerDescriptor):   
        ':type dataSourceHandler: GeoCsvDataSourceHandler'
        ':type vectorLayer: QgsVectorLayer'
        ':type vectorLayerDescriptor CsvVectorLayerDescriptor'
        self.initConnections(vectorLayer)                
        self.vectorLayer = vectorLayer        
        self.vectorLayerDescriptor = vectorLayerDescriptor 
        self.dataSourceHandler = dataSourceHandler 
        self.dirty = False
                                  
    def initConnections(self, vectorLayer):
        ':type vectorLayer: QgsVectorLayer'        
        vectorLayer.editingStarted.connect(self.editingDidStart)
        vectorLayer.editingStopped.connect(self.editingDidStop)
        vectorLayer.committedAttributesAdded.connect(self.attributesAdded)
        vectorLayer.committedAttributesDeleted.connect(self.attributesDeleted)
        vectorLayer.committedAttributeValuesChanges.connect(self.attributesChanged)
        vectorLayer.committedFeaturesAdded.connect(self.featuresAdded)
        vectorLayer.committedFeaturesRemoved.connect(self.featuresRemoved)
        vectorLayer.geometryChanged.connect(self.geometryChanged)
        
        
    def editingDidStart(self):
        self.vectorLayer.editBuffer().committedAttributeValuesChanges.connect(self.attributesChanged)
        self.vectorLayer.editBuffer().committedAttributesAdded.connect(self.attributesAdded)
        self.vectorLayer.editBuffer().committedAttributesDeleted.connect(self.attributesDeleted)
    
    def editingDidStop(self):
        if self.dirty:
            features = self.vectorLayer.getFeatures()
            try:
                self.dataSourceHandler.syncFeaturesWithCsv(self.vectorLayerDescriptor, features)
                self.dirty = False
            except:
                # ToDo Changes couldn't be saved
                raise
    
    def attributesAdded(self, layer, fields):
        # ToDo attrutes added        
        pass   
        
    def attributesDeleted(self, layer, deletedAttributesIds):
        # ToDo attrutes deleted
        pass
    
    def attributesChanged(self, layer, changes):
        # ToDo attrutes changed        
        pass
    
    def featuresAdded(self, layer, features):
        for feature in features:
            self.geometryChanged(feature.id(), feature.geometry())        
    
    def featuresRemoved(self, layer, featureIds):
        self.dirty = True
    
    def geometryChanged(self, featureId, geometry):
        feature = self.vectorLayer.getFeatures(QgsFeatureRequest(featureId)).next()
        self.vectorLayerDescriptor.updateGeoAttributes(self.vectorLayer, feature)
        self.dirty = True
