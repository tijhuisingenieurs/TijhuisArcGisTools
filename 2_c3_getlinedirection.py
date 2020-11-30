import sys
import os
import arcpy
import fiona
from utils.addresulttodisplay import add_result_to_display
from collections import OrderedDict

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

from gistools.utils.collection import MemCollection
from gistools.tools.validatie import get_angles
from gistools.utils.geometry import TLine

# input for testing or using the script without arcmap
# waterganglijn = './testdata/input/Testdata_watergangen.shp'
# # profiellijn = './testdata/input/Testdata_dwarsprofielen.shp'
# profiellijn = './testdata/input/dataset_met_geflipte_lijnen.shp'
# wrong_angle = 'false'
# output = './testdata/output/2_c2_lines_w_wrong_direction_3.shp'

# Input for ArcMap
waterganglijn = arcpy.GetParameterAsText(0)
profiellijn = arcpy.GetParameterAsText(1)
wrong_angle = arcpy.GetParameterAsText(2)
output = arcpy.GetParameterAsText(3)

wrong_angle = str(wrong_angle)

arcpy.AddMessage('waterlijnen = ' + str(waterganglijn))
arcpy.AddMessage('profiellijnen = ' + str(profiellijn))
arcpy.AddMessage('Verkeerde richting in output = ' + str(wrong_angle))
arcpy.AddMessage('output = ' + str(output))

arcpy.env.overwriteOutput = True

# waterway_line = fiona.open(waterganglijn)
# profile_line = fiona.open(profiellijn)

# check which profile_lines have the correct/incorrect angle (profile line should start left from waterway based on
# directions)
p_index_list = []

# waterway_line = arcpy.SearchCursor(waterganglijn)
# profile_line = arcpy.SearchCursor(profiellijn)

wline_col = MemCollection(geometry_type='MultiLinestring')
records = []
rows = arcpy.SearchCursor(waterganglijn)
fields = arcpy.ListFields(waterganglijn)
point = arcpy.Point()

pline_col = MemCollection(geometry_type='MultiLinestring')
precords = []
prows = arcpy.SearchCursor(profiellijn)
pfields = arcpy.ListFields(profiellijn)
ppoint = arcpy.Point()

# vullen collection
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

wline_col.writerecords(records)

# vullen collection
for prow in prows:
    pgeom = prow.getValue('SHAPE')
    pproperties = OrderedDict()
    for pfield in pfields:
        if pfield.name.lower() != 'shape':
            pproperties[pfield.name] = prow.getValue(pfield.name)

    precords.append({'geometry': {'type': 'MultiLineString',
                                  'coordinates': [[(ppoint.X, ppoint.Y) for
                                                   ppoint in pline] for pline in pgeom]},
                     'properties': pproperties})

pline_col.writerecords(precords)



for wline in wline_col:
    for i, _ in enumerate(wline['geometry']['coordinates'][0]):
        new_geom = []
        i_last = len(wline['geometry']['coordinates'][0]) - 1
        if i != i_last:
            new_geom.append(wline['geometry']['coordinates'][0][0 + i])
            new_geom.append(wline['geometry']['coordinates'][0][1 + i])

            w_linestring = TLine(new_geom)
            wline_angle = w_linestring.get_line_angle_with_negatives()

            for pidx, pline in enumerate(pline_col):
                p_linestring = TLine(pline['geometry']['coordinates'][0])
                pline_angle = p_linestring.get_line_angle_with_negatives()

                if w_linestring.intersects(p_linestring):
                    w_angle = wline_angle
                    p_angle = pline_angle
                    diff_angle = (w_angle - p_angle) if (w_angle - p_angle) >= 0 else (w_angle - p_angle) + 360
                    if wrong_angle == 'true':
                        arcpy.AddMessage('FID: {}, w_angle: {}, p_angle: {}, diff_angle: {}'
                                         .format(pidx, p_angle, p_angle, diff_angle))
                        if diff_angle < 180:
                            p_index_list.append(pidx)
                    if wrong_angle == 'false':
                        arcpy.AddMessage('FID: {}, w_angle: {}, p_angle: {}, diff_angle: {}'
                                         .format(pidx, p_angle, p_angle, diff_angle))
                        if diff_angle >= 180:
                            p_index_list.append(pidx)

profiles_to_copy = tuple(dict.fromkeys(p_index_list))
arcpy.AddMessage('Profielen met de volgende FIDs zijn gevonden: {}'.format(profiles_to_copy))
print(profiles_to_copy)

# copy correct/incorrect profile lines to new feature
featureLayer = arcpy.MakeFeatureLayer_management(profiellijn, "featureLayer")
if not profiles_to_copy:
    arcpy.AddMessage('Geen foutieve profielen gevonden')
else:
    query = "\"FID\" IN {}".format(profiles_to_copy)
    mem_points = arcpy.management.SelectLayerByAttribute(featureLayer,"ADD_TO_SELECTION",query)
    output_fl = arcpy.CopyFeatures_management(mem_points, output)

    add_result_to_display(output_fl, output)


