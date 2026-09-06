import arcpy
from arcpy.sa import Idw, ZonalStatisticsAsTable
arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
gdb = r"D:\Codex\building_01\data\processed\wuhan_features.gdb"
points = gdb + "\\communities_projected"
blocks = r"D:\Codex\building_01\data\processed\wuhan_blocks.gdb\blocks"
idw_price = Idw(points, "price_yuan_m2", cell_size=500, power=2, search_radius=arcpy.sa.RadiusVariable(24, 100000))
idw_price.save(gdb + "\\idw_price_v3")
zonal_out = gdb + "\\zonal_block_price_v3"
ZonalStatisticsAsTable(blocks, "block_id", gdb + "\\idw_price_v3", zonal_out, "DATA", "MEAN")
print("rows", arcpy.GetCount_management(zonal_out)[0])

