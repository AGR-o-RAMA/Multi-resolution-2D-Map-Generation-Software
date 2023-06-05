# Code Repository for AGR-O-RAMA Project - Deliverable D1.2 Multi-resolution 2D Map Generation Software
This repository contains the code for the Agro-rama project's Deliverable D1.2, which focuses on the development of a multi-resolution 2D map generation software. The software is designed to automate the process of generating orthomosaic maps and extracting tiles from the maps for targeted analysis.
![alt text](https://github.com/Mulham91/AGR-O-RAMA/blob/main/images/exp.png)

# Features and Advantages
Orthomosaic Map Generation: The software leverages the power of Metashape to generate accurate orthomosaic maps. It performs image alignment, point cloud generation, mesh and texture generation, and orthorectification, resulting in high-quality orthomosaic maps.

Tiling for Efficient Analysis: The software includes functionality to divide the generated orthomosaic map into smaller tiles. This tiling process improves efficiency by reducing computational and memory requirements. It also allows for easier navigation and targeted analysis of specific areas of interest within the map.

Image Projection and Cropped Image Extraction: After tiling the orthomosaic map, the software projects each tile back to the original images used for map creation. By leveraging spatial information, it identifies the corresponding regions in the source images that overlap with each tile. This enables the extraction of cropped images, which retain the necessary spatial context and visual information for subsequent analysis and processing tasks.
# Usage
- Ensure that the Metashape software is installed on your system.
- Clone this repository to your local machine.
- Open the YAML configuration file and set the desired parameters for map generation, tiling, and image extraction.
- Provide the path to the acquired images as input for the orthomosaic map generation process.
- Run the Python script to execute the software, automating the entire process, including orthomosaic map generation, tiling, and image extraction.
# Workflow
1- Orthomosaic Map Generation: The software utilizes Metashape to perform various steps, such as image alignment, point cloud generation, mesh and texture generation, and orthorectification, resulting in a precise and georeferenced orthomosaic map.

	- Image Alignment: The script uses Metashape's image alignment functionality to match corresponding features and establish spatial relationships between images.
	- Point Cloud Generation: The script generates a dense point cloud by matching points across multiple images, capturing the 3D structure of the agricultural field.
	- Mesh and Texture Generation: The script creates a mesh representation of the field's surface geometry and applies texture for visual appearance.
	- Orthorectification: The script rectifies the images to remove distortions caused by camera angles and terrain variations, producing orthorectified images.
	- Orthomosaic Map Creation: By combining the rectified images, the script generates a 	visually consistent and georeferenced orthomosaic map.

2- Tiling: After generating the orthomosaic map, the software divides it into smaller tiles by partitioning the map into rectangular or square regions of a predetermined size. This facilitates efficient management, processing, and analysis of large-scale maps.

3- Tile Projection and Cropped Image Extraction: The software projects each tile back to the original images that contributed to the orthomosaic map. By utilizing spatial information captured during the orthomosaic generation, it accurately identifies the relevant portions of the original images that overlap with each tile. Cropped images representing the specific portions of the original images are extracted, preserving the necessary spatial context and visual information for subsequent analysis and processing.

