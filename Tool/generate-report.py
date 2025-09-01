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

if fatalities == "true":  # If Fatalities are available
    fatalities_df = pd.DataFrame(fatalities_array)  # Create a dataframe from the structured array
    fatalities_df["day"] = fatalities_df[date_field].dt.day_name()  # Create a day variable from the date field
    fatalities_df["year"] = fatalities_df.loc[:, date_field].map(lambda x: x.year)  # Get the year value
    # Input the order for the days to plot them in day of the week order
    days_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    fatalities_df['day'] = pd.Categorical(fatalities_df['day'], categories=days_ordered, ordered=True)
    daily_fat = fatalities_df.groupby('day')['Fatalities'].mean()  # Get the mean fatalities per day of the week
    yearly_fat = fatalities_df.groupby('year')['Fatalities'].mean()  # Get the mean fatalities per day of the week

    # Plot the figure (Daily Fatalities)
    plt.figure()  # Creates a new, blank figure
    daily_fat.plot(kind='line', figsize=(8, 6), title='Fatalities by Day', color='green', linewidth=3)
    plt.ylabel("Mean fatalities")
    plt.xlabel("Day of the Week")  # Add a label to the x-axis
    daily_fat_png = "fatalities_by_day.png"

    # Save the plot
    output_path = report_path + "\\" + daily_fat_png
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    # Plot the figure (Yearly Fatalities)
    plt.figure()  # Creates a second new, blank figure
    yearly_fat.plot(kind='bar', figsize=(8, 6), title='Fatalities by Year', color='green')
    plt.ylabel("Mean fatalities")
    plt.xlabel("Year")  # Add a label to the x-axis

    # Save the plot
    yearly_fat_png = "fatalities_by_year.png"
    output_path = report_path + "\\" + yearly_fat_png
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()  # Closes the figure

# Get total crashes variable
total_crashes = int(arcpy.management.GetCount(crash_data)[0])
# Get total segments variable
total_road_segments = int(arcpy.management.GetCount(road_network)[0])

# Generate general statistics
segments_with_crashes = len(road_stats_df[road_stats_df['Join_Count'] > 0])  # Get the segments with crashes
crash_involvement_rate = (
                                     segments_with_crashes / total_road_segments) * 100  # Get the percentage of segments with crashes

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
    '{segments_with_crashes}': str(segments_with_crashes),
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