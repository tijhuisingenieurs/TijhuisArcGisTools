# LIBRARIES FOR TOOL
import arcpy
import fiona
from shapely import affinity
from shapely.geometry import Point, LineString, shape, MultiPolygon, Polygon, MultiLineString
from gistools.tools.connect_start_end_points import get_points_on_line
from gistools.tools.dwp_tools import get_haakselijnen_on_points_on_line
from matplotlib.collections import PatchCollection
import matplotlib.pyplot as plt
from gistools.utils.collection import MemCollection
from collections import OrderedDict
import numpy



# FUNCTIONS
def create_polygon(list_x, list_y):
    """
    Function to create a tuple polygon based on two lists with x and y coordinates.

    list_x: list with x coordinates
    list_y: list with y coordinates
    """

    polygon = list(zip(list_x, list_y))

    return polygon


def all_same(items):
    """
    function to check if all items in list are the same. Input is list
    """
    return all(x == items[0] for x in items)


def closest(lst, K):
    """
    Find closest K value in a list
    """
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]

### CODE

#TI19340_Te_peilen_Waterlopen_Tuitjenhorn.shp
#waterloop_ingewikkeld.shp
#TI19340_Te_peilen_Waterlopen_Waarland.shp
waterloop_lines = fiona.open("C:/Users/tom/_Python_projects/HHNK_profielen_intekenen/test/TI19340_Te_peilen_Waterlopen_Waarland.shp")

#waterdelen openen (importeren)
#waterdeel_selection_test.shp
#waterdeel_ingewikkeld.shp
#waterdeel_waarland.shp
shapes = MultiPolygon([shape(pol['geometry']) for pol in fiona.open("C:/Users/tom/_Python_projects/HHNK_profielen_intekenen/test/waterdeel_waarland.shp")])

plt.figure(figsize=(20,20))

#fixed distance between points
fixed_distance = 1.0
fixed_distance_profile = 50.0

#looproutes openen (importeren)
#waterloop_ingewikkeld.shp
#TI19340_Te_peilen_Waterlopen_Tuitjenhorn.shp
# #I19340_Te_peilen_Waterlopen_Waarland.shp
for waterloop_index, pol in enumerate(fiona.open("C:/Users/tom/_Python_projects/HHNK_profielen_intekenen/test/TI19340_Te_peilen_Waterlopen_Waarland.shp")):
    test_col = MemCollection(geometry_type='LineString')
    records = []
    records.append(pol)
    test_col.writerecords(records)
    waterlijn = LineString(test_col[0]['geometry']['coordinates'])

    # functie 1: punten intekenen op lijn
    point_col = get_points_on_line(test_col,
                                   fixed_distance=fixed_distance,
                                   all_lines=True)

    # functie 2: haakse lijnen tekenen
    haakse_lijnen = get_haakselijnen_on_points_on_line(test_col, point_col, default_length=200.0)

    # plot haakse lijnen
    for shape in shapes:
        if shape.intersects(waterlijn):
            print("ID:", waterloop_index)

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
                    # polyline = LineString(list(shape.exterior.coords))
                    # haakse_lijn.intersection(polyline)
                    # x, y = shape.intersection(haakse_lijn).coords.xy

                    multiline_intersect = shape.intersection(haakse_lijn)
                    # x,y = multiline_intersect[0].coords.xy
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

                # cehck to see if haakse lijn has a centroid point (which it should have)
                if not haakse_lijn.centroid.xy:
                    raise Exception("no centroid point for intersection")

                # searches two intersects closest to the centroid point
                intersect_1 = []
                intersect_2 = []
                for intersection in intersections_x:
                    if all_same(intersection):
                        intersect_1.append(intersection[0])
                        intersect_2.append(intersection[0])
                    else:
                        for i, x_coordinate in enumerate(intersection):
                            if round(x_coordinate, 2) == round(haakse_lijn.centroid.xy[0][0], 2):
                                intersect_1.append(intersection[i - 1])
                                intersect_2.append(intersection[i + 1])

                for intersection in intersections_y:
                    if all_same(intersection):
                        intersect_1.append(intersection[0])
                        intersect_2.append(intersection[0])
                    else:
                        for i, y_coordinate in enumerate(intersection):
                            if round(y_coordinate, 2) == round(haakse_lijn.centroid.xy[1][0], 2):
                                intersect_1.append(intersection[i - 1])
                                intersect_2.append(intersection[i + 1])

                # calculate distance between intersect points
                try:
                    distance = Point(intersect_1).distance(Point(intersect_2))
                    distance_list.append(distance)
                except:
                    print("no distance between points")

                # plot haakse lijnen
                # plt.plot(line_list_x, line_list_y, c='orange', zorder=0)
                # plt.scatter(intersections_x, intersections_y)
                # x, y = shape.exterior.xy

                # plot BGT waterdelen
                # plt.plot(x, y)
                # plt.show()

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
                    slice = distance_list[i:int(i+profile_distance_transformed) / 2]
                else:
                    slice = distance_list[i:int(i+profile_distance_transformed)]
                mean_distance = sum(slice)/len(slice)
                closest_point = closest(slice, mean_distance)
                idx = distance_list.index(closest_point)

                if len(slice) < 10 and i != 0: # make sure that if end of line is smaller than 10 meter, no point is drawn
                    pass
                elif len(slice) < 10 and i == 0:  # set minimum length of total line
                    pass
                elif i == 0 and len(distance_list) >= 50:
                    idx = 25
                    idx_list.append(idx)
                elif i == 0 and len(distance_list) < 50:
                    idx = len(distance_list) / 2
                    idx_list.append(idx)
                elif idx < 10 and len(distance_list) > (10 + idx): #if the best intersect of the line is within the first 15 meters:
                    idx = idx + 10
                    idx_list.append(idx) # add 10 meter
                elif len(distance_list)- idx < 10 and len(distance_list) > (idx - 10): # if best intersect is 10 meters or shorter from end of line
                    idx = idx - 10
                    idx_list.append(idx)
                else:
                    idx_list.append(idx)

                i += int(profile_distance_transformed)
                # print("mean:", mean_distance)
                print("closest:", closest_point, "mean:", mean_distance, "index:", idx)

            point_list_x = []
            point_list_y = []
            for item in idx_list:
                if idx_list > 0:
                    point_list_x.append(point_col[item]['geometry']['coordinates'][0])
                    point_list_y.append(point_col[item]['geometry']['coordinates'][1])
            plt.scatter(point_list_x, point_list_y, c='r', zorder=15, s=50)

            # calculate BGT waterdelen
            for shape in shapes:
                x,y = shape.exterior.xy

              #plot BGT waterdelen
                plt.plot(x,y, c='b', zorder=5)

                # x,y = shape.interiors[0].xy
                #
                # # plot BGT waterdelen
                # plt.plot(x, y, c='b', zorder=5)



            # plot waterlooplijnen
            for line in waterloop_lines:
                line_list_x = []
                line_list_y = []
                for i in range(len(line['geometry']['coordinates'])):
                    line_list_x.append(line['geometry']['coordinates'][i][0])
                    line_list_y.append(line['geometry']['coordinates'][i][1])
                    plt.plot(line_list_x, line_list_y, zorder=10)

plt.show()

### OVERIG

# plot profielpunten
# point_list_x = []
# point_list_y = []
# for i in range(len(point_col)):
#     point_list_x.append(point_col[i]['geometry']['coordinates'][0])
#     point_list_y.append(point_col[i]['geometry']['coordinates'][1])
# plt.scatter(point_list_x, point_list_y)