## import arcpy
# Get the date span
def get_time_span(date_span, date_field, crash_data):  # Input Parameters: date span, date field, crash point data
    date_values = {"year": 365, "month": 30, "week": 7}  # date value dictionary
    dates = []  # Store the single dates

    # Create an array based on the date field values
    crash_array = arcpy.da.FeatureClassToNumPyArray(crash_data, date_field)

    for i in crash_array:  # For each field element in the array
        dates.append(i[0])  # Append the date value to the dates list

    # Calculate the time span based on the data date field
    time_span = round(((max(dates) - min(dates)) / date_values[date_span]).astype(float))

    return time_span # Return the time span value

def get_snap_distance(dist, units):
    if dist != "":  # If max_distance was shared
        distance = dist + " " + units  # Create the distance variable
        return distance
    else:  # Else set the max distance to 25 miles
        distance = "0.25 Miles"
        return distance

# Snap points to road network function
def snap_points(max_dist, crash_points, road_lines, units): # Max distance, crash point layer, road line layer, distance units
    # Create a copy of the crash data point layer to snap to the road layer
    copied_points = arcpy.management.CopyFeatures(crash_points, "crash_data_copy")
    # Snap the crash data to the road network
    distance = get_snap_distance(max_dist, units)
    # Create snap environments
    snap_environment_1 = [road_lines, "EDGE", distance]  # Create the snap environment variable
    snap_environment_2 = [road_lines, "VERTEX", distance]  # Create the snap environment variable
    #Snap points
    snapped_points = arcpy.edit.Snap(copied_points, [snap_environment_1,
                                                     snap_environment_2])  # Snap the copied crash data to the road network
    arcpy.AddMessage("Crash Point data snapped to the road feature class.")  # Add message to update process
    return snapped_points # Return the snapped points

def get_road_length(road_lines, units):
    # If units were not provided, default to US miles
    if units == "":
        field_name = "Length_mi"
        arcpy.management.CalculateGeometryAttributes(road_lines, [[field_name, "LENGTH"]], "MILES_US")
        return field_name
    else: # Else, get the field name and length in specified units
        field_name = "Length" + "_" + units[:2].lower()
        arcpy.management.CalculateGeometryAttributes(road_lines, [[field_name, "LENGTH"]], units)
        return field_name

# Create field mapping
def create_field_map(road_lines, crash_points):
    # Create a FieldMappings object and add all fields from the target (road_network)
    field_mappings = arcpy.FieldMappings()

    # Add all fields from the road network (target feature class)
    field_mappings.addTable(road_lines)

    # Create a FieldMap for the Fatalities field from the join feature class
    fatalities_fieldmap = arcpy.FieldMap()

    # Add the 'Fatalities' field from the joined table to this FieldMap
    fatalities_fieldmap.addInputField(crash_points, "Fatalities")

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
    return field_mappings

def classify_incident(crash_points, report_type_field, fatalities_name):
    # Create an update cursor and set a 1 value if the row represent a fatal incident and 0 if not
    arcpy.management.AddField(crash_points, "Fatalities", "LONG")  # Create new field
    # Create update cursor for feature class
    with arcpy.da.UpdateCursor(crash_points, [report_type_field, "Fatalities"]) as cursor:
        for row in cursor:  # For each row on the cursor
            if row[0] == fatalities_name:  # If the row has a fatality
                row[1] = 1  # Set the value to 1
            else:
                row[1] = 0  # Else 0
            cursor.updateRow(row)  # Update the cursor
        arcpy.AddMessage("Crash and fatalities data points joined to the road data.")


# Prepare the road data
def prep_roads(road_lines, crash_points, fat_field = False, report_type_field = "", fatalities_variable_name = ""):
    # Join crash data to the road network
    # Do a Spatial Join joining the road network and the snapped point data
    if fat_field == "false":  # If no fatalities field have been provided
        # Join the road data and get the crash count
        joined_crash_roads = arcpy.analysis.SpatialJoin(road_lines,
                                                        crash_points,
                                                        "joined_crash_road_data",
                                                        join_operation="JOIN_ONE_TO_ONE",
                                                        join_type="KEEP_ALL",
                                                        match_option="INTERSECT")
        arcpy.AddMessage("Crash data points joined to the road data.")
        return joined_crash_roads
    else:  # If there is a fatalities field
        # Classify the crash incidents adding 1 if it has a fatality else 0
        classify_incident(crash_points, report_type_field, fatalities_variable_name)

        # Create a fieldmap to link fatalities count to the roads
        field_map_result = create_field_map(road_lines, crash_points)

        # Perform the spatial join with the configured field mappings
        joined_crash_roads = arcpy.analysis.SpatialJoin(
            road_lines,
            crash_points,
            "Crash_fatalities_count",
            join_operation="JOIN_ONE_TO_ONE",
            join_type="KEEP_ALL",
            field_mapping=field_map_result,
            match_option="INTERSECT"
        )
        where_clause = "tot_fata IS NULL"
        # To correct null values in Fatalities field
        with arcpy.da.UpdateCursor(joined_crash_roads, "tot_fata", where_clause) as cursor:
            for row in cursor:  # For each row on the cursor
                row[0] = 0
                cursor.updateRow(row)  # Update the cursor
        return joined_crash_roads


def get_avg_crash(road_lines, time_span, date_span, length_field):
    # Create a new field "Avg_Crash_per_Year"
    # Create an update cursor and calculate the average crash per year value
    arcpy.management.AddField(road_lines, "Avg_crash_yr", "DOUBLE")  # Create new field

    fields = ["Join_Count", length_field, "Avg_crash_yr"]  # Fields to use on the update cursor

    # Create update cursor for feature class
    with arcpy.da.UpdateCursor(road_lines, fields) as cursor:
        for row in cursor:  # For each row on the cursor
            avg_crash = row[0] / (time_span * row[1])  # Calculate the average number of crashes per year
            row[2] = avg_crash  # Store the average number of crashes in the new field
            cursor.updateRow(row)  # Update the cursor
    arcpy.AddMessage("Average crash incidents per road segment per %s calculated" % date_span)

def get_avg_fat(road_lines, time_span, date_span, length_field):
    # Create a new field "Avg_Crash_per_Year"
    # Create an update cursor and calculate the average fatalities per segment length by year value
    arcpy.management.AddField(road_lines, "Avg_fata_yr", "DOUBLE")  # Create new field

    fields = ["tot_fata", length_field, "Avg_fata_yr"]  # Fields to use on the update cursor

    # Create update cursor for feature class
    with arcpy.da.UpdateCursor(road_lines, fields) as cursor:
        for row in cursor:  # For each row on the cursor
            avg_crash = row[0] / (time_span * row[1])  # Calculate the average number of crashes per year
            row[2] = avg_crash  # Store the average number of crashes in the new field
            cursor.updateRow(row)  # Update the cursor

    arcpy.AddMessage("Average fatal incidents per road segment per %s calculated" % date_span)


# Run the Hotspot Analysis for average crash incidents per road segment
def hotspot_analysis(road_lines, crash_points, incident_type):
    # Calculate the distance band
    distance_band = arcpy.stats.CalculateDistanceBand(crash_points, 8, "EUCLIDEAN_DISTANCE")
    avg_distance = distance_band[1]  # Get the Average 8 neighbor distance

    # Run the hotspot analysis tool with average crash per time span
    crash_hotspots = arcpy.stats.HotSpots(road_lines,
                                          # Input the road layer with the calculated average crashes
                                          "Avg_crash_yr",  # Input the average yearly crash column
                                          "Crash_hotspots",  # Set the name of the output file
                                          "FIXED_DISTANCE_BAND",  # Set the spatial relationship
                                          "EUCLIDEAN_DISTANCE",  # Set the distance method
                                          Distance_Band_or_Threshold_Distance=avg_distance)  # Set the threshold distance
    arcpy.AddMessage("%s Hotspot calculated." % incident_type)
    return crash_hotspots