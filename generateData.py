import os
import cv2
import pickle
import numpy
import numpy as np 
import matplotlib.pyplot as plt

from math import floor
from glob import glob
from scipy import interpolate
from PIL import Image, ImageDraw
from scipy.interpolate import splprep, splev

# Define image dimensions
IMAGE_HEIGHT = 80 
IMAGE_WIDTH = 120

# Generates a image and draws a polygon with the given co-ordinates
def maskpolygon(coordinates):
	# Get an image with L mode: 8-bit pixels, black and white 
	# of desired resolution
	img = Image.new('L', (IMAGE_HEIGHT, IMAGE_WIDTH), 0)
	ImageDraw.Draw(img).polygon(coordinates, outline=1, fill=1)
	mask = np.array(img)
	return mask

# used to generate a Spline  around given polygon co-ordinates
def maskSpline(coordinates):
	# Get an image with L mode: 8-bit pixels, black and white 
	# of desired resolution
	img = Image.new('L', (IMAGE_WIDTH, IMAGE_HEIGHT), 0)
	mask = np.array(img)

	# Split x,y co-ordinates into lists
	x_coordinates = [ x[0] for x in coordinates ]
	y_coordinates = [ x[1] for x in coordinates ]
	points = [ x_coordinates, y_coordinates ]

	# Generate a spline curve fitting the points provided
	tck, u = splprep(points, u=None, s=0.0, per=1) 
	u_new = np.linspace(u.min(), u.max(), 1000)

	# Generate pixels for spline region
	x, y = splev(u_new, tck, der=0)
	x = x.astype(int)
	y = y.astype(int)

	# Exception handling for spline going out of bounds
	x[x >= IMAGE_HEIGHT] = IMAGE_HEIGHT-1
	y[y >= IMAGE_WIDTH] = IMAGE_WIDTH-1
	

	pts = np.array([x,y]).T

	# mark boundary by value 1 in grayscale
	for i in range(len(x)):
		mask[x[i]][y[i]] = 1


	# fill mask using scanline  algorithm
	for i in range(80):
		itemindex = np.where(mask[i]==1)
		if len(itemindex[0])>1:
			ind = np.array(itemindex[0])
			#  make all 1's between boundaries
			mask[i][ind[0]:ind[-1]+1]=1
	return mask
	
# return orginal image masked with mask generated
def returnAnd(im,mask):
	tem=im
	tem[:,:,0] = im[:,:,0] * mask
	tem[:,:,1] = im[:,:,1] * mask
	tem[:,:,2] = im[:,:,2] * mask
	return tem

# Segments Iris given masks or pupil, iris, lids
def segmentIris(pupilMask, irisMask, lidsMask):
	if pupilMask.shape == irisMask.shape ==\
		lidsMask.shape == (IMAGE_HEIGHT, IMAGE_WIDTH):
		return (lidsMask*(irisMask-pupilMask))
	return None


images = sorted([y for x in os.walk('./SynthEyes_data/') for y in glob(os.path.join(x[0], '*.png'))])
landmarks = sorted([y for x in os.walk('./SynthEyes_data/') for y in glob(os.path.join(x[0], '*.pkl'))])


for x,y in zip(images,landmarks):
	# #open the landmarks for the image 
	x = pickle.load(open(y,'rb'))
	y = x['ldmks']['ldmks_iris_2d']
	k=[]
	for  l in y:
		k.append((floor(l[1]),floor(l[0])))

	irisMask = maskSpline(coordinates = k)
	
	y = x['ldmks']['ldmks_lids_2d']
	t =[]
	for  l in y:
		t.append((floor(l[1]),floor(l[0])))

	lidsMask = maskSpline(coordinates = t)
	y = x['ldmks']['ldmks_pupil_2d']
	t =[]
	for  l in y:
		t.append((floor(l[1]),floor(l[0])))
	pupilMask = maskSpline(coordinates = t)

	segmented = segmentIris(pupilMask, irisMask, lidsMask)
	plt.imshow(segmented, cmap='gray')
	plt.show()
	break