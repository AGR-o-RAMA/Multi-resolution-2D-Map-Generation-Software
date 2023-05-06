import concurrent.futures
import Metashape
import multiprocessing
import yaml
import sys
import cv2 
from pathlib import Path
import numpy as np
def process_camera(chunk,camera, img, tile,tile_lable,output_path):
    x1= tile[0] 
    y1= tile[1] 
    x2= tile[0] + tile[2] 
    y2= tile[1] + tile[3] 
    ortho=chunk.findOrthomosaic(0)
    resy = (ortho.top - ortho.bottom) / (ortho.height)
    resx = (ortho.right - ortho.left) / (ortho.width) 
    tile_corner=[[x1,y1],[x1,y2],[x2,y1],[x2,y2]]
    corner_in_image=[]
    for corner in tile_corner:
        x=corner[0]
        y=corner[1]
        real_x = ortho.left + x * resx
        real_y = ortho.bottom + y * resy
        
        real_h = chunk.elevation.altitude(Metashape.Vector([real_x, real_y]))
        point3D = Metashape.Vector([real_x, real_y, real_h])
        point_local = chunk.transform.matrix.inv().mulp(chunk.crs.unproject(point3D))
        if (not camera.transform or camera.project(point_local) == None):
            continue

        else:
            pr_x, pr_y = camera.project(point_local)
            if (0 <= int(pr_x) < camera.sensor.width) and (0 <= int(pr_y) < camera.sensor.height):
                img[int(pr_y):int(pr_y+10),int(pr_x): int(pr_x+10)] = [0, 0, 255]
                corner_in_image.append((int(pr_x), int(pr_y)))
    if(len(corner_in_image)==4):
        new_image = np.zeros((tile[2],tile[3] , 3), np.uint8)
        new_image[:,:]= img[corner_in_image[2][1]:corner_in_image[0][1],corner_in_image[0][0]:corner_in_image[1][0]] #= [0, 0, 255]
   
        cv2.imwrite(output_path + camera.label+'_'+ tile_lable + ".png", new_image)
        cv2.imwrite(output_path + camera.label+'_img_'+ tile_lable + ".png", img)
def project_back(chunk,tile,tile_lable,images_path,output_path ):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for c, camera in enumerate(chunk.cameras):
            if Path(images_path + str(camera.label+ ".png")).is_file():
                img = cv2.imread(images_path + str(camera.label) +".png")
                futures.append(executor.submit(process_camera,chunk, camera, img,tile,tile_lable,output_path))
def main():

	doc = Metashape.app.document
	if not len(doc.chunks):
	    raise Exception("No chunks!")
	chunk = doc.chunk
	if not len(doc.chunks):
	    raise Exception("No chunks!")
	with open('/home/mulham/agrorama/output/config.yaml', 'r') as stream:
		try:
			data = yaml.safe_load(stream)
		except yaml.YAMLError as exc:
			print(exc)
	output_path = data['project_back_path']
	images_path = data['images_path']
	tile_names = data['tile_names']
	f = open(data['tiles_dic'], 'r')
	data_dict = {}
	for line in f:
		key, value = line.strip().split(': ')
		value = list(map(int, value.split(',')))
		data_dict[key] = value
	f.close()
	project_back(chunk,data_dict[tile_names], tile_names,images_path,output_path )

	print("Script finished!")


label = "Scripts/project back"
Metashape.app.addMenuItem(label, main)
print("To execute this script press {}".format(label))

