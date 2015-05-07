'''
Created on 06.05.2015

@author: faustos
'''
import unittest
import os

from geocsv_model import *
from geocsv_service import *

class TestCsvLayer(unittest.TestCase):
    
    pathToTesResources = os.path.dirname(__file__) + "/testresources/" 
    
    def test_GeoCsvContainer(self):
        url = TestCsvLayer.pathToTesResources + "geocsv_sample_point.csv"
        container = GeoCsvFileContainer(url)
        self.assertEqual(TestCsvLayer.pathToTesResources + "geocsv_sample_point.csvt", container.pathToCsvtFile)
          
     
#     def test_CreateVectorDescriptorFromCSVT(self):
#         pathToCsvFile = TestCsvLayer.pathToTesResources + "geocsv_sample_point.csv"
#         dataSourceHandler = GeoCsvDataSourceHandler(pathToCsvFile)
#         descriptor = dataSourceHandler.createCsvVectorDescriptor()
#         self.assertEqual(CsvVectorLayerDescriptor.pointDescriptorType, descriptor.descriptorType)
#         
#     def test_WktTypeRecognition(self):
#         pathToCsvFile = TestCsvLayer.pathToTesResources + "geocsv_sample_wkt.csv"
#         dataSourceHandler = GeoCsvDataSourceHandler(pathToCsvFile)        
#         #: :type descriptor: WktCsvVectorDescriptor
#         descriptor = dataSourceHandler.createCsvVectorDescriptor()
#         self.assertEqual(GeometryType.point, descriptor.geometryType)
        
        

if __name__ == '__main__':
    unittest.main()        
