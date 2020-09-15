# LIBRARIES FOR TOOL
import arcpy
import fiona
from shapely import affinity
from shapely.geometry import Point, LineString, shape
from shapely.ops import cascaded_union

# open document with all center points of old shapes
point_data_in = arcpy.GetParameterAsText(0)  # Point(0, 0)  # radial sweep centre point
input_lines_in = arcpy.GetParameterAsText(1)
output = arcpy.GetParameterAsText(2)

# PARAMETERS
sweep_res = arcpy.GetParameterAsText(3)  # sweep resolution (degrees)
sweep_radius = arcpy.GetParameterAsText(4)  # sweep radius
buffer_radius = arcpy.GetParameterAsText(5)  # radius of buffer for intersection

point_data = fiona.open(point_data_in)
input_lines = fiona.open(input_lines_in)

# permanent lists needed for final output:
min_dist_id_list = []
min_dist_list = []

# checks whether data is Point of LineString input and converts LineString layer to Point is necessary
if point_data[0]['geometry']['type'] == 'Point':
    arcpy.AddMessage('Point = True')
    pass
elif point_data[0]['geometry']['type'] == 'LineString':
    arcpy.AddMessage('LineString = True')
    raise ValueError('Geen geldige feature - input feature dient punt te zijn')
else:
    raise ValueError('Geen geldige feature - input feature dient punt te zijn')


####### CREATE RADIAL SWEEP TOOL #######


for i in range(len(point_data)):
    x, y = point_data[i]['geometry']['coordinates']
    focal_pt = Point(x, y)

    # create the radial sweep lines
    line = LineString([(focal_pt.x, focal_pt.y),
                       (focal_pt.x, focal_pt.y + float(sweep_radius))])

    sweep_lines = [affinity.rotate(line, i2, (focal_pt.x, focal_pt.y)) \
                   for i2 in range(0, 360, int(sweep_res))]

    radial_sweep = cascaded_union(sweep_lines)
    # print i, radial_sweep (check if radial sweep works)

    ####### USE RADIAL SWEEP TOOL ON NEAR FEATURES #######

    # load the input lines and combine them into one geometry
    input_shapes = [shape(f['geometry']) for f in input_lines]
    all_input_lines = cascaded_union(input_shapes)

    perimeter = []
    # traverse each radial sweep line and check for intersection with input lines
    for radial_line in radial_sweep:
        inter = radial_line.intersection(all_input_lines)

        if inter.type == "MultiPoint":
            # radial line intersects at multiple points
            inter_dict = {}
            for inter_pt in inter:
                inter_dict[focal_pt.distance(inter_pt)] = inter_pt
            # save the nearest intersected point to the sweep centre point
            perimeter.append(inter_dict[min(inter_dict.keys())])

        if inter.type == "Point":
            # radial line intersects at one point only
            perimeter.append(inter)

        if inter.type == "GeometryCollection":
            # radial line doesn't intersect, so skip
            pass

    # combine the nearest perimeter points into one geometry
    solution = cascaded_union(perimeter)
    arcpy.AddMessage('checking input feature point ID {}'.format(i))

    ####### USE RADIAL SWEEP TOOL ON NEAR FEATURES #######

    # create list with all distances for focal_pt
    distance_list = []
    if solution.type == "MultiPoint":
        for distance in range(len(solution)):
            distance_test = focal_pt.distance(solution[distance])
            distance_list.append(distance_test)

        # select smallest distance and index from distance_list
        closest_id = distance_list.index(min(distance_list))
        min_dist = min(distance_list)
        min_dist_list.append(min_dist)
        # print distance_list.index(min(distance_list))
        arcpy.AddMessage("{} meter is lowest distance to near feature".format(round(min(distance_list)),2))

        # convert multipoint to individual points
        individual_points = [(pt.x, pt.y) for pt in solution]
        closest_point = Point(individual_points[closest_id])

    else:
        closest_point = solution
        min_dist = focal_pt.distance(solution)
        min_dist_list.append(min_dist)

    ####### BUFFER AND INTERSECT #######

    # create buffer of 0.1 meter around point
    buffer_x = closest_point.buffer(float(buffer_radius))

    # test for intersection
    closest_shape = {}
    for i in range(len(input_lines)):
        input_line = LineString(input_lines[i]['geometry']['coordinates'])
        if buffer_x.intersects(input_line):
            arcpy.AddMessage('intersect with near feature ID {}'.format(i))
            min_dist_id_list.append(i)
            filter_test = input_lines[input_lines[0]['id'] == u'{}'.format(i)]
            closest_shape = input_line
        else:
            pass
            # print 'no intersect with {}'.format(i)

arcpy.AddMessage("..Analysing completed")

####### WRITING NEAR FEATURE SHAPEFILE #######
arcpy.AddMessage("..Updating attribute table")

idx = 0

# writes extra columns
with fiona.open(point_data_in, 'r') as source:
    source_schema = source.schema
    source_schema['properties']['min_id'] = 'float'
    source_schema['properties']['min_dist'] = 'float'

    with fiona.open(
            output, 'w',
            crs_wkt=source.crs_wkt,
            driver=source.driver,
            schema=source_schema,
    ) as sink:
        for f in source:
            if idx < len(min_dist_id_list):
                a = min_dist_id_list[idx]
                b = min_dist_list[idx]
                idx = idx + 1
            else:
                pass

            f['properties'].update(min_id=a,
                                   min_dist=b,
                                   )
            sink.write(f)

arcpy.AddMessage("Successfully completed run")

