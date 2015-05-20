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

class InvalidDelimiterException(Exception):
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