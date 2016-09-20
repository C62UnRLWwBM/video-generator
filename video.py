# Video functions

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Generate a video with a still cross at the center
def gen_cross(vid, dim, length, thickness, frames):
	img = Image.new('RGB', dim, (255, 255, 255))
	draw = ImageDraw.Draw(img)
	draw.rectangle(((int((dim[0]-thickness)/2),int((dim[1]-length)/2)),(int((dim[0]+thickness)/2),int((dim[1]+length)/2))),(0,0,0))
	draw.rectangle(((int((dim[0]-length)/2),int((dim[1]-thickness)/2)),(int((dim[0]+length)/2),int((dim[1]+thickness)/2))),(0,0,0))
	for i in range(frames):
		vid.write(cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB))

# Generate video of img moving toward the viewer, getting less blurry and bigger
def gen_moving(vid, img, dim=(400,400), frames=250, blur=10, s=0.25):
	if frames == 0:
		return

	if frames == 1:
		new_im = Image.new('RGB', dim, (255, 255, 255))
		new_im.paste(img, tuple(x//2 for x in np.subtract(dim, img.size)))
		vid.write(cv2.cvtColor(np.array(new_im), cv2.COLOR_BGR2RGB))
		return

	for i in range(0, frames):
		print(i)
		newdim = tuple(int(x*(1.0*s+1.0*i*(1-s)/(frames-1))) for x in img.size)

		resized = img.resize(newdim, Image.ANTIALIAS) # Resize text img

		new_im = Image.new('RGB', dim, (255, 255, 255))
		new_im.paste(resized, tuple(x//2 for x in np.subtract(dim, newdim))) # Paste it into image of right dimensions

		#blurred = new_im.filter(ImageFilter.GaussianBlur(blur*(1.0+1.0*i/(1-frames)))) # Blurring
		vid.write(cv2.cvtColor(np.array(new_im), cv2.COLOR_BGR2RGB))

# Generate scaled original image from an existing image
def gen_orig_img(dim, img):
	imgdim = img.size
	imgdim = tuple(int(min(0.8*dim[0]/imgdim[0], 0.8*dim[1]/imgdim[1]) * x) for x in imgdim)
	return img.resize(imgdim, Image.ANTIALIAS)

# Generate original image from text
def gen_orig_text(dim, text):
	fontsize = 0
	textdim = (0,0)
	while textdim[0] < 0.8*dim[0]:
		fontsize += 1
		fnt = ImageFont.truetype('/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf', fontsize)
		textdim = tuple(sum(x) for x in zip(fnt.font.getsize(text)[0], fnt.font.getsize(text)[1]))
	img = Image.new('RGB', textdim, (255, 255, 255))
	draw = ImageDraw.Draw(img)
	draw.text((0,0), text, (0,0,0), fnt)
	return img

# This function generates an ffmpeg command for combining multiple videos in a grid.
# The bulk of the code is for generating the filtergraph
# size: size of grid
# dim: dimensions of each tile
# padding arguments refer to the amount of padding between tiles, and how often to insert padding
def gen_ffmpeg_args_grid(name, size, dim, padding, padding_horiz_freq, padding_vert_freq, fps):
	ffmpeg_args=['ffmpeg']

        # Input files
	for i in range(size[0]):
		for j in range(size[1]):
			ffmpeg_args.append('-i')
			ffmpeg_args.append(name+'_'+'{0:0=3d}'.format(i)+'_'+'{0:0=3d}'.format(j)+'.webm')

	ffmpeg_args.append('-filter_complex')

	# This is in filtergraph syntax and uses hstack and vstack filters to combine the tiles
	# https://ffmpeg.org/ffmpeg-filters.html
	filtergraph = ''
	if size[0] != 1 and size[1] != 1:
		if padding > 0:
			# Horizontal padding
			if padding_horiz_freq < size[1]:
				filtergraph += 'color=c=black:s=' + str(padding) + 'x' + str(dim[1]) + ':r=' + str(fps) + ',split='
				filtergraph += str(size[0]*((size[1] - 1)//padding_horiz_freq))
				for i in range(size[0]*((size[1] - 1)//padding_horiz_freq)):
					filtergraph += '[c' + str(i) + ']'
				filtergraph += ';'

			# Vertical padding
			if padding_vert_freq < size[0]:
				filtergraph += 'color=c=black:s=' + str(dim[0]*size[1]+padding*((size[1]-1)//padding_horiz_freq)) + 'x' + \
						str(padding) + ':r=' + str(fps) + ',split='
				filtergraph += str((size[0] - 1)//padding_vert_freq)
				for i in range((size[0] - 1)//padding_vert_freq):
					filtergraph += '[d' + str(i) + ']'
				filtergraph += ';'

		for i in range(size[0]):
			for j in range(size[1]):
				filtergraph += '[' + str(size[1]*i+j) + ':v]'
				if padding > 0 and j != size[1] - 1 and (j + 1)%padding_horiz_freq == 0:
					filtergraph += '[c' + str(i*((size[1]-1)//padding_horiz_freq) + (j+1)//padding_horiz_freq - 1) + ']'
			filtergraph += 'hstack='
			if padding > 0:
				filtergraph += str(size[1]+(size[1] - 1)//padding_horiz_freq)
			else:
				filtergraph += str(size[1])
			filtergraph += ':1'
			filtergraph += '[v' + str(i) + '];'

		for i in range(size[0]):
			filtergraph += '[v' + str(i) + ']'
			if padding > 0 and i != size[0] - 1 and (i + 1)%padding_vert_freq == 0:
				filtergraph += '[d' + str((i+1)//padding_vert_freq - 1) + ']'
		filtergraph += 'vstack='
		if padding > 0:
			filtergraph += str(size[0]+(size[0] - 1)//padding_vert_freq)
		else:
			filtergraph += str(size[0])
		filtergraph += ':1'

	elif size[0] != 1 or size[1] != 1:
		if padding > 0:
			if size[0] == 1:
				padding_freq = padding_horiz_freq
			else:
				padding_freq = padding_vert_freq
			if padding_freq < size[0]*size[1]:
				filtergraph += 'color=c=black:s='
				if size[0] == 1:
					filtergraph += str(padding) + 'x' + str(dim[1])
				else:
					filtergraph += str(dim[0]) + 'x' + str(padding)
				filtergraph += ':r=' + str(fps) + ',split='
				padding_num = (size[0]*size[1] - 1)//padding_freq
				filtergraph += str(padding_num)
				for i in range(padding_num):
					filtergraph += '[c' + str(i) + ']'
				filtergraph += ';'

		for i in range(size[0]*size[1]):
			filtergraph += '[' + str(i) + ':v]'
			if padding > 0 and i != size[0]*size[1]-1 and (i+1)%padding_freq == 0:
				filtergraph += '[c' + str((i+1)//padding_freq - 1) + ']'
		if size[0] == 1:
			filtergraph += 'h'
		else:
			filtergraph += 'v'
		filtergraph += 'stack='
		if padding > 0 and padding_freq < size[0]*size[1]:
			filtergraph += str(size[0]*size[1] + padding_num)
		else:
			filtergraph += str(size[0]*size[1])
		filtergraph += ':1'

	ffmpeg_args.append(filtergraph)

	ffmpeg_args.append('-speed')
	ffmpeg_args.append('16')
	ffmpeg_args.append('-quality')
	ffmpeg_args.append('realtime')
	ffmpeg_args.append('-c:v')
	ffmpeg_args.append('libvpx') # Use VP8 instead of VP9

	ffmpeg_args.append(name + '.webm')

	return ffmpeg_args

def gen_ffmpeg_args_concat(dirname, name, count):
	txtfile = dirname + '/' + name + '.txt'
	with open(txtfile, 'w') as f:
		for i in range(count):
			print("file '" + name + '_' + str(i) + ".webm'", file=f)

	return ['ffmpeg', '-f', 'concat', '-i', txtfile, '-c', 'copy', name + '.webm']
