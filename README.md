# Road-Accident-Hotspot
A comprehensive ArcGIS tool designed to help urban planners and traffic engineers identify and visualize statistically significant crash hotspots and coldspots within a road network. This tool automates the core workflow of a GIS-based road safety analysis, as described in an Esri case study.

## Problem Statement
The Road Accident Hotspot tool will help city planners identify crash hotspots within a road network. The tool function is based on ESRI shared [case-study](https://desktop.arcgis.com/fr/analytics/case-studies/analyzing-crashes-2-pro-workflow.htm).

By facilitating the process through a tool, the user will only need to gather their inputs and get a road network classified by the level of statistically significant clusters of high crashes rate.

---

### Key Features

* **Automated Data Preparation:** Automatically snaps crash point data to the nearest road segments to ensure accurate spatial joining.
* **Customizable Analysis:** Analyze both total crashes and, optionally, crash fatalities to identify different types of high-risk areas.
* **Dynamic Hotspot Identification:** Uses the Getis-Ord Gi\* statistic to identify and map statistically significant clusters of high and low crash rates.
* **Comprehensive Reporting:** Generates a detailed HTML report with key statistics, including crash rates, crash-involved segments, and interactive plots of crash and fatality trends.
* **Error Handling:** Includes custom exceptions for invalid inputs like missing licenses or incorrect field names, providing clear user feedback.

---

### 🛠️ Requirements

* **Software:** ArcGIS Pro
* **ArcGIS Extension:** You'll need the **Spatial Analyst extension** to run the Hot Spot Analysis tool.
* **Python Libraries:** `arcpy`, `pandas`, `matplotlib`

---

### How to Use

The tool can be run directly within ArcGIS Pro. It exposes a series of parameters that the user can set within a geoprocessing pane.

#### Input Parameters

| Parameter Name                                     | Type      | Required | Description                                                                                             |
| :------------------------------------------------- | :-------- | :------- | :------------------------------------------------------------------------------------------------------ |
| **Working Directory or GDB** | Workspace | Yes      | The geodatabase or folder where the output will be saved.                                               |
| **Crash Point Data** | Point     | Yes      | A point feature class containing crash incident locations.                                              |
| **Date Field** | Field     | Yes      | The field in the crash data containing the date of the incident. Must be a date-time field.             |
| **Crash Hotspot Output Name** | String    | Yes      | The name for the output road feature class showing crash hotspots.                                      |
| **Road Network** | Line      | Yes      | A polyline feature class representing the road network.                                                 |
| **Date Span** | String    | Yes      | The time unit for averaging crash data (`'year'`, `'month'`, or `'week'`).                              |
| **Analyze Fatalities?** | Boolean   | No       | Check this box to include a fatality hotspot analysis. **Note:** This requires the next two parameters.  |
| **Report Type Field** | Field     | Yes (if Fatalities checked) | The field in the crash data that identifies the type of incident.                                     |
| **Fatal Incident Value** | String    | Yes (if Fatalities checked) | The value within the `Report Type Field` that indicates a fatal crash (e.g., `'FATAL'`).                |
| **Fatalities Hotspot Output Name** | String    | No       | The name for the output road feature class showing fatality hotspots.                                   |
| **Maximum Snap Distance** | Double    | No       | The maximum distance (in miles) to snap crash points to the nearest road segment. Defaults to 0.25 miles. |
| **Report Path** | Folder    | No       | The folder where the HTML analysis report will be saved. If left blank, no report will be generated.      |

---

### Methodology & Workflow

The tool's workflow follows these main steps:

1.  **Input Validation:** Checks for the necessary ArcGIS license and validates all user-provided fields to prevent runtime errors.
2.  **Data Preparation:** The script copies the input crash data and snaps each point to the nearest road segment. The snapping distance is user-defined or defaults to 0.25 miles. This step ensures crash points are correctly associated with the road network.
3.  **Data Joining & Aggregation:** A spatial join is performed to link the snapped crash points to the road segments. The script aggregates the number of crashes per road segment and, if requested, the total number of fatalities.
4.  **Average Incident Rate Calculation:** A new field is added to the road network to calculate the average number of crashes (or fatalities) per road length per time unit (year, month, or week) over the entire analysis period. This normalization is crucial for accurate hotspot analysis.
5.  **Hotspot Analysis (Getis-Ord Gi\*):** The script calculates the optimal distance band for the analysis and then runs the Hot Spot Analysis (Getis-Ord Gi\*) tool on the road network, using the average crash rate as the analysis field. This produces a new feature class highlighting statistically significant hot and cold spots.
6.  **HTML Report Generation (Optional):** If a report path is provided, the script generates a comprehensive HTML report summarizing the findings, including statistics, crash trends, and plots.

---

## Methodology
The tool will take the crash data and road network data as feature class inputs. Then, will copy the crash data to a new feature class and perform a snap to the road network to facilitate the spatial joint and count. The snapping will take a maximum distance from road threshold value from the user if provided, if not, it will use 0.25 miles as default (the distance suggested by ESRI in the shared article).
After snapping it will perform a spatial join, where if provided it will also aggregate the number of fatalities per road segment. An average crash per year field will be calculated by dividing the join count to the date span provided by the user. This field will be used on the hotspot analysis tool as the input field. If a Weights Matrix file is provided the conceptualization of spatial relationships will be taken from it, else, it will be set to Fixed Distance Band and a Distance Threshold will be calculated from the average distance to 8 nearest neighbors ([ESRI suggest 8 as the minimum number](https://pro.arcgis.com/en/pro-app/3.3/tool-reference/spatial-statistics/h-how-hot-spot-analysis-getis-ord-gi-spatial-stati.htm)).

![App Flowchart](Images/ArcGIS%20Road%20Accident%20Hotspot.png)

