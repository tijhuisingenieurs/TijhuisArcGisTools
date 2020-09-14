import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.dwp_tools import get_vertices_with_index, get_index_number_from_points
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand met route
# 1: Veld met id routes (id_field)
# 2: lijnenbestand voor toekenning volgnr
# 3: Doelbestand voor punten met volgnr
# 4: Doelbestand voor lijnen met volgnr

input_fl_route = arcpy.GetParameterAsText(0)
id_veld = arcpy.GetParameterAsText(1)
input_fl_lijnen = arcpy.GetParameterAsText(2)
output_file_lines = arcpy.GetParameterAsText(3)
output_file_points =  os.path.splitext(output_file_lines)[0]+'_controlepunten.shp'
check_points = arcpy.GetParameterAsText(4)

# Testwaarden voor test zonder GUI:
# input_fl_route = './testdata/input/Testdata_looproute.shp'
# id_veld = 'FID'
# input_fl_lijnen = './testdata/input/Testdata_watergangen.shp'
# output_file_lines = './testdata/output/2_b1_output/2_b1_output_test.shp'
# output_file_points = os.path.splitext(output_file_lines)[0]+'_controlepunten.shp'
# check_points = False

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand route = ' + input_fl_route)
arcpy.AddMessage('Route ID veld = ' + str(id_veld))
arcpy.AddMessage('Lijnenbestand voor volgnr = ' + input_fl_lijnen)
arcpy.AddMessage('Doelbestand voor punten met volgnr = ' + str(output_file_points))
arcpy.AddMessage('Doelbestand voor lijnen met volgnr = ' + str(output_file_lines))

# voorbereiden data typen en inlezen data
arcpy.AddMessage('Bezig met voorbereiden van de data...')

# vullen collection route
line_col_route = MemCollection(geometry_type='MultiLinestring')
records = []
rows_route = arcpy.SearchCursor(input_fl_route)
fields_route = arcpy.ListFields(input_fl_route)
point = arcpy.Point()

for row in rows_route:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields_route:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

line_col_route.writerecords(records)

# vullen collection lijnen
line_col_lijnen = MemCollection(geometry_type='MultiLinestring')
records = []
rows_lijnen = arcpy.SearchCursor(input_fl_lijnen)
fields_lijnen = arcpy.ListFields(input_fl_lijnen)
point = arcpy.Point()

for row in rows_lijnen:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields_lijnen:
        if field.name.lower() != 'shape':
            properties[field.name] = row.getValue(field.name)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

line_col_lijnen.writerecords(records)

# aanroepen tool
arcpy.AddMessage('Bezig met uitvoeren van get_vertices_with_index...')

point_col = get_vertices_with_index(line_col_route, id_veld)

arcpy.AddMessage('Bezig met uitvoeren van get_index_number_from_points...')

line_col_lijnen_indexed = get_index_number_from_points(line_col_lijnen, point_col, 'vertex_nr')

# wegschrijven tool resultaat
arcpy.AddMessage('Bezig met het genereren van het doelbestand punten...')

spatial_reference = arcpy.Describe(input_fl_route).spatialReference

output_name = os.path.basename(output_file_points).split('.')[0]
output_dir = os.path.dirname(output_file_points)

output_fl_points = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl_points,'line_id', 'SHORT')
arcpy.AddField_management(output_fl_points,'vertex_nr', 'DOUBLE', 8, 2)

dataset = arcpy.InsertCursor(output_fl_points)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
          
    row.setValue('line_id', p['properties'].get('line_id', 0))        
    row.setValue('vertex_nr', p['properties'].get('vertex_nr', 0.00)) 
   
    dataset.insertRow(row)

if check_points:
    add_result_to_display(output_fl_points, output_name)

arcpy.AddMessage('Bezig met het genereren van het doelbestand lijnen...')

spatial_reference = arcpy.Describe(input_fl_lijnen).spatialReference

output_name = os.path.basename(output_file_lines).split('.')[0]
output_dir = os.path.dirname(output_file_lines)

output_fl_lines = arcpy.CreateFeatureclass_management(output_dir, output_name, 'Polyline',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl_lines,'route_id', 'SHORT')
arcpy.AddField_management(output_fl_lines,'volgnr', 'DOUBLE', 8, 2)
arcpy.AddField_management(output_fl_lines,'richting', 'SHORT')

dataset = arcpy.InsertCursor(output_fl_lines)

for l in line_col_lijnen_indexed.filter():
    row = dataset.newRow()
    mline = arcpy.Array()
    for line_part in l['geometry']['coordinates']:
        array = arcpy.Array()
        for p in line_part:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)
            
        mline.add(array)

    row.Shape = mline

    row.setValue('route_id', l['properties'].get('line_id', 999))           
    row.setValue('volgnr', l['properties'].get('volgnr', 999.00))
    row.setValue('richting', 0)        

    dataset.insertRow(row)

add_result_to_display(output_fl_lines, output_name)

arcpy.AddMessage('Gereed')
