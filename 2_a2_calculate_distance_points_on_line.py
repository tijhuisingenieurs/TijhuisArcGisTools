import arcpy
from utils.addresulttodisplay import add_result_to_display

input_dwarsprofiel = arcpy.GetParameterAsText(0)
dwp_rid = arcpy.GetParameterAsText(1)
input_hydrovak = arcpy.GetParameterAsText(2)
hydrovak_rid = arcpy.GetParameterAsText(3)
output = arcpy.GetParameterAsText(4)

# Test script without GUI
# input_dwarsprofiel = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/data/subselectie_dwp_punten.shp' # lijnen of punten
# input_hydrovak = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/data/subselectie_lengteprofiel.shp' # Lijnen
# output = 'C:/Users/tom/Documents/_Python_projects/punten_interpoleren/output/dwp_met_afstand.shp' # Lijnen of punten van input meetpunten
#
# distance_field = 'afstand'
# dwp_rid = 'hydrovak'
# hydrovak_rid = 'monstervak'

# functies
arcpy.env.overwriteOutput = True

mem_points = arcpy.CopyFeatures_management(input_dwarsprofiel, "in_memory/inMemoryFeatureClass")
arcpy.AddField_management(mem_points, 'afstand', "FLOAT")

def measure_along_line(line, line_rid, points, point_rid, distance, factor=1):
    """ Calculates distances at points along line from beginning of segment

    Required:
        line -- input line feature class
        line_rid -- unique id for line route id
        points -- points feature class
        point_rid -- id field that matches up with values in line_rid
        distance -- field that will contain distance calculations

    Optional:
        factor -- factor for conversion of units. Default is 1.  If feature
            class units are in meters and you want to convert to feet, use a
            factor of 3.28084.

    """
    # read all lines into dict
    with arcpy.da.SearchCursor(line, [line_rid, 'SHAPE@']) as rows:
        ld = dict(r for r in rows)

    # now get the measure along line for every point (measure distance is in same units of projection)
    with arcpy.da.UpdateCursor(points, [point_rid, 'SHAPE@', distance]) as rows:
        for r in rows:
            # first get associated line
            line = ld.get(r[0])
            if line:
                # now get measure distance from beginning of line to this point
                measure = line.measureOnLine(r[1], False) * factor
                r[2] = measure
                rows.updateRow(r)

    return points

dwp_afstand = measure_along_line(input_hydrovak, hydrovak_rid, mem_points, dwp_rid, 'afstand', factor=1)

output_fl = arcpy.CopyFeatures_management(dwp_afstand, output)
add_result_to_display(output_fl, output)



