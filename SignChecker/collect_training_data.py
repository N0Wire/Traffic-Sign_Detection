import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
from selective_search import SelectiveSearch
import time
import pickle
import multiprocessing as mp

#Intersection over Union
def overlap(box1, box2):
	area1 = (box1[2]-box1[0])*(box1[3]-box1[1])
	area2 = (box2[2]-box2[0])*(box2[3]-box2[1])
	
	#intersection region
	miny = max(box1[0], box2[0])
	minx = max(box1[1], box2[1])
	maxy = min(box1[2], box2[2])
	maxx = min(box1[3], box2[3])
	
	intersect = max(0, maxy-miny)*max(0, maxx-minx)
	total_area = float(area1+area2-intersect) #don't count area 2 times
	
	return intersect/total_area

#parse file
def collect(start_index, num_bb, run_num):
	path = "../Data/FullIJCNN2013/"
	savepath = "Localization/"
	infos = pd.read_csv(path + "gt.txt", delimiter=";", header=None)

	found_boxes = [] #list of all bounding boxes found
	best_overlapps = np.zeros(len(infos)) #contains best overlap score(IoU) for bounding box
	times = np.zeros(900) #contains time needed for selective search on every image
	index = start_index #index for current entry of GT-Data (because one image can obtain multiple objects)
	t_index = 0	#index for time data (= image index)
	while index<len(infos):
		j = index
		name = infos[0][index] #current image file
		rectangles = [] #GT-Data for current image
		overlap_boxes = []	#best matching boxes found by Selective Search
		#look how many bounding boxes are in this picture to find
		while j<len(infos):
			if infos[0][j] == name: #if name isn't the same -> new image -> is handled next iteration
				temp = [infos[2][j], infos[1][j], infos[4][j], infos[3][j]] #identical format, compared to Selective Search output
				rectangles.append(temp)
				overlap_boxes.append([0,0,0,0]) #dummy bounding box
			else:
				break
			j += 1
		
		#print("Evaluating " + name)
		#run selective search and obtain bounding boxes
		img = plt.imread(path+name)
		
		start = time.time()
		ss = SelectiveSearch()
		boxes = ss.run(img, "deep")#, "fast")
		stop = time.time()
		found_boxes.append(boxes) 
		times[t_index] = (stop-start)
		t_index += 1
		
		#determine best overlapp
		for i,r in enumerate(rectangles):
			for b in boxes:
				score = overlap(r, b)
				if score > best_overlapps[index+i]:
					best_overlapps[index+i] = score
					overlap_boxes[i] = b
		
		
		index += len(rectangles)
		
		plt.figure(1, dpi=100, figsize=(13.6,8.0))
		plt.clf()
		plt.axis("off")
		plt.imshow(img)
		
		for r in rectangles: #given rectangles
			rect = patches.Rectangle((r[1], r[0]),np.abs(r[3]-r[1]), np.abs(r[2]-r[0]), linewidth=1, edgecolor="g", facecolor="none")
			plt.gca().add_patch(rect)
		for b in overlap_boxes: #best matching bounding boxes
			rect = patches.Rectangle((b[1], b[0]),np.abs(b[3]-b[1]), np.abs(b[2]-b[0]), linewidth=1, edgecolor="r", facecolor="none")
			plt.gca().add_patch(rect)
		plt.savefig(savepath + name[0:len(name)-3] + "png") #can't save as ppm
		
		if index >= num_bb+(start_index):
			break

	#reduce data
	best_overlapps = np.array(best_overlapps[0:index])
	times = np.array(times[0:t_index])

	#save data for later use
	np.save("Localization/overlap_"+str(run_num)+".npy", best_overlapps)
	np.save("Localization/time_"+str(run_num)+".npy", times)
	f = open("Localization/boxes_"+str(run_num)+".dat", "wb")
	pickle.dump(found_boxes,f)
	f.close()


#per "batch" 100 signs (not equal 100 images!)
#start_values =  [[0,20,1],[20,19,2],[39,20,3],[59,21,4],[80,20,5]]
start_values =  [[100,20,6],[120,20,7],[140,20,8],[160,21,9],[181,19,10]]
#start_values =  [[200,20,11],[220,20,12],[240,20,13],[260,22,14],[282,18,15]]

#output = mp.Queue()
procs = []
for v in start_values:
	p = mp.Process(target=collect, args=(v[0], v[1], v[2]))
	procs.append(p)

for i,p in enumerate(procs):
	print("Start " + str(start_values[i][2]))
	p.start()

for p in procs:
	p.join()
