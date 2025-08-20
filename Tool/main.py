# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 09:53:00 2025

@author: Paulo Medina
"""

# Import relevant modules
import arcpy
import numpy as np
import pandas as pd

# Get inputs from the user
workspace = arcpy.GetParameterAsText(0) # Working directory or gdb
crash_data = arcpy.GetParameterAsText(1) # Crash point data
fatalities_field = arcpy.GetParameterAsText(2) # OPTIONAL: Fatalities field
road_network = arcpy.GetParameterAsText(3) # Polyline road data
max_distance = arcpy.GetParameterAsText(4) # Float value in miles for snapping
weight_matrix = arcpy.GetParameterAsText(5) # OPTIONAL: weight matrix file


# Set environment settings
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True


# Create a copy of the crash data point layer
snapped_points = arcpy.management.CopyFeatures(crash_data, "crash_data_copy")

# Snap the crash data to the road network
distance = str(max_distance) + " Mile" # Craete the distance variable
snap_environment = [road_network, "EDGE", distance] # Create the snap environment variable
arcpy.edit.Snap(snapped_points, snap_environment) # Snap the copied crash data to the road network


# Join crash data to the road network

arcpy.analysis.SpatialJoin(road_network,snapped_points,"joined_crash_road_data")


