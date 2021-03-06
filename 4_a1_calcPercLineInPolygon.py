# TODO: this script is temporary. It is made as a quick solution. Script should be expanded so that the actual code /
# TODO  is contained in GIS tools. Also, more functionality should be added, as Esgo and Elma want.

import os.path
import sys
import logging
import arcpy
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))


logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)

# Read the parameter values
# 1. Lijnenbestand
# 2. Vlakkenbestand

input_line_fl = arcpy.GetParameter(0)
input_polygon_fl = arcpy.GetParameter(1)

# Local variables:
Geometry_Properties = "LENGTH"
Length_Unit = "METERS"
Coordinate_System = "PROJCS['RD_New',GEOGCS['GCS_Amersfoort',DATUM['D_Amersfoort'," \
                    "SPHEROID['Bessel_1841',6377397.155,299.1528128]],PRIMEM['Greenwich',0.0]," \
                    "UNIT['Degree',0.0174532925199433]],PROJECTION['Double_Stereographic']," \
                    "PARAMETER['False_Easting',155000.0],PARAMETER['False_Northing',463000.0]," \
                    "PARAMETER['Central_Meridian',5.38763888888889],PARAMETER['Scale_Factor',0.9999079]," \
                    "PARAMETER['Latitude_Of_Origin',52.15616055555555],UNIT['Meter',1.0]]"

# line_col = MemCollection(geometry_type='MultiLinestring')
# records = []
# line_cursor = arcpy.SearchCursor(input_line_fl)
# fields = arcpy.ListFields(input_line_fl)
# point = arcpy.Point()
#
# # vullen collection
# for row in line_cursor:
#     geom = row.getValue('SHAPE')
#     properties = OrderedDict()
#     for field in fields:
#         if field.baseName.lower() != 'shape':
#             properties[field.baseName] = row.getValue(field.baseName)
#
#     records.append({'geometry': {'type': 'MultiLineString',
#                                  'coordinates': [[(point.X, point.Y) for
#                                                   point in line] for line in geom]},
#                     'properties': properties})
#
# line_col.writerecords(records)

# Put the input lines in memory
spatial_reference = arcpy.Describe(input_line_fl).spatialReference
temp_name = "in_memory\lines"

# Copy the lines into memory to perform calculations
temp_lines = arcpy.CopyFeatures_management(input_line_fl, temp_name)
fields = arcpy.ListFields(temp_lines)

# Add a unique field
arcpy.AddField_management(temp_lines, "unique", "SHORT")
arcpy.CalculateField_management(temp_lines, "unique", "!FID!-1", "PYTHON_9.3")

# Add a LENGTH field
arcpy.AddGeometryAttributes_management(temp_lines, Geometry_Properties, Length_Unit,
                                       Coordinate_System=Coordinate_System)

# Perform dissolve on polygons to obtain one polygon only, save this to tempfile
temp_poly = "in_memory/polygons"
arcpy.Dissolve_management(input_polygon_fl, temp_poly)

# Perform clip to get new length of lines
temp_clip = "in_memory/clipped_lines"

arcpy.Clip_analysis(temp_lines, temp_poly, temp_clip)

# Add a LENGTH field
arcpy.AddGeometryAttributes_management(temp_clip, Geometry_Properties, Length_Unit,
                                       Coordinate_System=Coordinate_System)

# Join the length field of the clipped lines to the temporary input lines file
arcpy.JoinField_management(temp_lines, "unique", temp_clip, "unique", "LENGTH")
fields = arcpy.ListFields(temp_lines)
last_field = fields[-1].name

# Make new field and calculate percentage within polygon
before = "!LENGTH!"
after = "!" + last_field + "!"
expression = "calc_perc(" + before + "," + after + ")"

codeblock = """
def calc_perc(before, after):
    perc = 0
    if after > 0:
        perc = (after / before) * 100
        return perc
    else:
        return(0)"""

arcpy.AddField_management(temp_lines, "perc_in", "DOUBLE")
arcpy.CalculateField_management(temp_lines, "perc_in", expression, "PYTHON_9.3", codeblock)

# Join this new field to the input lines
arcpy.JoinField_management(input_line_fl, fields[0].name, temp_lines, "unique", "perc_in")