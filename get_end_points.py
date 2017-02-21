import sys
import os.path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.clean import get_end_points

# Read the parameter values
# 0: lijnenbestand
# 1: Id veld van lijnenbestand
# 2: Marge waarbinnen lijnen gecombineerd zijn
# 3: Doelmap voor doelbestand
# 4: Doelbestand voor punten

input_fl = arcpy.GetParameterAsText(0)
tolerance = arcpy.GetParameter(1)
id_field = arcpy.GetParameterAsText(2)
output_dir = arcpy.GetParameterAsText(3)
output_name = arcpy.GetParameterAsText(4)

# Testwaarden voor test zonder GUI:
# input_fl = 'C:\\tmp\\rd_line.shp'
# tolerance = 0.001
# id_field = 'id'
# output_dir = 'C:\\tmp\\'
# output_name = 'end_points'

# Print ontvangen input naar console
print 'Ontvangen parameters:'
print 'Lijnenbestand = ', input_fl
print 'Tolerantie = ', tolerance
print 'Id veld = ', id_field
print 'Bestandslocatie voor output = ', str(output_dir)
print 'Bestandsnaam voor output = ', str(output_name)

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
print 'Bezig met uitvoeren van get_endpoints..'

point_col = get_end_points(collection, id_field, tolerance)

# wegschrijven tool resultaat
print 'Bezig met het genereren van het doelbestand...'
spatial_reference = arcpy.Describe(input_fl).spatialReference

output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl, 'line_ids', 'text')
arcpy.AddField_management(output_fl, 'line_count', 'integer')

dataset = arcpy.InsertCursor(output_fl)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]

    row.Shape = point

    for field in ['line_ids', 'line_count']:
        row.setValue(field, p['properties'].get(field, None))

    dataset.insertRow(row)

print 'Gereed'
