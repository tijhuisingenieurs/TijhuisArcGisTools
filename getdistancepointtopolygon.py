import logging
import os.path
import sys
from collections import OrderedDict

import arcpy

from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))
from gistools.tools.validatie import get_distance_point_to_contour
from gistools.utils.collection import MemCollection

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: puntenbestand
# 1: vlakkenbestand
# 2: Doelbestand voor punten me afstanden
# 3: identificatieveld polygons

input_points = arcpy.GetParameterAsText(0)
input_poly = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
poly_id_field = arcpy.GetParameterAsText(3)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
# 
# input_poly = os.path.join(os.path.dirname(__file__),'test', 'data', 'Vlakken_afstand_test.shp')
# input_points = os.path.join(os.path.dirname(__file__),'test', 'data', 'Punten_afstand_test.shp')
# selectie = 'FALSE'
# 
# poly_id_field = 'vlak'
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#    
#     
# output_file =  os.path.join(test_dir, 'test_afstand.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Puntenbestand = ' + input_points)
arcpy.AddMessage('Vlakkenbestand = ' + input_poly)
arcpy.AddMessage('Identificatieveld vlakken = ' + str(poly_id_field))
arcpy.AddMessage('Bestandsnaam voor output = ' + str(output_file))

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

collection1 = MemCollection(geometry_type='MultiPoint')
records1 = []
rows1 = arcpy.SearchCursor(input_points)
fields1 = arcpy.ListFields(input_points)
point = arcpy.Point()

# vullen collections
for row in rows1:
    geom = row.getValue('SHAPE')
    properties1 = OrderedDict()
    for field in fields1:
        if field.name.lower() != 'shape':
            properties1[field.name] = row.getValue(field.name)

    records1.append({'geometry': {'type': 'Point',
                                  'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                     'properties': properties1})

collection1.writerecords(records1)

collection2 = MemCollection(geometry_type='MultiLineString')
records2 = []
rows2 = arcpy.SearchCursor(input_poly)
fields2 = arcpy.ListFields(input_poly)

for row in rows2:
    geom = row.getValue('SHAPE')
    properties2 = OrderedDict()
    for field in fields2:
        if field.name.lower() != 'shape':
            properties2[field.name] = row.getValue(field.name)
    coordinates = []
    for part in geom:
        for p in part:
            if p:
                point = (p.X, p.Y)        
                coordinates.append(point)
            else:
                arcpy.AddMessage('interior found')

    arcpy.AddMessage('OBJECTID = ' + str(properties2[poly_id_field]))
    arcpy.AddMessage('Coordinaten zijn: ' + str(coordinates))

    records2.append({'geometry': {'type': 'LineString',
                                  'coordinates': coordinates},
                     'properties': properties2})
    arcpy.AddMessage('record bevat nu: ' + str(records2[:1]))

collection2.writerecords(records2)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_distance_point_to_contour...')

point_col = get_distance_point_to_contour(collection2, collection1,
                                          poly_id_field)

# wegschrijven tool resultaat
spatial_reference = arcpy.Describe(input_points).spatialReference

arcpy.AddMessage('Bezig met het genereren van het doelbestand met afstanden...')

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT', 
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl, 'poly_id', 'integer', field_is_nullable=True)
arcpy.AddField_management(output_fl, 'afstand', 'double', field_is_nullable=True)

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point
        
    row.setValue('poly_id', p['properties'].get('poly_id', None))        
    row.setValue('afstand', p['properties'].get('afstand', None))

    dataset.insertRow(row)

add_result_to_display(output_fl, output_name) 

arcpy.AddMessage('Gereed')
