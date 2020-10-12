# Creates points on lines at a specified distance, percentage, or
# interval using a fixed or field-based value. All polyline fields
# are included in the output Point feature class. Points can be
# created starting from the beginning, or end of the line.

import arcpy
import random
from utils.addresulttodisplay import add_result_to_display

arcpy.env.overwriteOutput = True
arcpy.env.qualifiedFieldNames = False

polyline = arcpy.GetParameterAsText(0)
choice = str(arcpy.GetParameterAsText(1))
start_from = str(arcpy.GetParameterAsText(2))
use_field_for_value = str(arcpy.GetParameterAsText(3))
field_with_value = str(arcpy.GetParameterAsText(4))
distance = arcpy.GetParameter(5)  #percentage/distance/count
representative_distance = arcpy.GetParameter(6)
start_distance = arcpy.GetParameter(7)
end_points = str(arcpy.GetParameterAsText(8))
output = arcpy.GetParameterAsText(9)

# Test script without GUI
# polyline = './testdata/input/Testdata_watergangen.shp'
# choice = "AANTAL RANDOM"
# start_from = "BEGINNING"
# use_field_for_value = "NO"
# field_with_value = None
# distance = 4
# representative_distance = False
# start_distance = None
# end_points = "NO"
# output = './testdata/output/2_a5.shp'

if start_distance:
    start_distance = float(start_distance)

distance = float(distance)
spatial_ref = arcpy.Describe(polyline).spatialReference

mem_point = arcpy.CreateFeatureclass_management("in_memory", "mem_point", "POINT", "", "DISABLED", "DISABLED", spatial_ref)
arcpy.AddField_management(mem_point, "LineOID", "LONG")
arcpy.AddField_management(mem_point, "Value", "FLOAT")

result = arcpy.GetCount_management(polyline)
features = int(result.getOutput(0))

arcpy.SetProgressor("step", "Creating Points on Lines...", 0, features, 1)

search_fields = ["SHAPE@", "OID@"]
insert_fields = ["SHAPE@", "LineOID", "Value"]

if use_field_for_value == "YES":
    search_fields.append(field_with_value)

reverse_line = False
if start_from == "EINDE":
    reverse_line = True

with arcpy.da.SearchCursor(polyline, (search_fields)) as search:
    with arcpy.da.InsertCursor(mem_point, (insert_fields)) as insert:
        for row in search:
            try:
                line_geom = row[0]
                length = float(line_geom.length)
                oid = str(row[1])
                start = arcpy.PointGeometry(line_geom.firstPoint)
                end = arcpy.PointGeometry(line_geom.lastPoint)

                if representative_distance:
                    start_distance = distance / 2

                if start_distance:
                    count = start_distance
                else:
                    count = distance

                if reverse_line == True:
                   reversed_points = []
                   for part in line_geom:
                       for p in part:
                           reversed_points.append(p)

                   reversed_points.reverse()
                   array = arcpy.Array([reversed_points])
                   line_geom = arcpy.Polyline(array, spatial_ref)

                if use_field_for_value == "YES":
                    count = float(row[2])
                    distance = float(row[2])

                ################################################################

                if choice == "AFSTAND (1 PUNT)":
                    point = line_geom.positionAlongLine(count, False)
                    insert.insertRow((point, oid, count))

                elif choice == "AANTAL":
                    point_iterator = 0
                    point_interval = length / distance
                    while point_iterator <= distance - 1:
                        start_point = start_distance if start_distance else 0

                        if point_iterator == 0:
                            point = line_geom.positionAlongLine(0 + start_point, False)
                        else:
                            point = line_geom.positionAlongLine((point_interval * point_iterator) + start_point, False)

                        insert.insertRow((point, oid, count))
                        point_iterator += 1

                elif choice == "AANTAL RANDOM":
                    int_length = int(round(length))
                    random_points = random.sample(range(int_length), int(distance))
                    for random_point in random_points:
                        point = line_geom.positionAlongLine(random_point, False)
                        insert.insertRow((point, oid, count))

                elif choice == "PERCENTAGE (1 PUNT)":
                    point = line_geom.positionAlongLine((count/100), True)
                    insert.insertRow((point, oid, count))

                elif choice == "INTERVAL OBV AFSTAND":
                    while count <= length:
                        point = line_geom.positionAlongLine(count, False)
                        insert.insertRow((point, oid, count))

                        count += distance

                elif choice == "INTERVAL OBV PERCENTAGE":
                    percentage = float(count)
                    total_runs = int(100.0 / percentage)

                    run = 1
                    while run <= total_runs:
                        current_percentage = float((percentage * run) / 100.0)
                        point = line_geom.positionAlongLine(current_percentage, True)

                        insert.insertRow((point, oid, current_percentage))

                        run += 1

                elif choice == "START/EINDPUNTEN":
                    insert.insertRow((start, oid, 0))
                    insert.insertRow((end, oid, length))

                ################################################################

                if end_points == "START":
                    insert.insertRow((start, oid, 0))

                elif end_points == "EINDE":
                    insert.insertRow((end, oid, length))

                elif end_points == "BEIDE":
                    insert.insertRow((start, oid, 0))
                    insert.insertRow((end, oid, length))

                arcpy.SetProgressorPosition()

            except Exception as e:
                arcpy.AddMessage(str(e.message))


                ################################################################


line_keyfield = str(arcpy.ListFields(polyline, "", "OID")[0].name)

mem_point_fl = arcpy.MakeFeatureLayer_management(mem_point, "Points_memory")

arcpy.AddJoin_management(mem_point_fl, "LineOID", polyline, line_keyfield)

if "in_memory" in output:
    arcpy.SetParameter(8, mem_point_fl)

else:
    arcpy.CopyFeatures_management(mem_point_fl, output)
    add_result_to_display(mem_point_fl, output)

    arcpy.Delete_management(mem_point)
    arcpy.Delete_management(mem_point_fl)

arcpy.ResetProgressor()
arcpy.GetMessages()
