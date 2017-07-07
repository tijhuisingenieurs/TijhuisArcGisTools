import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.wdb_generator import export_points_to_wdb

# Read the parameter values
# 0: shapefile met velddata als punten
# 1: shapefile met lijnen van profielen
# 2: Project
# 3: Doelmap voor wdb betanden
# 4: Afstand tussen profielen

# input_fl_points = arcpy.GetParameterAsText(0)
# input_fl_lines = arcpy.GetParameterAsText(1)
# project = arcpy.GetParameterAsText(2)
# wdb_path = arcpy.GetParameterAsText(3)
# afstand = arcpy.GetParameter(4)

# Testwaarden voor test zonder GUI:
import tempfile
import shutil
 
input_fl_points = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_metingen.shp')
input_fl_lines = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_profielen.shp')

project = 'test wdb'
afstand = 50
wdb_path = os.path.join(tempfile.gettempdir(), 'wdb_test')
if os.path.exists(wdb_path):
    # empty test directory
    shutil.rmtree(wdb_path)
os.mkdir(wdb_path)



# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Shapefile met punten = ' + str(input_fl_points))
arcpy.AddMessage('Shapefile met lijnen = ' + str(input_fl_lines))
arcpy.AddMessage('Project = ' + str(project))
arcpy.AddMessage('Afstand profielen = ' + str(afstand))
arcpy.AddMessage('Doelmap wdb bestanden = ' + str(wdb_path))


# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met lezen van puntdata...')

point_col = MemCollection(geometry_type='MultiPoint')
records = []
rows_point = arcpy.SearchCursor(input_fl_points)
fields_point = arcpy.ListFields(input_fl_points)
point = arcpy.Point()

# vullen collection
for row in rows_point:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()

    for field in fields_point:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                    'properties': properties})

point_col.writerecords(records)


arcpy.AddMessage('Bezig met lezen van lijndata...')

line_col = MemCollection(geometry_type='MultiLineString')
records = []
rows_lines = arcpy.SearchCursor(input_fl_lines)
fields_lines = arcpy.ListFields(input_fl_lines)
point = arcpy.Point()

# vullen collection
for row in rows_lines:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields_lines:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

line_col.writerecords(records)

# Genereren metfile
arcpy.AddMessage('Bezig met genereren van WDB tabellen...')

metfile = export_points_to_wdb(point_col, line_col, wdb_path, afstand, project)

print 'Gereed'
