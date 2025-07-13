# Road-Accident-Hotspot
## Problem Statement
The Road Accident Hotspot tool will help city planners identify crash hotspots within a road network. The tool function is based on ESRI shared [case-study](https://desktop.arcgis.com/fr/analytics/case-studies/analyzing-crashes-2-pro-workflow.htm).

By facilitating the process through a tool, the user will only need to gather their inputs and get a road network classified by the level of statistically significant clusters of high crashes rate.
## Project Objectives
The outcome of the project will be an ArcGIS tool.
## Input and Output
### Input layers
#### Mandatory
1)	Point feature class - Crash data incidents with a unique ID field. 
2)	Polyline feature class - road network data. 
3)	Integer - Date span of the data: years/months for the data e.g.: If the data was collected from 2020 to 2024, the date span will be 4 years.
4)	String - Output name: The name of the output road network.
#### Optional
5)	Weights Matrix File
6)	Integer - Maximum distance from road: for snapping the points to the road.
7)	Attribute table field (integer) - Fatalities
### Output
Line Feature Class layers classified based on the crash incident hotspots.
## Methodology
The tool will take the crash data and road network data as feature class inputs. Then, will copy the crash data to a new feature class and perform a snap to the road network to facilitate the spatial joint and count. The snapping will take a maximum distance from road threshold value from the user if provided, if not, it will use 0.25 miles as default (the distance suggested by ESRI in the shared article).
After snapping it will perform a spatial join, where if provided it will also aggregate the number of fatalities per road segment. An average crash per year field will be calculated by dividing the join count to the date span provided by the user. This field will be used on the hotspot analysis tool as the input field. If a Weights Matrix file is provided the conceptualization of spatial relationships will be taken from it, else, it will be set to Fixed Distance Band and a Distance Threshold will be calculated from the average distance to 8 nearest neighbors ([ESRI suggest 8 as the minimum number](https://pro.arcgis.com/en/pro-app/3.3/tool-reference/spatial-statistics/h-how-hot-spot-analysis-getis-ord-gi-spatial-stati.htm)).

![App Flowchart](Images/ArcGIS%20Road%20Accident%20Hotspot.png)