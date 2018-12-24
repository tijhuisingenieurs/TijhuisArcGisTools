import logging
import os.path
import sys
import time
import numpy as np
import arcpy

from gistools.tools.calculate_slibaanwas_tool import get_profiel_middelpunt, create_buffer, \
    get_slibaanwas
from gistools.utils.collection import MemCollection
from utils.addresulttodisplay import add_result_to_display
from utils.arcgis_logging import setup_logging

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external'))
logging.basicConfig(level=logging.INFO)
setup_logging(arcpy)
log = logging.getLogger(__file__)
log.setLevel(logging.INFO)



# De functies om van arcgis naar python te gaan en terug
def from_shape_to_memcollection_points(input_shape):
    """Deze functie zet de shape met informatie om naar een punten collectie
    input: shapefile met meetpunten erin (het kan elke puntenshape zijn. De kolominfo wordt overgezet
    naar de properties en de coordinaten naar coordinates
    output: memcollection met deze punten erin"""

    # ---------- Omzetten van shapefile input naar memcollection----------------
    import arcpy
    # --- Initialize point collection
    point_col = MemCollection(geometry_type='MultiPoint')
    records_in = []
    rows_in = arcpy.SearchCursor(input_shape)
    fields_in = arcpy.ListFields(input_shape)
    # Fill the point collection
    for row in rows_in:
        geom = row.getValue('SHAPE')
        properties = {}
        for field in fields_in:
            if field.name.lower() != 'shape':
                if isinstance(field.name, unicode):
                    key = field.name.encode('utf-8')
                else:
                    key = field.name
                if isinstance(row.getValue(field.name), unicode):
                    value = row.getValue(field.name).encode('utf-8')
                else:
                    value = row.getValue(field.name)
                properties[key] = value
        # Voeg per punt de coordinaten en properties toe
        records_in.append({'geometry': {'type': 'Point',
                                        'coordinates': (geom.firstPoint.X, geom.firstPoint.Y)},
                           'properties': properties})
    # Schrijf de gegegevens naar de collection
    point_col.writerecords(records_in)
    return point_col

def write_list_to_collection(output_file, in_uit_combi, info_list):
    '''Hierin wordt de memcollectie (points) gevuld met de resultaten uit de get_slibaanwas tool
    Er wordt een shapefile gemaakt met per profiel het middelpunt en in GIS toegevoegd.
    input: output_dir (path van de folder waar de output wordt opgeslagen),
    in_uit_combi
    info_list
    output: shapefile (points) met de informatie weggeschreven in outputfolder, met de volgende kolommen:
    p_ids_in = profielnaam inpeiling,
    p_ids_uit = profielnaam uitpeiling,
    slibaanwas = m slibaanwas per m breedte,
    ps_breedte = breedte die mee is genomen voor het berekenen van het slib (m),
    ver_breed = verschil in breedte absoluut (inpeiling-uitpeiling) (m)
    datum_in,
    datum_uit,
    afstand =  deafstand tussen de middelpunten van de in- en uitpeiling,
    m_factor = aantal meters dat van de kant niet is meegenomen,
    error = geeft aan door welke error er geen berekening heeft plaatsgevonden. Null wanneer alles goed ging.
    '''

    import arcpy
    # specific file name and data
    # output_name = 'slibaanwas_{0}.shp'.format(np.random.random_integers(1,100))
    output_name = os.path.basename(output_file).split('.')[0]
    output_dir = os.path.dirname(output_file)
    output_file = arcpy.CreateFeatureclass_management(output_dir, output_name, 'POINT', spatial_reference=28992)
    arcpy.AddMessage('Outputname: ' + output_name)

    # op volgorde fields toevoegen en typeren
    arcpy.AddField_management(output_file, 'p_ids_in', "TEXT")
    arcpy.AddField_management(output_file, 'p_ids_uit', "TEXT")
    arcpy.AddField_management(output_file, 'slibaanwas', "DOUBLE")
    arcpy.AddField_management(output_file, 'ps_breed', "DOUBLE")
    arcpy.AddField_management(output_file, 'ver_breed', "DOUBLE")
    arcpy.AddField_management(output_file, 'datum_in', "TEXT")
    arcpy.AddField_management(output_file, 'datum_uit', "TEXT")
    arcpy.AddField_management(output_file, 'afstand', "DOUBLE")
    arcpy.AddField_management(output_file, 'm_factor', "DOUBLE")
    arcpy.AddField_management(output_file, 'error', "TEXT")

    dataset = arcpy.InsertCursor(output_file)

    # Geef de velden weer die aan de keys van de properties zijn
    fields = info_list.keys()
    fields.remove('geometrie')

    # Vul de shapefile in met de waardes
    for ind, p in enumerate(in_uit_combi):
        row = dataset.newRow()
        # Voeg de coordinaten toe aan het punt
        point = arcpy.Point()
        point.X = info_list['geometrie'][ind][0]
        point.Y = info_list['geometrie'][ind][1]

        # Voeg de properties toe aan de attribuuttable
        row.Shape = point
        row.setValue('p_ids_in', p[0])
        row.setValue('p_ids_uit', p[1])

        row.setValue('slibaanwas', info_list['slibaanwas'][ind])
        row.setValue('ps_breed', info_list['box_lengte'][ind])
        row.setValue('ver_breed', info_list['breedte_verschil'][ind])
        row.setValue('datum_in', info_list['datum_in'][ind])
        row.setValue('datum_uit', info_list['datum_uit'][ind])
        row.setValue('afstand', info_list['afstand'][ind])
        row.setValue('m_factor', info_list['meter_factor'][ind])
        row.setValue('error', info_list['errorwaarde'][ind])

        dataset.insertRow(row)
    # print('weggeschreven als file')
    arcpy.AddMessage('weggeschreven als file')
    #add_result_to_display(output_file, output_name)

# Read the parameter values
# 0: Meetpunten inpeiling (shapefile)
# 1: Meetpunten uitpeiling (shapefile)
# 2: Folder doelbestand en bestandsnaam
# 3: afstand waarbinnen een uitpeiling wordt gezocht(buffer radius)
# 4: waarde voor het maximale verschil in breedte toegestaan
# 5: waarde voor het maximale verschil in waterpeil toegestaan

input_inpeil = arcpy.GetParameterAsText(0)
input_uitpeil = arcpy.GetParameterAsText(1)
output_file = arcpy.GetParameterAsText(2)
zoekafstand = arcpy.GetParameter(3)
tolerantie_breedte = arcpy.GetParameter(4)
tolerantie_wp = arcpy.GetParameter(5)



# ------------- Spul om de functie zonder arcgis aan te roepen
# print('Start tool')
# print('Inlezen data...')
# input_inpeil = 'C:\Users\\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\Test_tool_inpeiling_0101.shp'
# input_uitpeil = 'C:\Users\\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\Test_tool_inpeiling_als_uitpeiling_0101.shp'
# output_file = 'C:\Users\\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\Test_tool_resultaat_{0}.shp'.format(np.random.random_integers(1,100))
# zoekafstand = 5
# tolerantie_breedte = 0.7
# tolerantie_wp = 0.15

#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
#input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VP_02_points.shp'
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_201800216_points.shp'
#input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_kortlang_points.shp'

#input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\VDH_IBA080_20170215_points.shp'

# input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20180718_IBA_meetjaar_2_points.shp'
# input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all\\20181108_IBA_meetjaar_1_points.shp'

# zoekafstand = 5
# input_inpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slib_error_meetjaar2_0101.shp'
# input_uitpeil = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slib_error_meetjaar1_0101.shp'
#
# output_folder = 'C:\Users\elma\Documents\GitHub\Test_data_werking_tools\\berekenen_slibaanwas\\proj_slibaanwas_all'
# ------------------

# Overzicht inladen
arcpy.AddMessage('Ontvangen parameters:')
arcpy.AddMessage('Bestand inpeiling = ' + input_inpeil)
arcpy.AddMessage('Bestand uitpeiling = ' + input_uitpeil)
arcpy.AddMessage('Output bestand = ' + output_file)
arcpy.AddMessage('Inlezen data...')

# Aanroepen functies voor berekening slib:
arcpy.AddMessage('Omzetten naar memcollection...')
point_col_in = from_shape_to_memcollection_points(input_inpeil)
point_col_uit = from_shape_to_memcollection_points(input_uitpeil)
arcpy.AddMessage('Omgezet naar memcollection')

arcpy.AddMessage('Middelpunten genereren...')
point_col_mid_in, point_col_mid_uit, profiel_namen_in, profiel_namen_uit = \
    get_profiel_middelpunt(point_col_in, point_col_uit)
arcpy.AddMessage('Middelpunten gegenereerd')

arcpy.AddMessage('Buffer creeren...')
buffer_mid_in = create_buffer(point_col_mid_in, zoekafstand)
arcpy.AddMessage('Buffer gecreeerd')

arcpy.AddMessage('Slibaanwas berekenen...')
t = time.time()
in_uit_combi, info_list = get_slibaanwas(point_col_in,point_col_uit,point_col_mid_uit,buffer_mid_in,
                                        tolerantie_breedte, tolerantie_wp)
elapsed = time.time() - t
# print('Slibaanwas berekend')
# print('TIJD: ', elapsed)

# Wegschrijven gegevens in shapefile
arcpy.AddMessage('Resultaat in shapefile wegschrijven...')
write_list_to_collection(output_file, in_uit_combi, info_list)
arcpy.AddMessage('Resultaat weggeschreven')
arcpy.AddMessage('klaar')
