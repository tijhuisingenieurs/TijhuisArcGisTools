import os.path
import sys
import logging
import arcpy
from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging
# import random

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection, OrderedDict
from gistools.tools.representative_length import representative_length
from gistools.utils.collection import MemCollection
from gistools.utils.geometry import TLine, TMultiLineString

logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Read the parameter values
# 0: Lijnenbestand hydrovakken
# 1: Lijnenbestand profielen
# 2: Doelbestand profiellijnen
# 3: Split lines?
# 4: Doelbestand split lines

input_lines = arcpy.GetParameter(0)
input_profiles = arcpy.GetParameter(1)
id_field = arcpy.GetParameterAsText(2)
output_file = arcpy.GetParameterAsText(3)
output_split = arcpy.GetParameter(4)
output_split_file = arcpy.GetParameterAsText(5)

# random_nr = random.randint(0, 100)
# input_lines = "C:\Users\eline\Documents\ArcGIS\Jolanda_1207\TI18135_type_plichtige_sp.shp"
# input_profiles = "C:\Users\eline\Documents\ArcGIS\Jolanda_1207\TI18135_DWP_def.shp"
# output_file = "C:\Users\eline\Documents\ArcGIS\Jolanda_1207\TI18135_DWP_def_rep_length_{0}.shp".format(
#     random_nr
# )
# id_field = "DWPnr"

# Print ontvangen input naar console
log.info('Ontvangen parameters:')
log.info('Hydrovakkenbestand = %s', str(input_lines))
log.info('Profiellijnenbestand = %s', str(input_profiles))
log.info('Veld met unieke profielcode = %s', id_field)
log.info('Doelbestand = %s', str(output_file))

log.info('Bezig met inlezen data...')

# Fill hydrovakken collection
line_col = MemCollection(geometry_type='MultiLinestring')
records = []
line_cursor = arcpy.SearchCursor(input_lines)
fields_line = arcpy.ListFields(input_lines)
point = arcpy.Point()

for row in line_cursor:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields_line:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

line_col.writerecords(records)

# Fill profile collection
profile_col = MemCollection(geometry_type='MultiLinestring')
records = []
line_cursor = arcpy.SearchCursor(input_profiles)
fields_prof = arcpy.ListFields(input_profiles)
point = arcpy.Point()
prof_id_field = None

for row in line_cursor:
    geom = row.getValue('SHAPE')
    properties = OrderedDict()
    for field in fields_prof:
        if field.baseName.lower() != 'shape':
            properties[field.baseName] = row.getValue(field.baseName)
        if field.name == id_field:
            prof_id_field = field

    records.append({'geometry': {'type': 'MultiLineString',
                                 'coordinates': [[(point.X, point.Y) for
                                                  point in line] for line in geom]},
                    'properties': properties})

profile_col.writerecords(records)

# Call tool
log.info('Bezig met berekenen van de representatieve lengtes...')

rep_length_col, split_lines_col = representative_length(line_col, profile_col, id_field)

# Write result to new file
log.info('Bezig met genereren van het doelbestand...')
spatial_reference = arcpy.Describe(input_profiles).spatialReference

output_name = os.path.basename(output_file).split('.')[0]
output_dir = os.path.dirname(output_file)
output_fl = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)

# Add the fields from the profile collection to the new shapefile (excluding ID and geometry fields)
for field in fields_prof:
    if field.editable and field.baseName.lower() not in ['shape', 'id', 'fid', 'objectid']:
        arcpy.AddField_management(output_fl, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required,
                                  field.domain)

arcpy.AddField_management(output_file, 'voor_leng', 'DOUBLE')
arcpy.AddField_management(output_file, 'na_leng', 'DOUBLE')
arcpy.AddField_management(output_file, 'tot_leng', 'DOUBLE')

# Start filling the shapefile with the new points (new geometry and same properties as input file)
dataset = arcpy.InsertCursor(output_fl)

for l in rep_length_col.filter():
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

    for field in fields_prof:
        if field.editable and field.baseName.lower() not in ['shape', 'fid']:
            row.setValue(field.name, l['properties'].get(field.name, None))

    row.setValue('voor_leng', l['properties'].get('voor_leng', None))
    row.setValue('na_leng', l['properties'].get('na_leng', None))
    row.setValue('tot_leng', l['properties'].get('tot_leng', None))

    dataset.insertRow(row)

if output_split:
    # Write resulting split lines to file
    spatial_reference = arcpy.Describe(input_lines).spatialReference

    output_name_split = os.path.basename(output_split_file).split('.')[0]
    output_dir_split = os.path.dirname(output_split_file)
    output_fl_split = arcpy.CreateFeatureclass_management(output_dir_split, output_name_split, 'POLYLINE',
                                                    spatial_reference=spatial_reference)

    for field in fields_line:
        if field.editable and field.baseName.lower() not in ['shape', 'id', 'fid', 'objectid']:
            arcpy.AddField_management(output_fl_split, field.name, field.type, field.precision, field.scale,
                                      field.length, field.aliasName, field.isNullable, field.required,
                                      field.domain)

    arcpy.AddField_management(output_fl_split, prof_id_field.name, prof_id_field.type)
    arcpy.AddField_management(output_fl_split, 'tot_leng', 'DOUBLE')

    # Start filling the shapefile with the new points (new geometry and same properties as input file)
    dataset = arcpy.InsertCursor(output_fl_split)

    for l in split_lines_col.filter():
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

        for field in fields_line:
            if field.editable and field.baseName.lower() not in ['shape', 'fid', 'objectid']:
                row.setValue(field.name, l['properties'].get(field.name, None))

        row.setValue(id_field, str(l['properties'].get(id_field, None)))
        row.setValue('tot_leng', l['properties'].get('tot_leng', None))

        dataset.insertRow(row)
    add_result_to_display(output_fl_split, output_name_split)

# Add results to display
add_result_to_display(output_fl, output_name)

arcpy.AddMessage('Gereed')