import arcpy
from arcpy.sa import Idw, ZonalStatisticsAsTable

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
gdb = r"D:\Codex\building_01\data\processed\wuhan_features.gdb"
points = gdb + "\\communities_projected"
blocks = r"D:\Codex\building_01\data\processed\wuhan_blocks.gdb\blocks"

# 参数与论文一致：IDW power=2，500m栅格，可变搜索半径
idw_price = Idw(points, "price_yuan_m2", cell_size=500, power=2, search_radius=arcpy.sa.RadiusVariable(12, 50000))
raster_out = gdb + "\\idw_price"
idw_price.save(raster_out)
print("saved raster", raster_out)

zonal_out = gdb + "\\zonal_block_price_v2"
ZonalStatisticsAsTable(blocks, "block_id", raster_out, zonal_out, "DATA", "MEAN")
print("saved zonal table", zonal_out)

count = int(arcpy.GetCount_management(zonal_out)[0])
print("zonal rows", count)

