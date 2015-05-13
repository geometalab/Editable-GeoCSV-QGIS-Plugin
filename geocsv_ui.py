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

import os

from PyQt4 import QtGui, uic
from PyQt4.QtCore import QCoreApplication

FORM_CLASS_NEW, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geocsv_dialog_new.ui'))

FORM_CLASS_CONFLICT, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'geocsv_dialog_conflict.ui'))


class GeoCsvDialogNew(QtGui.QDialog, FORM_CLASS_NEW):
    def __init__(self, parent=None):        
        super(GeoCsvDialogNew, self).__init__(parent)        
        self.setupUi(self)
        
class GeoCsvDialogConflict(QtGui.QDialog, FORM_CLASS_CONFLICT):
    def __init__(self, parent=None):        
        super(GeoCsvDialogConflict, self).__init__(parent)        
        self.setupUi(self)  
        
class QtHelper:
    @staticmethod        
    def translate(message):
        return QCoreApplication.translate('geocsveditor', message)             
