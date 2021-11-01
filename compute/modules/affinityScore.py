'''
@author: Shahzeb
@created: Friday, July 17th 2020
'''

from .gVars import isp_pops, Output_Directory
from shapely.geometry import Point, Polygon
import numpy as np
import math, operator, statistics, json, os
import matplotlib.patches as mpatches
import geopandas as gpd
import matplotlib.pyplot as plt

def sort_by_angle(isp, isp_center):
    '''
        Given an array of lat/long points, and a center point, this function returns the lat/long array\n
        sorted clockwise around the provided center point.\n

        isp: a list of (longitude, latitude) for PoP os the isp

        isp_center: the center point for all the PoP locations

        @return list of PoPs sorted clockwise with respect to the center
    '''
    angle = {}
    for x,y in isp:
        x = round(x,3)
        y = round(y,3)
        try:
            m = (isp_center[1]-y)/(isp_center[0]-x)
        except:
            m = 0
        if (m==0):
            angle[(x,y)] = 0 if y>isp_center[1] else 180

        elif (x >= isp_center[0]):
            angle[(x,y)] = 90 - math.degrees(math.atan(m))
        elif (x < isp_center[0]):
            angle[(x,y)] = 270 - math.degrees(math.atan(m))


    sorted_d = sorted(angle.items(), key=operator.itemgetter(1))
    sorted_angle = []
    for pair in sorted_d:
        sorted_angle.append(pair[0])

    return sorted_angle

def generatePolygon(isp_pop_locations_list):
    '''
    Given a list of lat/long points sorted clockwise against the center, this function returns\n
    a shapely Polygon object.
    '''
    isp_location = {'longitude': [pair[0] for pair in isp_pop_locations_list], 'latitude': [pair[1] for pair in isp_pop_locations_list]}

    isp_center = (statistics.median(isp_location["longitude"]), statistics.median(isp_location["latitude"]))
    return Polygon(sort_by_angle(zip(isp_location["longitude"], isp_location["latitude"]),isp_center))

def getPopulation(isp_a_poly, isp_b_poly):
    '''
    isp_a_poly: Polygon object that represents the area covered by isp_a\n
    isp_b_poly: Polygon object that represents the area covered by isp_b\n
    Given two polygons, this function uses the GPW gridded population of the world data to calculate\n
    the population in polygon A, polygon B and the intersection of those polygons.
    '''
    pop_data = np.loadtxt("compute/data/gpw_v4_population_count_2020.asc", skiprows=6)
    pop_data = np.where(pop_data==-9999, 0.0, pop_data)

    isp_a_pop=0.0
    isp_b_pop=0.0
    int_pop=0.0

    min_x, min_y, max_x, max_y = isp_a_poly.union(isp_b_poly).bounds

    min_x = int((min_x+180.0)/0.041666666666667)
    min_y = int((min_y+90.0)/0.041666666666667)

    max_x = int(math.ceil((max_x+180.0)/0.041666666666667))+2
    max_y = int(math.ceil((max_y+90.0)/0.041666666666667))+2

    for i in range(min_x,max_x):
        for j in range(min_y,max_y):

            point_to_check = Point((0.041666666666667*i)-180.0, (0.041666666666667*j)-90.0)
            pop_at_point = pop_data[i][j]

            if point_to_check.within(isp_a_poly):

                isp_a_pop += pop_at_point
                if point_to_check.within(isp_b_poly):

                    isp_b_pop += pop_at_point
                    int_pop += pop_at_point

            elif point_to_check.within(isp_b_poly):
                isp_b_pop += pop_at_point

    return int(isp_a_pop), int(isp_b_pop), int(int_pop)


def drawOverlapGraph(isp_a, isp_b, isp_a_pops, isp_b_pops, isp_a_poly, isp_b_poly):
    '''
    This function draws a matplotlib graph to visualize the PoP locations and coverage areas for the two ISPs.
    '''
    output_directory_for_graph = os.path.abspath(Output_Directory + "/" + str(isp_a[1]) + "_" + str(isp_b[1])+'/graph/')

    if not os.path.exists(output_directory_for_graph):
        os.makedirs(output_directory_for_graph)

    usa_map = gpd.read_file('./compute/data/tl_2017_us_state/tl_2017_us_state.shp')
    crs = {'init': 'epsg:4326'}

    isp_a_plottable_points = [Point(xy) for xy in isp_a_pops] # run this line first for points
    isp_b_plottable_points = [Point(xy) for xy in isp_b_pops]

    isp_a_point_geo = gpd.GeoDataFrame(crs=crs, geometry=isp_a_plottable_points)
    isp_b_point_geo = gpd.GeoDataFrame(crs=crs, geometry=isp_b_plottable_points)

    isp_a_geo = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[isp_a_poly]) # run this line with poly
    isp_b_geo = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[isp_b_poly])

    fig, ax = plt.subplots(figsize = (15, 15))
    plt.xlim(-125, -66.5)
    plt.ylim(24, 50)

    usa_map.plot(ax = ax, alpha=0.4, color='grey')

    isp_a_geo.plot(ax=ax,color='red', alpha=0.3)
    isp_b_geo.plot(ax=ax,color='blue', alpha=0.3)

    isp_a_point_geo.plot(ax=ax, color='red', alpha=0.7)
    isp_b_point_geo.plot(ax=ax, color='blue', alpha=0.7)

    plt.axis('off')
    red_patch = mpatches.Patch(color='red',alpha=0.4, label= str(isp_a[0]).upper())
    blue_patch = mpatches.Patch(color='blue',alpha=0.4, label=str(isp_b[0]).upper())
    purple_patch = mpatches.Patch(color='#801B88',alpha=0.5, label='Overlap')


    ax.legend(loc='lower right', prop={"size":18}, handles=[red_patch, blue_patch, purple_patch])
    plt.savefig('./compute/output/' + str(isp_a[1]) +'_'+ str(isp_b[1]) + '/graph/'+str(isp_a[1]) +'_'+ str(isp_b[1])+'_overlap.png', bbox_inches='tight')


def affinityScore(isp_a, isp_b, isp_a_pop_locations_list, isp_b_pop_locations_list, common_pop_locations):

    '''
    Given two ISPs, this function uses the ISP PoP locations to calculate the affinity score.\n
    '''


    # cacheFile1 = './compute/cache/'+str(isp_a_as)+'_'+str(isp_b_as)+'.json'
    # cacheFile2 = './compute/cache/'+str(isp_b_as)+'_'+str(isp_a_as)+'.json'

    # if os.path.exists(cacheFile1):
    #     with open(cacheFile1, 'r') as f:
    #         affinitySocre = json.load(f)
    #         return affinitySocre['affinityScore']
    # elif os.path.exists(cacheFile2):
    #     with open(cacheFile2, 'r') as f:
    #         affinitySocre = json.load(f)
    #         return affinitySocre['affinityScore']


    isp_a_poly = generatePolygon(isp_a_pop_locations_list)
    isp_b_poly = generatePolygon(isp_b_pop_locations_list)

    drawOverlapGraph(isp_a, isp_b, isp_a_pop_locations_list, isp_b_pop_locations_list, isp_a_poly, isp_b_poly)

    ### To make the program faster only for testing purposes:
    # return 0.5
    ###
    isp_a_population, isp_b_population, intersection_population = getPopulation(isp_a_poly, isp_b_poly)

    total_coverage_population = (isp_a_population + isp_b_population) - intersection_population

    affinity_score_isp_a = 1 - (isp_a_population / total_coverage_population)

    if affinity_score_isp_a < 0:
        affinity_score_isp_a = 0.0

    affinity_score_isp_b = 1 - (isp_b_population / total_coverage_population)


    if affinity_score_isp_b < 0:
        affinity_score_isp_b = 0.0

    affinity_score_combined = math.sqrt(affinity_score_isp_a * affinity_score_isp_b)

    # with open(cacheFile1, 'w') as f:
    #     json.dump({'affinityScore':affinity_score_combined},f)

    return affinity_score_combined
