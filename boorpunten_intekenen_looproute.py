# Deze tool gaat aan de hand van een looproute aan de monstervakken de boorpunten intekenen en nummeren

# maak van lijnenbestand monstervakken een dissolve en een memcollection
# maak punten op de monstervakken
# Voer de tool van de volgnummering uit op de looproute en monstervakken
# dan de tool van de hernummerering van de punten op de looproute
# Daarna de haakselijnen maken op de punten
# De punten willekeurig verspreiden binnen de bgt
# De punten aanpassen zodat ze van 1-10 lopen steeds ipv doornummeren

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
from gistools.tools.dwp_tools import get_vertices_with_index, get_index_number_from_points
from gistools.tools.number_points import number_points_on_line_boorpunten
from utils.addresulttodisplay import add_result_to_display

arcpy.Delete_management("in_memory")

# Read the parameter values
# 0: Lijnenbestand van de monstervakken
# 1: Lijnenbestand van de looproute
# 2: Polygonbestand van de BGT
# 3: Veld waarin het monstervaknummer staat
# 4: Aantal boorpunten per monstervak in te tekenen
# 5: Minimale afstand van de kant voor het intekenen van de boorpunten
# 6: Doelbestand monstervakken (dissolved)
# 7: Doelbestand boorpunten

# # Script arguments
watergang = arcpy.GetParameterAsText(0)
input_fl_route = arcpy.GetParameterAsText(1)
bgt = arcpy.GetParameterAsText(2)
monstervak_veld = arcpy.GetParameterAsText(3)
aantal_boorpunten = arcpy.GetParameterAsText(4)
minimale_afstand = arcpy.GetParameterAsText(5)
monstervakken_doelbestand = arcpy.GetParameterAsText(6)
doelbestand_boorpunten = arcpy.GetParameterAsText(7)

#-------------------------------
# Script arguments voor in GUI
# nummer_test = (np.random.random_integers(1,1000))
# watergang = "C:\Users\elma\Documents\GitHub\MAP_eline\Algemeen\GIS\Tooltesting\TestData\Tool_d1_boorpuntenIntekenen\watergangen.shp"
# bgt = "C:\Users\elma\Documents\GitHub\MAP_eline\Algemeen\GIS\Tooltesting\TestData\Tool_d1_boorpuntenIntekenen\\bgt.shp"
# monstervak_veld = "mv_code"
# monstervakken_doelbestand = "C:\Users\elma\Documents\GitHub\MAP_eline\Algemeen\GIS\Tooltesting\TestData\Tool_d1_boorpuntenIntekenen\Elma\monstervakken_jan2019_{0}.shp".format(nummer_test)
# aantal_boorpunten = 10
# minimale_afstand = 0.1
# doelbestand_boorpunten = "C:\Users\elma\Documents\GitHub\MAP_eline\Algemeen\GIS\Tooltesting\TestData\Tool_d1_boorpuntenIntekenen\Elma\\boorpunten_jan2019_{0}.shp".format(nummer_test)
# # input lijnen looptroute
# input_fl_route = 'C:\Users\elma\Documents\GitHub\MAP_eline\Algemeen\GIS\Tooltesting\TestData\Tool_d1_boorpuntenIntekenen\Elma\\routelijn.shp'
#--------------------------------

# input lijnen monstervakken
input_fl_lijnen = watergang

# field name van het veld waarin de ID van de looproute is meegegeven
id_veld = 'id'

arcpy.AddMessage("Inlezen bestanden...")

# ------------ Inlezen monstergangen DISSOLVE --------------------
# Clip de watergangen met de bgt and dissolve op monstervak
temp_clip = "in_memory\clip_watergangen"
clipped = arcpy.Clip_analysis(watergang, bgt, temp_clip)
dissolved = arcpy.Dissolve_management(temp_clip, monstervakken_doelbestand, monstervak_veld, "",
                                      "MULTI_PART", "DISSOLVE_LINES")

# Create memcollection from dissolved lines
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

# ------------------ Inlezen lijnen LOOPROUTE ----------------
# inlezen looproute shape naar collection
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

# ------------------- Inlezen monstergangen as collection------------------------------
# inlezen monstervakken shapefile naar collection
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

arcpy.AddMessage("Bestanden ingelezen")

# ------------------ Generate points on DISSOLVED lines -----------------
arcpy.AddMessage("Genereer boorpunten per monstervak...")
# Create points on dissolved lines
point_col_boorpunten = get_points_on_line_amount(collection, copy_fields=[monstervak_veld],
                                                 default_amount=aantal_boorpunten)
arcpy.AddMessage("Boorpunten per monstervak gegenereerd")


# ------------- TOOL looproute overzetten naar monstervakken: output LIJNEN-----------
# aanroepen tool
arcpy.AddMessage('Looproute overzetten naar monstervakken...')
arcpy.AddMessage('Bezig met uitvoeren van get_vertices_with_index...')

point_col_looproute = get_vertices_with_index(line_col_route, id_veld)

arcpy.AddMessage('Bezig met uitvoeren van get_index_number_from_points...')

line_col_lijnen_indexed = get_index_number_from_points(line_col_lijnen, point_col_looproute, 'vertex_nr')

# wegschrijven tool resultaat
spatial_reference = arcpy.Describe(input_fl_lijnen).spatialReference

temp_num_monster = "in_memory\\num_monster"
output_name = os.path.basename(temp_num_monster).split('.')[0]
output_dir = os.path.dirname(temp_num_monster)

output_fl_lines = arcpy.CreateFeatureclass_management(output_dir, output_name, 'Polyline',
                                                      spatial_reference=spatial_reference)

arcpy.AddField_management(output_fl_lines, 'route_id', 'SHORT')
arcpy.AddField_management(output_fl_lines, 'volgnr', 'DOUBLE', 8, 2)
arcpy.AddField_management(output_fl_lines, 'richting', 'SHORT')

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

arcpy.AddMessage("Looproute overgezet naar monstervakken")

# ----------------- TOOL hernummer punten ---------------
arcpy.AddMessage("Hernummer de punten...")
# lijnendata met nummering erin: line_col_lijnen_indexed
# puntendata te hernummeren: point_col_boorpunten

# Initializering:
line_nr_field = 'volgnr'
point_nr_field = 'hernummer'
start_nr = 1

# Aanroepen tool: hernummer punten ahv looproute
point_col_hernummerd = number_points_on_line_boorpunten(line_col_lijnen_indexed, point_col_boorpunten, line_nr_field,
                                             point_nr_field, start_nr)

# -------------- Willekeurig verspreiden van de boorpunten -------------
# Zet pointcol om naar shapefile, zodat later arcpy tools toegepast kunnen  worden.
temp_points = "in_memory\\temp_points"
spatial_reference = arcpy.Describe(watergang).spatialReference
output_name = os.path.basename(temp_points).split('.')[0]
output_dir = os.path.dirname(temp_points)
fields = point_col_hernummerd[0]['properties'].keys()

output_points = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

for field in fields:
    if field == monstervak_veld: # dit bestaat nu niet meer, ergens anders toevoegen
        arcpy.AddField_management(output_points, field, "STRING", field_length=50)
    if field == 'nummer':
        arcpy.AddField_management(output_points, field, "SHORT")

dataset = arcpy.InsertCursor(output_points)

for p in point_col_hernummerd.filter():
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point

    for field in fields:
        if field == monstervak_veld:  # dit bestaat nu niet meer, ergens anders toevoegen
            row.setValue(field, p['properties'].get(field, None))
        if field == 'nummer':
            row.setValue(field, p['properties'].get(field, None))

    dataset.insertRow(row)

arcpy.AddMessage("Punten hernummerd")

arcpy.AddMessage("Punten willekeurig verplaatsen binnen monstervak...")
# Maak haakse lijnen op de locatie van de gemaakte punten
haakselijnen_col = get_haakselijnen_on_points_on_line(collection, point_col_hernummerd, [monstervak_veld, 'nummer', 'hernummer'], default_length=100)

# Create temporary feature class from haakse lijnen
temp_haakselijnen = "in_memory\\temp_haaks"

output_name = os.path.basename(temp_haakselijnen).split('.')[0]
output_dir = os.path.dirname(temp_haakselijnen)
fields = haakselijnen_col[0]['properties'].keys()

output_haakselijnen = arcpy.CreateFeatureclass_management(output_dir,
                                                output_name, 'POLYLINE',
                                                spatial_reference=spatial_reference)
for field in fields:
    if field == monstervak_veld:
        arcpy.AddField_management(output_haakselijnen, field, "STRING", field_length=50)
    if field == 'hernummer':
        arcpy.AddField_management(output_haakselijnen, field, "SHORT")

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
        if field == monstervak_veld:
            row.setValue(field, l['properties'].get(field, None))
        if field == 'hernummer':
            row.setValue(field, l['properties'].get(field, None))

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

# Random point op elke haakse lijn
boorpunten_col = get_points_on_line_random(haakselijnen_select_col, [monstervak_veld, 'hernummer'],
                                           default_offset=minimale_afstand)
arcpy.AddMessage("Punten willekeurig verplaatst binnen monstervak")

# ------------- wegschrijven boorpunten naar shapefile ---------------
# Wegschrijven boorpunten als shapefile
arcpy.AddMessage("Boorpunten wegschrijven...")
output_name = os.path.basename(doelbestand_boorpunten).split('.')[0]
output_dir = os.path.dirname(doelbestand_boorpunten)
same_monstervak = ''
fields = boorpunten_col[0]['properties'].keys()

output_boorpunten = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT',
                                                spatial_reference=spatial_reference)

arcpy.AddField_management(output_boorpunten, "hernummer", "SHORT")
arcpy.AddField_management(output_boorpunten, "mv_code", "STRING", field_length=50)
arcpy.AddField_management(output_boorpunten, "bp", "STRING", field_length=50)
arcpy.AddField_management(output_boorpunten, "mv_bp", "STRING", field_length=50)

dataset = arcpy.InsertCursor(output_boorpunten)

for p in boorpunten_col.filter():
    # Bepaal de boorpuntnummer per monstervak (bv. 01, 02, 03 etc ... 10)
    if same_monstervak == p['properties'][monstervak_veld]:
        boorpuntnummer += 1
        boorpunt_text = '%02d'%boorpuntnummer
    else:
        same_monstervak = p['properties'][monstervak_veld]
        boorpuntnummer = 1
        boorpunt_text = '%02d'%boorpuntnummer

    bp_mv_text = same_monstervak + '_' + boorpunt_text

    # Wegschrijven van de gegevens naar shapefile
    row = dataset.newRow()
    point = arcpy.Point()
    point.X = p['geometry']['coordinates'][0]
    point.Y = p['geometry']['coordinates'][1]
    row.Shape = point
    for field in fields:
        if field == monstervak_veld:
            row.setValue(field, p['properties'].get(field, None))
        if field == 'hernummer':
            row.setValue(field, p['properties'].get(field, None))
    row.setValue('bp', boorpunt_text)
    row.setValue('mv_bp', bp_mv_text)
    dataset.insertRow(row)

arcpy.AddMessage("Boorpunten weggeschreven")
arcpy.AddMessage("Output bestand boorpunten: " + doelbestand_boorpunten)
arcpy.AddMessage("Output bestand monstervakken (dissolved): " + monstervakken_doelbestand)

arcpy.Delete_management("in_memory")

add_result_to_display(output_boorpunten, output_name)
add_result_to_display(monstervakken_doelbestand, output_name)

