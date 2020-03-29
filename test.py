'''
Created on Jan 23, 2019

@author: prasun
'''
# import numpy
# from scipy.stats import rankdata
# 
# a = [4,2,7,1, 1]
# a_ = rankdata(a, method='ordinal').astype(int)
# print(a_)


# a = [1, 2, 3, 4]
# b = [2, 3, 4, 5]
# 
# c = [[v, k, b.index(v)] for k, v in enumerate(a) if v in b]
# a_extra = set(a) - set(b)
# len_c = len(c)
# for item_, i in zip(a_extra, range(len(a_extra))):
#     c.append([item_, a.index(item_), len_c + i])
# b_extra = set(b) - set(a)
# len_c = len(c)
# for item_, i in zip(b_extra, range(len(b_extra))):
#     c.append([item_, len_c + i, b.index(item_)])
# print(c)


# import numpy 
# a = numpy.array([3,2,1,0,-1])
# a += (-1)*a[-1]
# print(a)



# def test_func(a):
#     a *= 2
#         
# a = 5
# test_func(a)
# print(a)



# from shapely.geometry import Polygon
# from scipy.spatial import ConvexHull
# import numpy as np
# 
# p1 = Polygon([(0,2), (1,3), (2,2), (1,0), (0,2)])
# p2_list = np.array([(1,1), (2,3), (3,3), (4,2), (3,0), (3,4)])
# print(p2_list)
# p2_hull = ConvexHull(p2_list)
# p2_points = [(p2_list[i][0], p2_list[i][1]) for i in p2_hull.vertices]
# p2_points.append(p2_points[0])
# p2 = Polygon(p2_points)
# print(p2.exterior.coords.xy)
# # p2 = Polygon([(1,1), (2,3), (3,4), (4,2), (3,0), (1,1)])
# p3 = Polygon([(3,1), (4,3), (4,0), (3,1)])
# if p1.overlaps(p2):
#     intersec_p1_p2 = p1.intersection(p2)
#     print(intersec_p1_p2.area)
#     x, y = intersec_p1_p2.exterior.coords.xy
#     print(x, y)

# n = 4
# print([i for i in range(1, n/2 + 1)])


# import math
# n = 9
# if n % 2 == 0:
#     willingness_min = 2 / float(n) * sum([math.sqrt((n - i + 1)/float(n) * i/float(n)) for i in range(1, n/2 + 1)])
# else:
#     willingness_min = ((2 * sum([math.sqrt((n - i + 1)/float(n) * i/float(n)) for i in range(1, (n - 1)/2 + 1)])) + (n + 1)/(2*float(n))) / float(n)
# print(willingness_min)
# 
# x = [(1-(i-1)/float(n)) for i in range(1, n+1)]
# y = [(1-(n-i)/float(n)) for i in range(1, n+1)]
# print(x)
# print(y)
# s = sum([math.sqrt(i * j) for i, j in zip(x, y)])
# print(s/len(x))


# import numpy as np
# from scipy import stats
# np.random.seed(12345678)
# x = np.random.random(10)
# y = 1.6*x + np.random.random(10)
# 
# print(x)
# print(y)



# import requests, time
# 
# base_url = "http://www.antennasearch.com"
# final_url = "{0}/{1}".format(base_url, "sitestart.asp")
# headers = {
#     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
# 
# s = requests.Session()
# payload = {"AddressIn":"N Alafaya Tr", "CityName":"Orlando", "StateName":"Fl", "ZipCodeNum":"32826", "sourcepagename": "hopgsitemain", "reportname":"antennacheck", "cmdRequest":"startcheck", }
# response = s.post(final_url, data=payload, headers = headers)
# print(response.content)
# payload = {"reportname001":"antennacheck", "statename001":"fl", "cityname001":"orlando", "Address001":"N Alafaya Tr, Orlando, FL 32826", "latitude001": "28.5669737560291", "longitude001":"-81.2075819698511", "sourcepagename":"SrchAnt", "cmdRequest":"process"}
# response = s.post(final_url, data=payload)#, headers = headers, timeout=30)
# print(response.content)
# time.sleep(20)
# payload = {"sourcepagename":"woprebincheck", "cmdrequest":"bincheck"}
# response = s.post(final_url, data=payload, headers = headers)
# print(response.content)
# print(response.status_code, response.reason)


cidr = 27
_mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
_subnet = (str ((0xff000000 & _mask) >> 24 ) + "." +
           str ((0x00ff0000 & _mask) >> 16 ) + "." +
           str ((0x0000ff00 & _mask) >> 8 ) + "." +
           str ((0x000000ff & _mask)))
print(_subnet)

