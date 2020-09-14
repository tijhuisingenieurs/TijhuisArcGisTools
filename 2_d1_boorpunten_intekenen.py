import os.path
import sys
import arcpy
import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from collections import OrderedDict
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line_amount
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from gistools.tools.connect_start_end_points import get_points_on_line_random
from utils.addresulttodisplay import add_result_to_display

# Read the parameter values
# 0: lijnenbestand
# 1: BGT bestand
# 2: Veld met monstervaknamen
# 3: Doelbestand voor monstervakken
# 4: Aantal boorpunten per monstervak
# 5: Minimale afstand (in m) voor boorpunten vanaf de kade
# 6: Doelbestand voor boorpunten

# Script arguments
watergang = arcpy.GetParameterAsText(0)
bgt = arcpy.GetParameterAsText(1)
monstervak_veld = arcpy.GetParameterAsText(2)
monstervakken_doelbestand = arcpy.GetParameterAsText(3)
aantal_boorpunten = arcpy.GetParameterAsText(4)
minimale_afstand = arcpy.GetParameterAsText(5)
doelbestand_boorpunten = arcpy.GetParameterAsText(6)

# Testwaarden voor test zonder GUI:
# watergang = './testdata/input/Testdata_watergangen.shp'
# bgt = './testdata/input/BGT.shp'
# monstervak_veld = 'MONSTERVAK'
# monstervakken_doelbestand = './testdata/output/2_d1_output_monstervakken.shp'
# aantal_boorpunten = 10
# minimale_afstand = 0.1
# doelbestand_boorpunten = './testdata/output/2_d1_output_boorpunten.shp'

# Clip de watergangen met de bgt and dissolve op monstervak
temp_clip = "in_memory\clip_watergangen"
clipped = arcpy.Clip_analysis(watergang, bgt, temp_clip)
dissolved = arcpy.Dissolve_management(temp_clip, monstervakken_doelbestand, monstervak_veld, "", "MULTI_PART", "DISSOLVE_LINES")

# Create points on line and haakse lijnen
collection = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(dissolved)
fields = arcpy.ListFields(dissolved)
point = arcpy.Point()

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

point_col = get_points_on_line_amount(collection, copy_fields=[monstervak_veld], default_amount=aantal_boorpunten)

temp_points = "in_memory\\temp_points"
spatial_reference = arcpy.Describe(watergang).spatialReference
output_name = os.path.basename(temp_points).split('.')[0]
output_dir = os.path.dirname(temp_points)

output_points = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                    spatial_reference=spatial_reference)

for field in fields:
    if field.name == monstervak_veld:
        arcpy.AddField_management(output_points, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_points)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point

    for field in fields:
        if field.name == monstervak_veld:
            row.setValue(field.name, p['properties'].get(field.name, None))

    dataset.insertRow(row)

haakselijnen_col = get_haakselijnen_on_points_on_line(collection, point_col, [monstervak_veld], default_length=100)

# Create temporary feature class from haakse lijnen
temp_haakselijnen = "in_memory\\temp_haaks"

output_name = os.path.basename(temp_haakselijnen).split('.')[0]
output_dir = os.path.dirname(temp_haakselijnen)

output_haakselijnen = arcpy.CreateFeatureclass_management(output_dir,
                                                output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name == monstervak_veld:
        arcpy.AddField_management(output_haakselijnen, field.name, field.type,
                                  field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable,
                                  field.required, field.domain)

dataset = arcpy.InsertCursor(output_haakselijnen)

for l in haakselijnen_col.filter():
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
        if field.name == monstervak_veld:
            row.setValue(field.name, l['properties'].get(field.name, None))

    dataset.insertRow(row)

# Clip haakse lijnen op de BGT en maak het singleparts
clip_haaks = "in_memory\\clip_haaks"
arcpy.Clip_analysis(temp_haakselijnen, bgt, clip_haaks)
temp_sp = "in_memory\\temp_sp"
arcpy.MultipartToSinglepart_management(clip_haaks, temp_sp)
lay = arcpy.MakeFeatureLayer_management(temp_sp, "Haakse_Lijn_Singlepart_Feature_class")

# Selecteer alleen de lijnen die een intersect hebben met de punten
temp_select = "in_memory\\temp_select"
selection = arcpy.SelectLayerByLocation_management(lay, "INTERSECT", temp_points, "", "NEW_SELECTION", "NOT_INVERT")
arcpy.CopyFeatures_management(selection, temp_select)

# Create points on line and haakse lijnen
haakselijnen_select_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(temp_select)
fields = arcpy.ListFields(temp_select)
point = arcpy.Point()

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

haakselijnen_select_col.writerecords(records)

# Random point op elke haakse lijn
boorpunten_col = get_points_on_line_random(haakselijnen_select_col, [monstervak_veld], default_offset=minimale_afstand)

output_name = os.path.basename(doelbestand_boorpunten).split('.')[0]
output_dir = os.path.dirname(doelbestand_boorpunten)

output_boorpunten = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field.name == monstervak_veld:
        arcpy.AddField_management(output_boorpunten, field.name, field.type, field.precision, field.scale,
                                  field.length, field.aliasName, field.isNullable, field.required, field.domain)

dataset = arcpy.InsertCursor(output_boorpunten)

for p in boorpunten_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point

    for field in fields:
        if field.name == monstervak_veld:
            row.setValue(field.name, p['properties'].get(field.name, None))

    dataset.insertRow(row)

add_result_to_display(output_boorpunten, output_name)