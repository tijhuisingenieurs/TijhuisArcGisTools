import arcpy
import fiona
import sys
import os.path
from shapely.geometry import Point, LineString, shape, MultiPolygon, mapping

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))

# internal library
from gistools.utils.collection import MemCollection
from gistools.tools.connect_start_end_points import get_points_on_line
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from gistools.tools.validatie import get_angles
from gistools.utils.geometry import TLine, create_polygon
from gistools.utils.lists import all_same, closest

# input for testing or using the script without arcmap
# waterloop_lines = './testdata/input/Testdata_watergangen.shp'
# shapes = './testdata/input/BGT.shp'
# output_point = './testdata/output/2_e1_output_punten.shp'
# output_line = './testdata/output/2_e1_output_lijnen.shp'
# fixed_distance_profile_int = 50.0
# start_distance = 15
# profile_width = 20
# label_north_south = 'west'
# label_west_east = 'north'

# arcpy.env.overwriteOutput = True

# Input for ArcMap
waterloop_lines = arcpy.GetParameterAsText(0)
shapes = arcpy.GetParameterAsText(1)
output_point = arcpy.GetParameterAsText(2)
output_line = arcpy.GetParameterAsText(3)

# values for input
fixed_distance_profile_int = arcpy.GetParameterAsText(4)
start_distance = arcpy.GetParameterAsText(5)
profile_width = arcpy.GetParameterAsText(6)

label_north_south = arcpy.GetParameterAsText(7)
label_west_east = arcpy.GetParameterAsText(8)

arcpy.AddMessage(str(label_north_south))
arcpy.AddMessage(str(label_west_east))

# check voor bestandeninput
arcpy.AddMessage('waterlijnen = ' + str(waterloop_lines))
arcpy.AddMessage('watervlakken = ' + str(shapes))
arcpy.AddMessage('lengte waterweg per te plaatsen dwarsprofiel (m) = ' + str(fixed_distance_profile_int))
arcpy.AddMessage('startpositie eerste dwarsprofiel (m) = ' + str(start_distance))
arcpy.AddMessage('lengte haakse lijn dwarsprofiel (m) = ' + str(profile_width))

# open waterway lines (waterloop lines) and BGT water shapes (shapes)
waterloop_lines = fiona.open(waterloop_lines)
shapes = MultiPolygon([shape(pol['geometry']) for pol in fiona.open(shapes)])

#fixed distance between points
fixed_distance = 1.0 # units in meters
start_distance = int(start_distance)
fixed_distance_profile = float(fixed_distance_profile_int)

# lists needed for collection
point_list = []
haakse_lijnen_list = []
angle_list = []
closest_point_list = []
actual_angle_list = []

arcpy.AddMessage('calculating best profile location based on average width of waterway')

for waterloop_index, lines in enumerate(waterloop_lines):
    line_col = MemCollection(geometry_type='LineString')
    records = []
    records.append(lines)
    line_col.writerecords(records)

    # determine angle of waterway
    line_col = get_angles(line_col)
    actual_angle = line_col[0]['properties']['feature_angle']
    if line_col[0]['properties']['feature_angle'] <= 45 or line_col[0]['properties']['feature_angle'] >=  135:
        angle_waterloop = 0
    else:
        angle_waterloop = 90

    waterlijn = LineString(line_col[0]['geometry']['coordinates'])

    # draw points on line
    point_col = get_points_on_line(line_col,
                                   fixed_distance=fixed_distance,
                                   all_lines=True)

    #draw perpendicular line per point
    haakse_lijnen = get_haakselijnen_on_points_on_line(line_col, point_col, default_length=200.0)

    # calculate best profile locations per waterway
    for shape in shapes:
        if shape.intersects(waterlijn):
            arcpy.AddMessage('water-line ID: {}'.format(waterloop_index))

            distance_list = []
            for i, line in enumerate(haakse_lijnen):
                line_list_x = []
                line_list_y = []

                intersections_x = []
                intersections_y = []

                for i in range(len(line['geometry']['coordinates'])):
                    line_list_x.append(line['geometry']['coordinates'][i][0])
                    line_list_y.append(line['geometry']['coordinates'][i][1])

                # create intersection of haakse lijn with waterdeel
                haakse_lijn = LineString(create_polygon(line_list_x, line_list_y))
                if shape.intersection(haakse_lijn).geom_type == "LineString":
                    x,y = shape.intersection(haakse_lijn).coords.xy
                elif shape.intersection(haakse_lijn).geom_type == "MultiLineString":

                    multiline_intersect = shape.intersection(haakse_lijn)
                    x = []
                    y = []
                    for i in range(len(multiline_intersect)):
                        x_sub,y_sub = multiline_intersect[i].coords.xy
                        x_sub = x_sub.tolist()
                        y_sub = y_sub.tolist()
                        x += x_sub
                        y += y_sub
                else:
                    continue

                intersections_x.append(x)
                intersections_y.append(y)

                # check to see if haakse lijn has a centroid point (which it should have)
                if not haakse_lijn.centroid.xy:
                    raise Exception("no centroid point for intersection")

                # searches two intersects closest to the centroid point
                intersect_1 = []
                intersect_2 = []
                for intersection in intersections_x:
                    if len(intersections_x[0]) < 3:
                        pass
                    if all_same(intersection):
                        intersect_1.append(intersection[0])
                        intersect_2.append(intersection[0])
                    else:
                        count = 0
                        for i, x_coordinate in enumerate(intersection):
                            if round(x_coordinate, 3) == round(haakse_lijn.centroid.xy[0][0], 3):
                                count += 1
                                if count == 1 and len(intersection) != (i + 1):
                                    intersect_1.append(intersection[i - 1])
                                    intersect_2.append(intersection[i + 1])

                for intersection in intersections_y:
                    if len(intersections_y[0]) < 3:
                        pass
                    elif all_same(intersection):
                        intersect_1.append(intersection[0])
                        intersect_2.append(intersection[0])
                    else:
                        count = 0
                        for i, y_coordinate in enumerate(intersection):
                            if round(y_coordinate, 3) == round(haakse_lijn.centroid.xy[1][0], 3):
                                count += 1
                                if count == 1 and len(intersection) != (i + 1):
                                    intersect_1.append(intersection[i - 1])
                                    intersect_2.append(intersection[i + 1])

                # calculate distance between intersect points
                try:
                    distance = Point(intersect_1).distance(Point(intersect_2))
                    distance_list.append(distance)
                except:
                    print("no distance between points")

            # transform distance to units for iteration purposes
            if fixed_distance_profile % fixed_distance == 0:
                profile_distance_transformed = fixed_distance_profile / fixed_distance
            else:
                profile_distance_transformed = (fixed_distance_profile / fixed_distance) + 1

            # while loop takes 25 distance from end of waterway
            i = 0
            idx_list = []
            while i < (len(distance_list)):
                if i == 0:
                    slice = distance_list[i:int(i+profile_distance_transformed)]
                else:
                    slice = distance_list[i:int(i+profile_distance_transformed)]
                    if len(slice) == int(profile_distance_transformed):
                        slice = distance_list[i+10:(int(i + profile_distance_transformed)-10)]
                mean_distance = sum(slice)/len(slice)
                closest_point = closest(slice, mean_distance)
                idx = distance_list.index(closest_point)

                skip = 0
                if len(slice) < 10 and i != 0:
                    skip = 1 # make sure that if end of line is smaller than 10 meter, no point is drawn
                elif len(slice) < 10 and i == 0:
                    skip = 1 # set minimum length of total line
                elif i == 0 and len(distance_list) >= 50:
                    idx = start_distance
                    idx_list.append(idx)
                elif i == 0 and len(distance_list) < 50:
                    idx = len(slice) / 2
                    idx_list.append(idx)
                elif len(distance_list) - idx < 10 and len(distance_list) > (idx - 10):  # if best intersect is 10 meters or shorter from end of line
                    idx = idx - 10
                    idx_list.append(idx)
                else:
                    idx_list.append(idx)

                i += int(profile_distance_transformed)
                # print("mean:", mean_distance)
                arcpy.AddMessage("mean width: {}, closest width: {}, index of closest (m): {}".format(closest_point, mean_distance, idx))

                if skip == 0:
                    if closest_point < 15:
                        closest_point_list.append(start_distance)
                    else:
                        closest_point_list.append(closest_point + 5)

            point_list_x = []
            point_list_y = []
            haakse_lijnen_final = []
            for item in idx_list:
                if idx_list > 0:
                    haakse_lijnen_final.append(LineString(haakse_lijnen[item]['geometry']['coordinates']))
                    point_list_x.append(point_col[item]['geometry']['coordinates'][0])
                    point_list_y.append(point_col[item]['geometry']['coordinates'][1])
                    point_list.append(Point(point_col[item]['geometry']['coordinates']))
                    angle_list.append(angle_waterloop)
                    actual_angle_list.append(actual_angle)


arcpy.AddMessage("..Calculating points completed")
arcpy.AddMessage("..Writing (profiles) points to shapefile")

schema_point = {
    'geometry': 'Point',
    'properties': {'DWPnr': 'int', 'DWPcode': 'str', "length": 'float'},
}

# Write a new Shapefile
with fiona.open(output_point, 'w', 'ESRI Shapefile', schema_point, crs_wkt=waterloop_lines.crs_wkt) as c:
    ## If there are multiple geometries, put the "for" loop here
    for e, point in enumerate(point_list):
        c.write({
            'geometry': mapping(point),
            'properties': {'DWPnr': e, 'DWPcode': "", "length" : closest_point_list[e]},
        })
c.close()

points_to_line = fiona.open(output_point)

#, length_field="length"
# Create perpendicular lines
arcpy.AddMessage("..Converting points to perpendicular lines")
haakse_lijnen_final = get_haakselijnen_on_points_on_line(waterloop_lines, points_to_line, default_length=int(profile_width))

# flip perpendicular lines based on the waterway orientation
arcpy.AddMessage("..Flip line direction based on label orientation")
haakse_lijnen_flipped = []
for i, line in enumerate(haakse_lijnen_final):

    # get angles of haakse lijnen
    haakse_lijnen_final = get_angles(haakse_lijnen_final)

    # add haakse lijnen to list
    haaks = LineString(haakse_lijnen_final[i]["geometry"]["coordinates"])
    haakse_lijnen_list.append(haaks)

    # put all the directions of the haakse_lijnen in the correct direction for north_south waterways
    if label_north_south == 'west':
        if angle_list[i] == 0:
            xy_id = haaks.coords.xy[0].index(min(haaks.coords.xy[0]))
            plot_point = Point(haaks.coords[xy_id])
            if Point(haakse_lijnen_final[i]["geometry"]["coordinates"][0]) == plot_point:
                haakse_lijnen_flipped.append(haaks)
            else:
                haaks = TLine(haaks)
                haaks_flipped = TLine(haaks.get_flipped_line())
                haakse_lijnen_flipped.append(haaks_flipped)
    elif label_north_south == 'east':
        if angle_list[i] == 0:
            xy_id = haaks.coords.xy[0].index(max(haaks.coords.xy[0]))
            plot_point = Point(haaks.coords[xy_id])
            if Point(haakse_lijnen_final[i]["geometry"]["coordinates"][0]) == plot_point:
                haakse_lijnen_flipped.append(haaks)
            else:
                haaks = TLine(haaks)
                haaks_flipped = TLine(haaks.get_flipped_line())
                haakse_lijnen_flipped.append(haaks_flipped)

    # put all the directions of the haakse_lijnen in the correct direction for east_west waterways
    if label_west_east == 'north':
        if angle_list[i] == 90:
            xy_id = haaks.coords.xy[1].index(max(haaks.coords.xy[1]))
            plot_point = Point(haaks.coords[xy_id])
            if Point(haakse_lijnen_final[i]["geometry"]["coordinates"][0]) == plot_point:
                haakse_lijnen_flipped.append(haaks)
            else:
                haaks = TLine(haaks)
                haaks_flipped = TLine(haaks.get_flipped_line())
                haakse_lijnen_flipped.append(haaks_flipped)
    elif label_west_east == 'south':
        if angle_list[i] == 90:
            xy_id = haaks.coords.xy[1].index(min(haaks.coords.xy[1]))
            plot_point = Point(haaks.coords[xy_id])
            if Point(haakse_lijnen_final[i]["geometry"]["coordinates"][0]) == plot_point:
                haakse_lijnen_flipped.append(haaks)
            else:
                haaks = TLine(haaks)
                haaks_flipped = TLine(haaks.get_flipped_line())
                haakse_lijnen_flipped.append(haaks_flipped)

# writing profile lines to ESRI shapefile
schema_line = {
    'geometry': 'LineString',
    'properties': {'DWPnr': 'int', 'DWPcode': 'str', 'angle': 'int', 'ActualAngle': 'int'},
}

arcpy.AddMessage("..Writing profiles (lines) to shapefile")

with fiona.open(output_line, 'w', 'ESRI Shapefile', schema_line, crs_wkt=waterloop_lines.crs_wkt) as c:
    for e, line in enumerate(haakse_lijnen_flipped):
        c.write({
            'geometry': mapping(line),
            'properties': {'DWPnr': e, 'DWPcode': "", 'angle': angle_list[e], 'ActualAngle': actual_angle_list[e]},
        })

arcpy.AddMessage("Successfully completed run")