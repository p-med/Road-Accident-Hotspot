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
    if date_field not in field_names: # If the inputed date_field is not on the list
        # Raise the error
        raise invalidField  
    date_values = {"year": 365, "month": 30, "week": 7} # date value dictionary
    
    # Check date span input
    if date_span not in date_values.keys(): # If the date span is not on the dictionary keys
        # Raise the custom error    
        raise invalidDateSpan
        
    # Set environment settings MAYBE MOVE DOWN
    
    arcpy.env.overwriteOutput = True
    arcpy.addOutputsToMap = True
    # Get the current ArcGIS Pro project and active map
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    active_map = aprx.activeMap
    
    
    # Prepare the global variables
        
    # Create a copy of the crash data point layer to snap to the road layer
    snapped_points = arcpy.management.CopyFeatures(crash_data, "crash_data_copy")
    
    # Get the date span variable based on the date field
    
    def getTimeSpan(d_span, d_field, c_data): # Input Parameters: date span, date field, crash point data
        dates = [] # Store the single dates
        crash_array = arcpy.da.FeatureClassToNumPyArray(c_data, d_field)
    
        for i in crash_array: # For each field element in the array
            dates.append(i[0]) # Append the date value to the dates list
    
        # Calcualte the time span based on the data date field
        time_span = round(((max(dates) - min(dates))/date_values[d_span]).astype(float))
        
        return time_span
    
    # Snap points function
    
    def snapPoints(m_dist, points):
        # Snap the crash data to the road network
        if m_dist != "": # If max_distance was not shared, then set the max distance to 25 miles
            distance = m_dist + " " + units # Create the distance variable
        else:
            distance = "0.25 Miles"
        snap_environment_1 = [road_network, "EDGE", distance] # Create the snap environment variable
        snap_environment_2 = [road_network, "VERTEX", distance] # Create the snap environment variable
        snapped_points = arcpy.edit.Snap(points, [snap_environment_1,snap_environment_2]) # Snap the copied crash data to the road network
        arcpy.AddMessage("Crash Point data snapped to the road feature class.") # Add message to update process
        return snapped_points
        
    
    # Calculate the length of each road segment
    arcpy.management.CalculateGeometryAttributes(road_network, [["Length_mi", "LENGTH"]], "MILES_US")
    
    
    # Join crash data to the road network
    
    # Do a Spatial Join joining the road network and the snapped point data
    
    if fatalities == "false": # If no fatalities field have been provided
        # Join the road data and get the crash count
        joined_crash_roads = arcpy.analysis.SpatialJoin(road_network,
                                                        snapped_points,
                                                        "joined_crash_road_data", 
                                                        join_operation="JOIN_ONE_TO_ONE",
                                                        join_type="KEEP_ALL",
                                                        match_option="INTERSECT")
        arcpy.AddMessage("Crash data pointsjoined to the road data.")
    else: # If there is a fatalities field
        # Create an update cursor and set a 1 value if the row represent a fatal incident and 0 if not
        arcpy.management.AddField(snapped_points, "Fatalities", "LONG") # Create new field  
        # Create update cursor for feature class 
        with arcpy.da.UpdateCursor(snapped_points, [report_type_field,"Fatalities"]) as cursor:
            for row in cursor: # For each row on the cursor
                if row[0] == fatalities_variable_name: # If the row has a fatality
                    row[1] = 1 # Set the value to 1
                else:
                    row[1] = 0 # Else 0
                cursor.updateRow(row) # Update the cursor
            arcpy.AddMessage("Crash and fatalities data points joined to the road data.")
        
        # Store fatalities in array dataset 
        fatalities_array = arcpy.da.FeatureClassToNumPyArray(snapped_points, ("Fatalities", date_field))
        
        # Create a FieldMappings object and add all fields from the target (road_network)
        field_mappings = arcpy.FieldMappings()
        
        # Add all fields from the road network (target feature class)
        field_mappings.addTable(road_network)
        
        # Create a FieldMap for the Fatalities field from the join feature class
        fatalities_fieldmap = arcpy.FieldMap()
        
        # Add the 'Fatalities' field from the joined table to this FieldMap
        fatalities_fieldmap.addInputField(snapped_points, "Fatalities")
        
        # Set the properties of the output field that will be created
        output_field = fatalities_fieldmap.outputField
        output_field.name = "tot_fata"
        output_field.aliasName = "Total fatalities"
        output_field.type = "LONG"
        
        # Set the merge rule to "Sum" to total up fatalities for segments with multiple crashes
        fatalities_fieldmap.mergeRule = "Sum"
        fatalities_fieldmap.outputField = output_field
        
        # Add the customized FieldMap to the FieldMappings object
        field_mappings.addFieldMap(fatalities_fieldmap)
        
        # Perform the spatial join with the configured field mappings
        joined_crash_roads = arcpy.analysis.SpatialJoin(
                                                    road_network,
                                                    snapped_points,
                                                    "Crash_fatalities_count",
                                                    join_operation="JOIN_ONE_TO_ONE",
                                                    join_type="KEEP_ALL",
                                                    field_mapping=field_mappings,
                                                    match_option="INTERSECT"
                                                    )
        where_clause = "tot_fata IS NULL"
        # To correct null values in Fatlities field
        with arcpy.da.UpdateCursor(joined_crash_roads, "tot_fata", where_clause) as cursor:
            for row in cursor: # For each row on the cursor
                row[0] = 0
                cursor.updateRow(row) # Update the cursor
                                            
    # Create a new field "Avg_Crash_per_Year"
    # Create an update cursor and calculate the average crash per year value
    arcpy.management.AddField(joined_crash_roads, "Avg_crsh_yr", "DOUBLE") # Create new field
    
    fields = ["Join_Count", "Length_mi", "Avg_crsh_yr"] # Fields to use on the update cursor
    
    # Create update cursor for feature class 
    with arcpy.da.UpdateCursor(joined_crash_roads, fields) as cursor:
        for row in cursor: # For each row on the cursor
            avg_crash = row[0]/(time_span*row[1]) # Calculate the average number of crashes per year
            row[2] = avg_crash # Store the average number of crashes in the new field
            cursor.updateRow(row) # Update the cursor
    
    arcpy.AddMessage("Average crash indicents per road segement per %s calculated" % date_span)
    
    # Run the Hotspot Analysis for average crash incidents per road segment
    
    # Calculate the distance band
    distance_band = arcpy.stats.CalculateDistanceBand(snapped_points, 8, "EUCLIDEAN_DISTANCE")
    avg_distance = distance_band[1] # Get the Average 8 neighbor distance
    
    
    # Run the hotspot analysis tool with average crash per time span
    crash_hotspots = arcpy.stats.HotSpots(joined_crash_roads, # Input the road layer with the calculated average crashes
                         "Avg_crsh_yr", # Input the average yearly crash column
                         "Crash_hotspots", # Set the name of the output file
                         "FIXED_DISTANCE_BAND",# Set the spatial relationship
                         "EUCLIDEAN_DISTANCE", # Set the distance method
                         Distance_Band_or_Threshold_Distance = avg_distance) # Set the threshold distance
     
    arcpy.AddMessage("Crash incidents Hotspot calculated.")
    
    if fatalities == "true": # If the fatalities field variable is not empty
        # Create a new field "Avg_Crash_per_Year"
        # Create an update cursor and calculate the average fatalities per segment length by year value
        arcpy.management.AddField(joined_crash_roads, "Avg_fata_yr", "DOUBLE") # Create new field
    
        fields = ["tot_fata", "Length_mi", "Avg_fata_yr"] # Fields to use on the update cursor
    
        # Create update cursor for feature class 
        with arcpy.da.UpdateCursor(joined_crash_roads, fields) as cursor:
            for row in cursor: # For each row on the cursor
                avg_crash = row[0]/(time_span*row[1]) # Calculate the average number of crashes per year
                row[2] = avg_crash # Store the average number of crashes in the new field
                cursor.updateRow(row) # Update the cursor
        
        arcpy.AddMessage("Average fatal indicents per road segement per %s calculated" % date_span)
        
        # Get the Hotspot Analysis result for fatalities
        arcpy.stats.HotSpots(joined_crash_roads, # Input the road layer with the calculated average crashes
                             "Avg_fata_yr", # Input the average yearly crash column
                             "Fatalities_hotspots", # Set the name of the output file
                             "FIXED_DISTANCE_BAND",# Set the spatial relationship
                             "EUCLIDEAN_DISTANCE", # Set the distance method
                             Distance_Band_or_Threshold_Distance = avg_distance) # Set the threshold distance
        arcpy.AddMessage("Fatal incidents Hotspot calculated.")
    
    # Create graphs and variable for report
    
    # Get an array for the crash data
    crash_array = arcpy.da.FeatureClassToNumPyArray(crash_data, [date_field, "OBJECTID"])
    hotspot_array = arcpy.da.FeatureClassToNumPyArray(crash_hotspots, ["Gi_Bin", "GiZScore", "GiPValue"])
    road_stats_array = arcpy.da.FeatureClassToNumPyArray(joined_crash_roads, 
        ["Join_Count", "Length_mi", "Avg_crsh_yr", "OBJECTID"])
    
    # Convert to np arrays to DataFrames
    crash_df = pd.DataFrame(crash_array)
    hotspot_df = pd.DataFrame(hotspot_array)
    road_stats_df = pd.DataFrame(road_stats_array)
    
   
    if fatalities == "true": # If Fatalities are available
        fatalities_df = pd.DataFrame(fatalities_array) # Create a dataframe from the structured array
        fatalities_df["day"] = fatalities_df[date_field].dt.day_name() # Create a day variable from the date field
        fatalities_df["year"] = fatalities_df.loc[:,date_field].map(lambda x: x.year) # Get the year value
        # Input the order for the days to plot them in day of the week order
        days_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'] 
        fatalities_df['day'] = pd.Categorical(fatalities_df['day'], categories=days_ordered, ordered=True)
        daily_fat = fatalities_df.groupby('day')['Fatalities'].mean() # Get the mean fatalities per day of the week
        yearly_fat = fatalities_df.groupby('year')['Fatalities'].mean() # Get the mean fatalities per day of the week
        
        # Plot the figure (Daily Fatalities)
        plt.figure() # Creates a new, blank figure
        daily_fat.plot(kind='line', figsize=(8, 6), title='Fatalities by Day', color='green', linewidth=3)
        plt.ylabel("Mean fatalities")
        plt.xlabel("Day of the Week") # Add a label to the x-axis
        daily_fat_png = "fatalities_by_day.png"

        
        # Save the plot
        output_path = report_path + "\\" + daily_fat_png
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Plot the figure (Yearly Fatalities)
        plt.figure() # Creates a second new, blank figure
        yearly_fat.plot(kind='bar', figsize=(8, 6), title='Fatalities by Year', color='green')
        plt.ylabel("Mean fatalities")
        plt.xlabel("Year") # Add a label to the x-axis
        
        # Save the plot
        yearly_fat_png = "fatalities_by_year.png"
        output_path = report_path + "\\" + yearly_fat_png
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close() # Closes the figure
        
        
    # Get total crashes variable
    total_crashes = int(arcpy.management.GetCount(crash_data)[0])
    # Get total segments variable
    total_road_segments = int(arcpy.management.GetCount(road_network)[0])
    
    # Generate general statistics
    segments_with_crashes = len(road_stats_df[road_stats_df['Join_Count'] > 0]) # Get the segments with crashes
    crash_involvement_rate = (segments_with_crashes / total_road_segments) * 100 # Get the percentage of segments with crashes
      
    # Get number of hot and cold spots
    hot_spots = len(hotspot_df[hotspot_df['Gi_Bin'] > 0])
    cold_spots = len(hotspot_df[hotspot_df['Gi_Bin'] < 0])
    
    
    # Open HTML template file
    html_template_path = r".\report_template.html"
    with open(html_template_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    if fatalities == "true":
        total_fatalities = fatalities_df['Fatalities'].sum()
    else:
        total_fatalities = "Not analyzed"
    
    # Create substitution dictionary
    substitutions = {
        '{crash_data_name}': crash_data,
        '{road_data_name}': road_network,
        '{crash_length}': str(total_crashes),
        '{fatalities}': str(total_fatalities),
        '{hotspots}': str(hot_spots),
        '{coldspots}': str(cold_spots),
        '{segments_with_crashes}':str(segments_with_crashes),
        '{crash_involvement_rate}': "%.2f %%" % crash_involvement_rate,
        '{analysis_period}': date_span
    }
        
        
    # Replace placeholders with actual values
    for placeholder, value in substitutions.items():
        html_content = html_content.replace(placeholder, str(value))
        
       # Write the updated HTML file
    output_html_path = report_path + r"\Crash_Analysis_Report.html"
    with open(output_html_path, 'w', encoding='utf-8') as file:
        file.write(html_content)
        
    arcpy.AddMessage("HTML report generation completed successfully.")
    arcpy.AddMessage("HTML report generated: %s" % output_html_path)
    
except LicenseError:
    arcpy.AddError("The Spatial Analyst License is not available.")
except invalidField:
    arcpy.AddError("The date field %s field is not valid." % date_field)
except invalidDateSpan:
    arcpy.AddError("The date %s is not valid. The values should be Year, Month, or Week." % date_span)






