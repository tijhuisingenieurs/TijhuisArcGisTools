import os.path
import sys
import logging
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from utils.addresulttodisplay import add_result_to_display

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: lijnenbestand
# 1: puntenbestand
# 2: Veld met afstand (distance_field)
# 3: Vaste waarde voor afstand (default_distance)
# 4: Veld met lengte haakselijn (length_field)
# 5: Vaste waarde voor lengte haakselijn (default_length)
# 6: Extra punt in restlengte zetten (restlength)
# 7: Lijst met velden (copy_fields)
# 8: Doelbestand voor haakse lijnen

input_fl = arcpy.GetParameterAsText(0)
input_points = arcpy.GetParameterAsText(1)
distance_veld = arcpy.GetParameterAsText(2)
default_afstand = arcpy.GetParameter(3)
lengte_veld = arcpy.GetParameterAsText(4)
default_lengte = arcpy.GetParameter(5)
restlength = arcpy.GetParameter(6)
copy_velden = [str(f) for f in arcpy.GetParameter(7)]
output_file_haakselijn = arcpy.GetParameterAsText(8)

# Testwaarden voor test zonder GUI:
# import tempfile
# import shutil
#
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'Lijnen_Bedum_singlepart.shp')
# input_fl = os.path.join(os.path.dirname(__file__),'test', 'data', 'TI17034_Trajectenshape_aaenmaas_2017.shp')
# input_points = os.path.join(os.path.dirname(__file__),'test', 'data', 'Test_kwaliteit_punten.shp')
# selectie = 'FALSE'
# distance_veld = None
# default_afstand = 10.0
# lengte_veld = None
# default_lengte = 15
# restlength = True
# copy_velden = ['HYDRO_CODE', 'DATUM_KM', 'VER_EIND']
# test_dir = os.path.join(tempfile.gettempdir(), 'arcgis_test')
# if os.path.exists(test_dir):
#     # empty test directory
#     shutil.rmtree(test_dir)
# os.mkdir(test_dir)
#   
#    
# output_file_haakselijn =  os.path.join(test_dir, 'test_haakselijnen.shp')

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + input_fl)
arcpy.AddMessage('Puntenbestand = ' + input_points)
arcpy.AddMessage('Afstand uit veld = ' + str(distance_veld))
arcpy.AddMessage('Afstand vaste waarde = ' + str(default_afstand))
arcpy.AddMessage('Lengte haakse lijn uit veld = ' + str(lengte_veld))
arcpy.AddMessage('Lengte haakse lijn vaste waarde = ' + str(default_lengte))
arcpy.AddMessage('Restlengte extra haakse lijn geven = ' + str(restlength))
arcpy.AddMessage('Over te nemen velden = ' + str(copy_velden))
arcpy.AddMessage('Bestandsnaam voor output haakse lijnen = ' + str(output_file_haakselijn))

# validatie ontvangen parameters
if input_points == None:
    if distance_veld is None and default_afstand is None:
        raise ValueError('Geen afstand opgegeven')
    
    if default_afstand < 0 and distance_veld is None:
        raise ValueError('Geen geldige afstand opgegeven')
    
if lengte_veld is None and default_afstand is None:
    raise ValueError('Geen afstand opgegeven')

if default_lengte < 0 and distance_veld is None:
    raise ValueError('Geen geldige afstand opgegeven')

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

collection = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_fl)
fields = arcpy.ListFields(input_fl)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_points_on_line...')

if input_points is None or input_points == '':
    point_col = get_points_on_line(collection,
                                   copy_velden,
                                   distance_field=distance_veld,
                                   fixed_distance=default_afstand,
                                   max_repr_length= restlength)
else:
    point_col = MemCollection(geometry_type='MultiPoint')
    records = []
    rows = arcpy.SearchCursor(input_points)
    fields = arcpy.ListFields(input_points)
    point = arcpy.Point()
    
    # vullen collection
    for row in rows:
        geom = row.getValue('SHAPE')
        properties = OrderedDict()
        for field in fields:
            if field.name.lower() != 'shape':
                properties[field.name] = row.getValue(field.name)
              
        records.append({'geometry': {'type': 'Point',
                                     'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                       'properties': properties})
    
    point_col.writerecords(records)
    
    copy_velden = []
    
    for field in fields:
        if field.name.lower() not in ['fid', 'shape']:
            copy_velden.append(field.name.lower())
    

haakselijn_col = get_haakselijnen_on_points_on_line(collection, 
                                                    point_col, 
                                                    copy_velden,
                                                    length_field=lengte_veld,
                                                    default_length=default_lengte)

# wegschrijven tool resultaat pointsonline
spatial_reference = arcpy.Describe(input_fl).spatialReference

if input_points is None or input_points == '':
    arcpy.AddMessage('Bezig met het genereren van het doelbestand met punten...')
    output_name_points = os.path.basename(output_file_haakselijn).split('.')[0] + '_intersectiepunten'
    output_dir_points = os.path.dirname(output_file_haakselijn)

    output_fl_points = arcpy.CreateFeatureclass_management(output_dir_points, output_name_points, 'POINT', 
                                                       spatial_reference=spatial_reference)

    for field in fields:
        if field.name in copy_velden:
            arcpy.AddField_management(output_fl_points, field.name, field.type, 
                                      field.precision, field.scale,
                                      field.length, field.aliasName, field.isNullable, 
                                      field.required, field.domain)
    
    dataset = arcpy.InsertCursor(output_fl_points)
    
    for p in point_col.filter():
        row = dataset.newRow()
        point = arcpy.Point()
        point.X = p['geometry']['coordinates'][0]
        point.Y = p['geometry']['coordinates'][1]
        row.Shape = point
            
        for field in fields:
            if field.name in copy_velden:
                row.setValue(field.name, p['properties'].get(field.name, None))        
    
        dataset.insertRow(row)
    
    add_result_to_display(output_fl_points, output_name_points) 

# wegschrijven tool resultaat haakselijnen
arcpy.AddMessage('Bezig met het genereren van het doelbestand met haakse lijnen...')

output_name_haakselijn = os.path.basename(output_file_haakselijn).split('.')[0]
output_dir_haakselijn = os.path.dirname(output_file_haakselijn)

output_fl_haakselijnen = arcpy.CreateFeatureclass_management(output_dir_haakselijn, 
                                                             output_name_haakselijn, 'POLYLINE', 
                                                             spatial_reference=spatial_reference)

for field in fields:
    if field.name in copy_velden:
        arcpy.AddField_management(output_fl_haakselijnen, field.name, field.type, 
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, 
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl_haakselijnen)

# Haakselijn_col bevat enkel LineStrings, geen MultiLineStrings, nalopen line_parts is dus niet nodig...
for l in haakselijn_col.filter():
    row = dataset.newRow()
    mline = arcpy.Array()
    array = arcpy.Array()
    for p in l['geometry']['coordinates']:
        point.X = p[0]
        point.Y = p[1]
        array.add(point)

    mline.add(array)

    row.Shape = mline

    for field in fields:
        if field.name in copy_velden:
            row.setValue(field.name, l['properties'].get(field.name, None))

    dataset.insertRow(row)

add_result_to_display(output_fl_haakselijnen, output_name_haakselijn) 

arcpy.AddMessage('Gereed')
