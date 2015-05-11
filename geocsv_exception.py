'''
Created on 07.05.2015

@author: faustos
'''


class GeoCsvUnknownAttributeException(Exception):
    def __init__(self, attributeName):
        self.attributeName = attributeName        
        
class GeoCsvMultipleGeoAttributeException(Exception):
    pass

class GeoCsvMalformedGeoAttributeException(Exception):
    pass  

class GeoCsvUnknownGeometryTypeException(Exception):
    pass

class InvalidDataSourceException(Exception):
    pass        

class FileIOException(Exception):
    pass

class CsvCsvtMissmatchException(Exception):
    pass

class FileNotFoundException(Exception):
    pass

class MissingCsvtException(Exception):
    pass

class UnknownFileFormatException(Exception):
    pass