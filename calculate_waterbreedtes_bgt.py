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