import Metashape
import multiprocessing
import yaml
import os

def create_tiles():
	print("File location using os.getcwd():", os.getcwd())

	with open('/home/mulham/agrorama/output/config.yaml', 'r') as stream:


		try:
			data = yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			print(exc)
	f = open(data['tiles_dic'], 'w')
	save_path = data['tiles_path']
	tile_size=data['tile_size']
	start_x=data['start_x']
	start_y=data['start_y']
	doc = Metashape.app.document
	if not len(doc.chunks):
	    raise Exception("No chunks!")
	chunk = doc.chunk
	orthomap=chunk.findOrthomosaic(0)
	crs = chunk.crs
	if not chunk.shapes:
		chunk.shapes = Metashape.Shapes()
		chunk.shapes.crs = crs
	resy = (orthomap.top - orthomap.bottom) / (orthomap.height)
	resx = (orthomap.right - orthomap.left) / (orthomap.width)
	num_cols = (orthomap.width - start_x - 1) // tile_size + 1
	num_rows = (orthomap.height - start_y - 1) // tile_size + 1
	for i in range(num_rows):
		for j in range(num_cols):
			tile_x = start_x + (j* tile_size)
			tile_y = start_y + (i * tile_size)
			tile_width = min(tile_size, orthomap.width - tile_x)
			tile_height = min(tile_size, orthomap.height - tile_y)
			bbox = Metashape.BBox()
			bbox.min = Metashape.Vector([tile_x * resx + orthomap.left, tile_y  * resy+ orthomap.bottom])
			bbox.max = Metashape.Vector([(tile_x + tile_width) * resx + orthomap.left, (tile_y + tile_height) * resy + orthomap.bottom])
			tile_path = save_path+"/tile{}_{}.jpg".format(i, j)
			v1 =Metashape.Vector([bbox.min[0],bbox.min[1]])
			v2 =Metashape.Vector([bbox.max[0],bbox.min[1]])
			v3 =Metashape.Vector([bbox.max[0],bbox.max[1]])
			v4 =Metashape.Vector([bbox.min[0],bbox.max[1]])
			coords = [v1,v2,v3,v4]
			shape = chunk.shapes.addShape()
			shape.label = "tile{}_{}".format(i, j)
			shape.geometry.type = Metashape.Geometry.Type.PolygonType
			shape.geometry = Metashape.Geometry.Polygon(coords)
			tile_dic=[tile_x,tile_y, tile_width,tile_height]
			f.write("tile{}_{}".format(i, j) + ': ' + ','.join(map(str, tile_dic)) + '\n')

			chunk.exportRaster(tile_path, image_format = Metashape.ImageFormatJPEG,clip_to_boundary=False,
			   raster_transform=Metashape.RasterTransformNone,  region = bbox,
			   resolution_x = resx, resolution_y = resy,split_in_blocks = True, block_width = int(tile_width), block_height = int(tile_height),
			    white_background = True, save_alpha=True, source_data=Metashape.OrthomosaicData)

	Metashape.app.update()
	
	print("Script finished!")


label = "Scripts/Create tiles shape layer"
Metashape.app.addMenuItem(label, create_tiles)
print("To execute this script press {}".format(label))
