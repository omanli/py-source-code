
'''
Start with drawing networks


TSP
gim travelling salesman problem big instance
gim travelling salesman problem 48 states
https://www.ibm.com/developerworks/community/blogs/jfp/entry/no_the_tsp_isn_t_np_complete?lang=en
https://www.ibm.com/developerworks/community/blogs/jfp/entry/np_or_not_np_that_is_the_question49?lang=en
http://graham-kendall.com/blog/2013/12/what-is-operations-research/
http://nonstationarity.tumblr.com/post/71472825016/ive-been-everywhere-optimally
http://www.johnnycashhasbeeneverywhere.com
http://www.nomachetejuggling.com/2012/09/14/traveling-salesman-the-most-misunderstood-problem/
https://orinanobworld.blogspot.com.tr/2012/11/np-dopey.html
https://adamo.wordpress.com/2009/10/22/re-the-humbling-power-of-p-v-np/

number of digits in 100 factorial
https://math.stackexchange.com/questions/1075422/how-many-digits-are-there-in-100

'''




'''
D:\oma\Courses\COME102\py



x = array([3, 5, 10])
x.tolist()
np.asarray(someListOfLists, dtype=np.float32)

https://docs.scipy.org/doc/numpy/reference/generated/numpy.linalg.norm.html
reshape()
norm()

numpy.random.random_integers(10, 99, (10,2))




import come102tsp as tsp
import imp 
imp.reload(tsp)


r = tsp.two_opt(tsp.cities,0.1)
tsp.plot_route(tsp.cities,r)
tsp.plot_cities(tsp.cities)

tsp.cities = tsp.random_cities(30)
r = arange(tsp.cities.shape[0])

'''



'''
python draw travelling salesman

https://stackoverflow.com/questions/25585401/travelling-salesman-in-scipy


tsp_solution = min( (sum( Dist[i] for i in izip(per, per[1:])), n, per) for n, per in enumerate(i for i in permutations(xrange(Dist.shape[0]), Dist.shape[0])) )[2]
 Dist (numpy.array) is the distance matrix

'''



'''
http://www.blog.pyoung.net/2013/07/26/visualizing-the-traveling-salesman-problem-using-matplotlib-in-python/
 https://gist.github.com/payoung/6087046

https://stackoverflow.com/questions/25585401/travelling-salesman-in-scipy


Manipal University Summer of Code
https://github.com/MUSoC
https://github.com/MUSoC/Visualization-of-popular-algorithms-in-Python
https://github.com/MUSoC/Visualization-of-popular-algorithms-in-Python/tree/master/Travelling%20Salesman%20Problem
https://github.com/MUSoC/Visualization-of-popular-algorithms-in-Python/blob/master/Travelling%20Salesman%20Problem/README.md
https://github.com/MUSoC/Visualization-of-popular-algorithms-in-Python/blob/master/Travelling%20Salesman%20Problem/input.txt
https://github.com/MUSoC/Visualization-of-popular-algorithms-in-Python/blob/master/Travelling%20Salesman%20Problem/tsp_christofides.py


'''





'''

 
tsp.plot_route(tsp.cities, r10)


 
tsp.plot_route(tsp.cities, np.arange(70))
Route: [ 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47
 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69]

Distance: 36.79773890173411

  
 
array([ 0, 12, 68,  4, 57, 27, 60, 63, 26, 17, 25, 56, 37, 43,  1, 46, 40,
       59, 44, 31, 47, 19, 48,  9, 24, 15, 35, 67, 52,  6, 58, 38, 10, 14,
       41, 39, 61, 18,  7,  2, 28, 49, 54, 55, 65, 30, 42, 11, 62, 66, 29,
       20, 64, 50, 36, 21,  5, 34, 16,  3, 33, 45, 22, 13, 32,  8, 23, 51,
       53, 69])

tsp.plot_route(tsp.cities, r)
Route: [ 0 12 68  4 57 27 60 63 26 17 25 56 37 43  1 46 40 59 44 31 47 19 48  9
 24 15 35 67 52  6 58 38 10 14 41 39 61 18  7  2 28 49 54 55 65 30 42 11
 62 66 29 20 64 50 36 21  5 34 16  3 33 45 22 13 32  8 23 51 53 69]

Distance: 7.540527208219586





tsp.cities = 
array([[0.37454012, 0.95071431],
       [0.73199394, 0.59865848],
       [0.15601864, 0.15599452],
       [0.05808361, 0.86617615],
       [0.60111501, 0.70807258],
       [0.02058449, 0.96990985],
       [0.83244264, 0.21233911],
       [0.18182497, 0.18340451],
       [0.30424224, 0.52475643],
       [0.43194502, 0.29122914],
       [0.61185289, 0.13949386],
       [0.29214465, 0.36636184],
       [0.45606998, 0.78517596],
       [0.19967378, 0.51423444],
       [0.59241457, 0.04645041],
       [0.60754485, 0.17052412],
       [0.06505159, 0.94888554],
       [0.96563203, 0.80839735],
       [0.30461377, 0.09767211],
       [0.68423303, 0.44015249],
       [0.12203823, 0.49517691],
       [0.03438852, 0.9093204 ],
       [0.25877998, 0.66252228],
       [0.31171108, 0.52006802],
       [0.54671028, 0.18485446],
       [0.96958463, 0.77513282],
       [0.93949894, 0.89482735],
       [0.59789998, 0.92187424],
       [0.0884925 , 0.19598286],
       [0.04522729, 0.32533033],
       [0.38867729, 0.27134903],
       [0.82873751, 0.35675333],
       [0.28093451, 0.54269608],
       [0.14092422, 0.80219698],
       [0.07455064, 0.98688694],
       [0.77224477, 0.19871568],
       [0.00552212, 0.81546143],
       [0.70685734, 0.72900717],
       [0.77127035, 0.07404465],
       [0.35846573, 0.11586906],
       [0.86310343, 0.62329813],
       [0.33089802, 0.06355835],
       [0.31098232, 0.32518332],
       [0.72960618, 0.63755747],
       [0.88721274, 0.47221493],
       [0.11959425, 0.71324479],
       [0.76078505, 0.5612772 ],
       [0.77096718, 0.4937956 ],
       [0.52273283, 0.42754102],
       [0.02541913, 0.10789143],
       [0.03142919, 0.63641041],
       [0.31435598, 0.50857069],
       [0.90756647, 0.24929223],
       [0.41038292, 0.75555114],
       [0.22879817, 0.07697991],
       [0.28975145, 0.16122129],
       [0.92969765, 0.80812038],
       [0.63340376, 0.87146059],
       [0.80367208, 0.18657006],
       [0.892559  , 0.53934224],
       [0.80744016, 0.8960913 ],
       [0.31800347, 0.11005192],
       [0.22793516, 0.42710779],
       [0.81801477, 0.86073058],
       [0.00695213, 0.5107473 ],
       [0.417411  , 0.22210781],
       [0.11986537, 0.33761517],
       [0.9429097 , 0.32320293],
       [0.51879062, 0.70301896],
       [0.3636296 , 0.97178208]])



tsp.cities = 
array([[69, 36],
       [33, 72],
       [59, 64],
       [87, 91],
       [46, 92],
       [66, 61],
       [17, 29],
       [52, 58],
       [95, 76],
       [69, 53]])

       
tsp.plot_route(tsp.cities, arange(10))
Route: [0 1 2 3 4 5 6 7 8 9]

Distance: 482.73951842174586

C10 = tsp.cities
r10 = r
r = array([0, 2, 4, 6, 3, 7, 8, 1, 5, 9])



'''


