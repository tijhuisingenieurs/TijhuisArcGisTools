import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: raster bestand
# 1: punten bestand
# 2: Doelbestand voor punten met raster waarde

input_fl_raster = arcpy.GetParameterAsText(0)
input_fl_points = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)


# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#  
# input_fl_raster = os.path.join(os.path.dirname(__file__), 'test', 'data', 'AHN3_maai_clip.tif')  
# input_fl_points = os.path.join(os.path.dirname(__file__), 'test', 'data', 'Profielpunten_AHN3_offset.shp')
#      
# test_dir = os.path.join(tempfile.gettempdir(), 'ahn_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#       
# output_file = os.path.join(test_dir, 'test_AHN_punten.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Raster bestand = ' + str(input_fl_raster))
arcpy.AddMessage('Punten bestand = ' + str(input_fl_points))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data en uitvoeren get_cell_value...')

collection = MemCollection(geometry_type='MultiPoint')
records = []
rows = arcpy.SearchCursor(input_fl_points)
fields = arcpy.ListFields(input_fl_points)
point = arcpy.Point()

# vullen collections
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.name.lower() not in ['shape', 'id', 'fid']:
            properties[field.name] = row.getValue(field.name)
    
    object = properties['OBJECTID']
    point_string = (str(geom.firstPoint.X) + ' ' + str(geom.firstPoint.Y))
    raster_value = arcpy.GetCellValue_management(input_fl_raster,point_string,1 )
    
    if raster_value.getOutput(0) <> 'NoData':
        properties['rast_value'] = raster_value.getOutput(0)
    arcpy.AddMessage('Gevonden waarde in raster: ' + str(raster_value.getOutput(0)))
          
    records.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                   'properties': properties})

collection.writerecords(records)
   

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand...')

spatial_reference = arcpy.Describe(input_fl_points).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name.lower() not in ['shape', 'id', 'fid']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)
arcpy.AddField_management(output_fl, 'rast_value', "FLOAT")

dataset = arcpy.InsertCursor(output_fl)

for p in collection.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point
        
    for field in fields:
        if field.name.lower() not in ['shape', 'id', 'fid']:
            row.setValue(field.name, p['properties'].get(field.name, None))        
    row.setValue('rast_value', p['properties'].get('rast_value', None)) 
    
    dataset.insertRow(row)
 
add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')
