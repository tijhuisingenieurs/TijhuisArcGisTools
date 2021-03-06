###########################################################################
############### 0_a1 Bereken de waterbreedte ahv de BGT ###################
###########################################################################

import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

import arcpy
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict
from shapely.geometry import MultiLineString, LineString, MultiPoint
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from gistools.utils.collection import MemCollection
from gistools.utils.geometry import TLine, TMultiLineString

# Read the parameter values
# 0: Lijnenbestand watergangen
# 1: Lijnenbestand profielen
# 2: Field waar ID of naam van profiel staat
# 3: Vlakkenbestand BGT
# 4: Doelbestand

input_watergangen = arcpy.GetParameterAsText(0)
input_profielen = arcpy.GetParameterAsText(1)
input_bgt = arcpy.GetParameterAsText(3)
prof_id = arcpy.GetParameterAsText(2)
output_bestand = arcpy.GetParameterAsText(4)

# Test script without ArcMAP
# input_watergangen = './testdata/input/Testdata_watergangen.shp'
# input_profielen = './testdata/input/Testdata_dwarsprofielen.shp'
# input_bgt = './testdata/input/BGT.shp'
# output_bestand = './testdata/output/0_a1_output'
# prof_id = 'DWPnr'

# ---------------------------------------
arcpy.AddMessage('Opgegeven bestanden: ')
arcpy.AddMessage('Input watergangen: ' + input_watergangen)
arcpy.AddMessage('Input profielen: ' + input_profielen)
arcpy.AddMessage('Input bgt: ' + input_bgt)
arcpy.AddMessage('Output bestand ' + output_bestand)

# Zet de lijnen om naar een memcollection: watergangen
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
arcpy.AddMessage('Watergangen ingelezen')

# Zet de lijnen om naar een memcollection: profielen
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
arcpy.AddMessage('Profielen ingelezen')

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
    for profile in profielen_input_col.filter(bbox=line.bounds, precision=10 ** -6):
        if type(profile['geometry']['coordinates'][0][0]) != tuple:
            prof = LineString(profile['geometry']['coordinates'])
        else:
            prof = MultiLineString(profile['geometry']['coordinates'])

        # Making an intersection of the profile with the line creates a point
        x = line.intersection(prof)

        # If the profile intersects the watergang more than once
        if isinstance(x, MultiPoint):
            arcpy.AddMessage('Profiel {0} heeft meerdere intersecties met de onderliggende BGT. Er wordt geen '
                             'breedte bepaald'.format(profile['properties'][prof_id]))
            continue

        # If the profile has an intersect with the line, and thus a point is created
        if not x.is_empty:
            points.append(
                {'geometry': {'type': 'Point', 'coordinates': x.coords[0]},
                 'properties': profile['properties']})

    # No profiles on the line
    if not points:
        continue

    point_col.writerecords(points)
arcpy.AddMessage('Maken haakse lijnen')
# -------- maak haakse lijnen -----------
haakselijnen_col = get_haakselijnen_on_points_on_line(watergangen_col, point_col, [prof_id],
                                                      default_length=100, length_field=None, source="points")

# --------- Clip haakse lijnen met BGT ----------
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
                row.setValue(field, str(l['properties'].get(field, None)))
    dataset.insertRow(row)

arcpy.AddMessage('Clip lijnen op BGT')

# Clip haakse lijnen op de BGT en maak het singleparts
clip_haaks = "in_memory\\clip_haaks"
arcpy.Clip_analysis(temp_haakselijnen, input_bgt, clip_haaks)
temp_sp = "in_memory\\temp_sp"
arcpy.MultipartToSinglepart_management(clip_haaks, temp_sp)
lay = arcpy.MakeFeatureLayer_management(temp_sp, "Haakse_Lijn_Singlepart_Feature_class")

# Selecteer alleen de lijnen die een intersect hebben met de punten
haakse_lijnen_bestandsnaam = os.path.basename(output_bestand).split('.')[0] + '.shp'
selected_haakselijnen = output_bestand + '.shp'

# haakse_lijnen_bestandsnaam = "\\waterbreedtes_profielen.shp"
# selected_haakselijnen = output_folder + haakse_lijnen_bestandsnaam
selection = arcpy.SelectLayerByLocation_management(lay, "INTERSECT", temp_points, "", "NEW_SELECTION", "NOT_INVERT")
arcpy.CopyFeatures_management(selection, selected_haakselijnen)

arcpy.AddMessage('Bepaal de breedtes')

# ------ Add field length -----------------------
Geometry_Properties = "LENGTH"
Length_Unit = "METERS"
Coordinate_System = "PROJCS['RD_New',GEOGCS['GCS_Amersfoort',DATUM['D_Amersfoort'," \
                    "SPHEROID['Bessel_1841',6377397.155,299.1528128]],PRIMEM['Greenwich',0.0]," \
                    "UNIT['Degree',0.0174532925199433]],PROJECTION['Double_Stereographic']," \
                    "PARAMETER['False_Easting',155000.0],PARAMETER['False_Northing',463000.0]," \
                    "PARAMETER['Central_Meridian',5.38763888888889],PARAMETER['Scale_Factor',0.9999079]," \
                    "PARAMETER['Latitude_Of_Origin',52.15616055555555],UNIT['Meter',1.0]]"
# Add a LENGTH field
arcpy.AddField_management(selected_haakselijnen, Geometry_Properties, "DOUBLE")
arcpy.AddGeometryAttributes_management(selected_haakselijnen, Geometry_Properties, Length_Unit,
                                       Coordinate_System=Coordinate_System)

# ------ Add field length categorie -------------
# Make new field and get the categorie from the breedte
expression = "getCategorie(!LENGTH!)"

codeblock = """
def getCategorie(waarde):
    if waarde < 5:
        return "<5 meter"
    elif waarde < 12:
        return "5-12 meter"   
    elif waarde < 25:
        return "12-25 meter"  
    elif waarde < 60:
        return "25-60 meter" 
    elif waarde > 60:
        return ">60 meter"   
    else:
        return "geen breedte bepaald"                       
"""

arcpy.AddField_management(selected_haakselijnen, "breedte", "TEXT")
arcpy.CalculateField_management(selected_haakselijnen, "breedte", expression, "PYTHON_9.3", codeblock)

add_result_to_display(selected_haakselijnen, haakse_lijnen_bestandsnaam)

arcpy.AddMessage('Doelbestand gemaakt: ' + haakse_lijnen_bestandsnaam)
arcpy.AddMessage('Gereed')
