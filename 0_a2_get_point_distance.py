###########################################################################
############### 0_a2 Bepaal afstand van punten op lijnen ##################
###########################################################################

import os.path
import sys
from shapely.geometry import Point

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.utils.geometry import TLine, TMultiLineString

# Read the parameter values
# 0: Lijnenbestand
# 1: Puntenbestand
# 2: Doelbestand

input_fl_lines = arcpy.GetParameterAsText(0)
input_fl_points = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)

# Test script without ArcMAP
# input_fl_lines = './testdata/input/Testdata_watergangen.shp'
# input_fl_points = './testdata/input/Testdata_dwarsprofielen_punten.shp'
# output_file = './testdata/output/0_a2_output'

# Print ontvangen input naar console
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Lijnenbestand = ' + str(input_fl_lines))
arcpy.AddMessage('Puntenbestand = ' + str(input_fl_points))
arcpy.AddMessage('Doelbestand = ' + str(output_file))

# voorbereiden data typen en inlezen data
arcpy.AddMessage( 'Bezig met voorbereiden van de data...')

line_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_fl_lines)
fields = arcpy.ListFields(input_fl_lines)
point = arcpy.Point()

# vullen collection
for row in rows:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.baseName.lower() not in ['shape', 'id', 'fid']:
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

line_col.writerecords(records)


point_col = MemCollection(geometry_type='MultiPoint')
records2 = []
rows2 = arcpy.SearchCursor(input_fl_points)
fields2 = arcpy.ListFields(input_fl_points)
point = arcpy.Point()

# vullen collections
for row in rows2:
    geom = row.getValue('SHAPE')
    properties2 = OrderedDict()
    for field in fields2:
        if field.name.lower() != 'shape':
            properties2[field.name] = row.getValue(field.name)
          
    records2.append({'geometry': {'type': 'Point',
                                 'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                   'properties': properties2})

point_col.writerecords(records2)

# aanroepen tool
arcpy.AddMessage( 'Bezig met berekenen afstanden..')

output_point_col = MemCollection(geometry_type='MultiPoint')
records3 = []
i = 0

for l in line_col:
    i = i + 1
    
    if type(l['geometry']['coordinates'][0][0]) != tuple:
        line = TLine(l['geometry']['coordinates'])
    else:
        line = TMultiLineString(l['geometry']['coordinates']) 
    
    for p in point_col.filter(bbox=line.bounds, precision=10**-3):
        punt = Point(p['geometry']['coordinates'])
        if line.almost_intersect_with_point(punt):
                
            properties3 = OrderedDict()        
            
            segment = line.get_line_part_point(punt)
            afstand = segment[2]  
            
            properties3['punt_nr'] = p['properties']['FID']
            properties3['lijn_nr'] = i   
            properties3['afstand'] = afstand
                
            records3.append({'geometry': {'type': 'Point',
                                     'coordinates': (p['geometry']['coordinates'][0], p['geometry']['coordinates'][1])},
                       'properties': properties3})
        
output_point_col.writerecords(records3)

# wegschrijven tool resultaat
arcpy.AddMessage( 'Bezig met het genereren van het doelbestand...')
spatial_reference = arcpy.Describe(input_fl_points).spatialReference


output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl, 'punt_nr', "SHORT")
arcpy.AddField_management(output_fl, 'Lijn_nr', "SHORT")
arcpy.AddField_management(output_fl, 'afstand', "DOUBLE")

dataset = arcpy.InsertCursor(output_fl)

for p in output_point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point
    
    row.setValue('punt_nr', p['properties'].get('punt_nr', None))
    row.setValue('lijn_nr', p['properties'].get('lijn_nr', None))    
    row.setValue('afstand', p['properties'].get('afstand', None))
           
    dataset.insertRow(row)

add_result_to_display(output_fl, output_name)

arcpy.AddMessage( 'Gereed')
