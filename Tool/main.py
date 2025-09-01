# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 09:53:00 2025

@author: Paulo Medina
"""

# Import relevant modules
import arcpy
import pandas as pd
import matplotlib.pyplot as plt

# Get inputs from the user

arcpy.env.workspace = arcpy.GetParameterAsText(0) # REQUIRED: Working directory or gdb
crash_data = arcpy.GetParameterAsText(1) # REQUIRED: Crash point data
date_field = arcpy.GetParameterAsText(2) # REQUIRED: Date field from crash point data
fatalities = arcpy.GetParameterAsText(3) # OPTIONAL: Fatalities field
report_type_field = arcpy.GetParameterAsText(4) # REQUIRED IF FATALITIES CHECKED: Report type field
fatalities_variable_name = arcpy.GetParameterAsText(5) # REQUIRED IF FATALITIES CHECKED: Fatal incident name
road_network = arcpy.GetParameterAsText(6) # REQUIRED: Polyline road data
max_distance = arcpy.GetParameterAsText(7) # OPTIONAL: Distance in miles for snapping
units = arcpy.GetParameterAsText(8) # OPTIONAL: Get units preferred by the user
date_span = str(arcpy.GetParameterAsText(9)).lower() # REQUIRED: time span to average the crash data
report_path = arcpy.GetParameterAsText(10) # REQUIRED: Get the report path
#arcpy.env.outputCoordinateSystem = arcpy.GetParameterAsText(9) # REQUIRED: Spatial Reference for calculations


class invalidField(Exception): # Exception class to identify invalid field
    pass
class LicenseError(Exception): # Exception class to handle necessary licenses
    pass
class invalidDateSpan(Exception): # Exception class to handle invalid date span
    pass

try:
    
    # Check extension
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        # Raise a custom exception
        raise LicenseError
    
    # Check invalid fields    
    field_names = []
    for field in arcpy.ListFields(crash_data): # Retrieve all the field names from crash data
        field_names.append(field.name) # Append the name to the field_names list
    if date_field not in field_names: # If the inputted date_field is not on the list
        # Raise the error
        raise invalidField

    # Check date span input
    if date_span not in ["year", "month", "week"]: # If the date span is not on the dictionary keys
        # Raise the custom error    
        raise invalidDateSpan
        
    # Set environment settings MAYBE MOVE DOWN
    
    arcpy.env.overwriteOutput = True
    arcpy.addOutputsToMap = True

except LicenseError:
    arcpy.AddError("The Spatial Analyst License is not available.")
except invalidField:
    arcpy.AddError("The date field %s field is not valid." % date_field)
except invalidDateSpan:
    arcpy.AddError("The date %s is not valid. The values should be Year, Month, or Week." % date_span)






