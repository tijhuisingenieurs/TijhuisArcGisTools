# bereken de waterbreedte ahv de BGT
# Input:
# lijnenbestand van de watergangen
# lijnenbestand van de profielen
# vlakkenbestand van de BGT
# Output:
# lijnenbestand van de profielen met daarbij 2 kolommen toegevoegd: breedte van de watergang in meter (double) en de
# breedte van de watergang in verschillende categorien (text)
#
# Verschillende stappen:
# Vind de intersectie van de watergangen met de profielen -> punten
# Maak op de intersectiepunten haakse lijnen van 100 m breed -> lijnen
# Clip de haakse lijnen op de BGT -> lijnen
# Spatial join van de geclipped lijnen met de punten
# Koppeling van de geclipped lijnen met de orginele profiellijnen
# Add fields met de verschillende kolommen en waterbreedtes
#---------------------------------------------------------------------------
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from gistools.utils.collection import MemCollection
from shapely.geometry import MultiLineString, LineString
from shapely.geometry import MultiPoint
from shapely.ops import split
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line


from gistools.utils.collection import MemCollection
from gistools.utils.geometry import TLine, TMultiLineString


# Read the parameter values
# 0: Lijnenbestand watergangen
# 1: Lijnenbestand profielen
# 2: Field waar ID of naam van profiel staat
# 3: Vlakkenbestand BGT
# 4: Doelmap

# input_watergangen = arcpy.GetParameterAsText(0)
# input_profielen = arcpy.GetParameterAsText(1)
# input_bgt = arcpy.GetParameterAsText(3)
# prof_id = arcpy.GetParameterAsText(2)
# output_folder = arcpy.GetParameterAsText(4)

# For without GIS
input_watergangen = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\waterbreedtes_BGT\watergangen.shp'
input_profielen = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\waterbreedtes_BGT\profielen.shp'
input_bgt = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\waterbreedtes_BGT\BGT.shp'
output_folder = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\waterbreedtes_BGT'
prof_id = 'Id'

# Zet de lijnen om naar een memcollection
#--------Watergangen --------------
watergangen_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_watergangen)
fields = arcpy.ListFields(input_watergangen)
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

watergangen_col.writerecords(records)

#---------Profielen-------------
profielen_input_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(input_profielen)
fields = arcpy.ListFields(input_profielen)
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

profielen_input_col.writerecords(records)

# ---------- Find intersection profielen en watergangen -------------
# Initalize new point collection for the intersection points
point_col = MemCollection(geometry_type='MultiPoint')

# Loop through each line and select the profiles that intersect the line
for feature in watergangen_col:
    # Check if line is LineString or MultiLineString and create the appropriate line object
    if type(feature['geometry']['coordinates'][0][0]) != tuple:
        line = TLine(feature['geometry']['coordinates'])
    else:
        line = TMultiLineString(feature['geometry']['coordinates'])

    # Initialize the list that collects the points that intersect with the line
    points = []

    # Loop through the profiles within the bounding box of the line
    for profile in profielen_input_col.filter(bbox=line.bounds, precision=10**-6):
        if type(profile['geometry']['coordinates'][0][0]) != tuple:
            prof = LineString(profile['geometry']['coordinates'])
        else:
            prof = MultiLineString(profile['geometry']['coordinates'])

        # Making an intersection of the profile with the line creates a point
        x = line.intersection(prof)

        # If the profile has an intersect with the line, and thus a point is created
        if not x.is_empty:
            points.append(
                {'geometry': {'type': 'Point', 'coordinates': x.coords[0]},
                          'properties': profile['properties']})

    # No profiles on the line
    if not points:
        continue

    point_col.writerecords(points)
k=3

# -------- maak haakse lijnen -----------
haakselijnen_col = get_haakselijnen_on_points_on_line(watergangen_col, point_col, [prof_id],
                                       default_length=100, length_field=None, source="points")

# --------- Clip haakse lijnen met BGT ----------
p = 90
# ______CODE om te gebruiken uit andere tools...___________
# -------------- Willekeurig verspreiden van de boorpunten -------------
# Zet om naar shapefile, zodat later arcpy tools toegepast kunnen  worden.
# Zet pointcol om naar shapefile, zodat later arcpy tools toegepast kunnen  worden.
temp_points = "in_memory\\temp_points"
spatial_reference = arcpy.Describe(input_watergangen).spatialReference
output_name = os.path.basename(temp_points).split('.')[0]
output_dir = os.path.dirname(temp_points)
fields = point_col[0]['properties'].keys()

output_points = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field == prof_id:
        arcpy.AddField_management(output_points, field, "STRING", field_length=50)

dataset = arcpy.InsertCursor(output_points)

for p in point_col.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point

    for field in fields:
        if field == prof_id:  # dit bestaat nu niet meer, ergens anders toevoegen
            row.setValue(field, p['properties'].get(field, None))

    dataset.insertRow(row)

# Maak haakse lijnen op de locatie van de gemaakte punten
# Create temporary feature class from haakse lijnen
temp_haakselijnen = "in_memory\\temp_haaks"

output_name = os.path.basename(temp_haakselijnen).split('.')[0]
output_dir = os.path.dirname(temp_haakselijnen)
fields = haakselijnen_col[0]['properties'].keys()

output_haakselijnen = arcpy.CreateFeatureclass_management(output_dir,
                                                output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)
for field in fields:
    if field == prof_id:
        arcpy.AddField_management(output_haakselijnen, field, "STRING", field_length=50)

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
        if field == prof_id:
            row.setValue(field, l['properties'].get(field, None))

    dataset.insertRow(row)

# Clip haakse lijnen op de BGT en maak het singleparts
clip_haaks = "in_memory\\clip_haaks"
arcpy.Clip_analysis(temp_haakselijnen, input_bgt, clip_haaks)
temp_sp = "in_memory\\temp_sp"
arcpy.MultipartToSinglepart_management(clip_haaks, temp_sp)
lay = arcpy.MakeFeatureLayer_management(temp_sp, "Haakse_Lijn_Singlepart_Feature_class")

# Selecteer alleen de lijnen die een intersect hebben met de punten
temp_select = "in_memory\\temp_select"
selection = arcpy.SelectLayerByLocation_management(lay, "INTERSECT", temp_points, "", "NEW_SELECTION", "NOT_INVERT")
arcpy.CopyFeatures_management(selection, temp_select)

# Maak van de geselecteerde lijnen van shape naar memcollection
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

K = 20
# --------------- OUTPUT profiellijnen shape ------------------
output_name = 'Waterbreedte_profielen'
output_dir = os.path.dirname(output_folder)
fields = haakselijnen_select_col[0]['properties'].keys()

output_waterbreedte_profielen = arcpy.CreateFeatureclass_management(output_dir,
                                                output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)
for field in fields:
    if field == prof_id:
        arcpy.AddField_management(output_haakselijnen, field, "STRING", field_length=50)

dataset = arcpy.InsertCursor(output_haakselijnen)

for l in haakselijnen_select_col.filter():
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
        if field == prof_id:
            row.setValue(field, l['properties'].get(field, None))

    dataset.insertRow(row)

# ------ Add field length -----------------------

# ------ Add field length categorie -------------