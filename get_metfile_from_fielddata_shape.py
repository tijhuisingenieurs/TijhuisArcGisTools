import os.path
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.metfile_generator import export_points_to_metfile

# Read the parameter values
# 0: shapefile met velddata als punten
# 1: Project naam
# 2: Doelbestand voor metfile
# 3: Veld voor tekencode
 
input_fl = arcpy.GetParameterAsText(0)
project = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
tekencode = arcpy.GetParameterAsText(3)
type_metfile = arcpy.GetParameterAsText(4)
type_peiling = arcpy.GetParameterAsText(5)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#  
# input_fl = os.path.join(os.path.dirname(__file__), 'test', 'data', 'test_toolc_metingen.shp')
# project = 'test metfile'
# 
# test_dir = os.path.join(tempfile.gettempdir(), 'metfile_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#       
# output_file = os.path.join(test_dir, 'test_metfile.csv')
# tekencode = 'gecombineerde code'


# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Shapefile = ' + str(input_fl))
arcpy.AddMessage('Project = ' + str(project))
arcpy.AddMessage('Doelbestand metfile = ' + str(output_file))
arcpy.AddMessage('Tekencode halen uit = ' + str(tekencode))
arcpy.AddMessage('Opmaaktype metfile = ' + type_metfile)
arcpy.AddMessage('Type peiling = ' + type_peiling)

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met lezen van puntdata...')

point_col = MemCollection(geometry_type='Point')
records = []
rows = arcpy.SearchCursor(input_fl)
fields = arcpy.ListFields(input_fl)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()

    for field in fields:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                    'properties': properties})

point_col.writerecords(records)

# Genereren metfile
arcpy.AddMessage('Bezig met genereren van metfile...')
code = None

if tekencode == 'tekencode':
    code = 1
else:
    code = 2

if type_peiling:
    metfile = export_points_to_metfile(point_col, project, output_file, code, type_metfile, type_peiling)
else:
    metfile = export_points_to_metfile(point_col, project, output_file, code, type_metfile)

arcpy.AddMessage('Gereed')
