# -*- coding: utf-8 -*-
"""
/***************************************************************************
 geocsveditor
                                 A QGIS plugin
 Editable CSV Vector Layer
                             -------------------
        begin                : 2015-04-29
        copyright            : (C) 2015 by geometalab
        email                : geometalab@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load geocsveditor class from file geocsveditor.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from geocsv_plugin import EditableGeoCsv
    return EditableGeoCsv(iface)
