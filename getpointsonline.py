import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: gebruik alleen geselecteerde features (boolean)
# 2: Veld met afstand (distance_field)
# 3: Vaste waarde voor afstand (default_distance)
# 4: Lijst met velden (copy_fields)
# 5: Doelmap voor doelbestand
# 6: Doelbestand voor punten

input_fl = arcpy.GetParameterAsText(0)
selectie = arcpy.GetParameter(1)
distance_veld = arcpy.GetParameterAsText(2)
default_afstand = arcpy.GetParameter(3)
copy_velden = arcpy.GetParameterAsText(4)
output_dir = arcpy.GetParameterAsText(5)
output_name = arcpy.GetParameterAsText(6)

# Testwaarden voor test zonder GUI:
# input_fl = 'C:\\Users\\annemieke\\Desktop\\TIJDELIJK\\1. GIS zaken\\Test_kwaliteit.shp'
# selectie = 'FALSE'
# distance_veld = None
# default_afstand = 10.0
# copy_velden = ['HYDRO_CODE', 'DATUM_KM', '[VER_EIND]']
# output_dir = 'C:\\Users\\annemieke\\Desktop\\TIJDELIJK\\1. GIS zaken\\'
# output_name = 'test_punten'

# Print ontvangen input naar console
print 'Ontvangen parameters:'
print 'Lijnenbestand = ', input_fl
print 'Gebruik selectie = ', str(selectie)
print 'Afstand uit veld = ', str(distance_veld)
print 'Afstand vaste waarde = ', str(default_afstand)
print 'Over te nemen velden = ', str(copy_velden)
print 'Bestandslocatie voor output = ', str(output_dir)
print 'Bestandsnaam voor output = ', str(output_name)

# validatie ontvangen parameters
if distance_veld is None and default_afstand is None:
    raise ValueError('Geen afstand opgegeven')

if default_afstand < 0 and distance_veld is None:
    raise ValueError('Geen geldige afstand opgegeven')

# voorbereiden data typen en inlezen data
print 'Bezig met voorbereiden van de data...'

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
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)
          
    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                 point in line] for line in geom]},
                   'properties': properties})

collection.writerecords(records)

# aanroepen tool
print 'Bezig met uitvoeren van get_points_on_line...'

point_col = get_points_on_line(collection, copy_velden, 
                               distance_field=distance_veld,
                               default_distance=default_afstand)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_fl).spatialReference

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT', 
                                                spatial_reference=spatial_reference)

#
# ToDo: velden ophalen uit output collection op basis van copy_fields
#
for field in fields:
    if field.name.lower() not in ['shape', 'fid', 'id']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
#     print p
#     print point.X
#     print point.Y
    row.Shape = point
        
    for field in fields:
        if field.name.lower() not in ['shape', 'fid', 'id']:
            row.setValue(field.name, p['properties'].get(field.name, None))        

    dataset.insertRow(row)

display_name = output_name
add_result_to_display(output_fl, display_name)

print 'Gereed'
