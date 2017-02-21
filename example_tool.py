import arcpy
from collections import OrderedDict
import os.path

point = arcpy.Point()
array = arcpy.Array()

filename = 'c:\\tmp\\rd_line.shp'

input_filename = arcpy.GetParameterAsText(0)
only_selected = arcpy.GetParameter(1)
output_filename = arcpy.GetParameterAsText(2)

features = arcpy.SearchCursor(input_filename)
fields = arcpy.ListFields(filename)
items = []

for feature in features:
    geom = feature.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = feature.getValue(field.baseName)

    items.append({'geometry': {'type': 'MultiLineString',
                               'coordinates': [[(point.X, point.Y) for point in line]
                                               for line in geom]},
                  'properties': properties})

spatial_reference = arcpy.Describe(filename).spatialReference

output_dir = os.path.dirname(output_filename)
output_filename = os.path.basename(output_filename)

template = {}
output_fl = arcpy.CreateFeatureclass_management(output_dir,
                                                output_filename,
                                                'POLYLINE',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name.lower() not in ['shape', 'fid', 'id']:
        arcpy.AddField_management(output_fl, field.name, field.type,
                                  field.precision, field.scale, field.length,
                                  field.aliasName, field.isNullable,
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_fl)

for item in items:
    row = dataset.newRow()
    mline = arcpy.Array()
    for line_part in item['geometry']['coordinates']:
        array = arcpy.Array()
        for p in line_part:
            point.X = p[0]
            point.Y = p[1]
            array.add(point)

        mline.add(array)

    row.Shape = mline
    # arcpy.geometries.Polyline(line, spatial_reference)

    for field in fields:
        if field.name.lower() not in ['shape', 'fid', 'id']:
            row.setValue(field.name, item['properties'].get(field.name, None))

    dataset.insertRow(row)

print items
