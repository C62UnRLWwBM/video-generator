#!/usr/bin/env python3
# Generate video from JSON config file

import cv2
from PIL import Image
import argparse, json, subprocess, tempfile, threading
import video

# Generate file with static cross
def gen_cross_file(name, dim, length, thickness, frames, fps=25):
	vid = cv2.VideoWriter(name + '.webm', cv2.VideoWriter_fourcc(*'VP80'), fps, dim)
	video.gen_cross(vid, dim, length, thickness, frames)
	vid.release()

# Generate video for one rectangle, composed of multiple moving videos
def gen_tile(name, dim, cfg, fps=25):
	vid = cv2.VideoWriter(name + '.webm', cv2.VideoWriter_fourcc(*'VP80'), fps, dim)
	for i in cfg:
		if i['type'] == 'image':
			video.gen_moving(vid, video.gen_orig_img(dim, Image.open(i['image'])), dim, i['frames'])
		else:
			video.gen_moving(vid, video.gen_orig_text(dim, i['text']), dim, i['frames'])
	vid.release()

# Generate grid section from config
def gen_grid(name, cfg, fps=25):
	dim = (cfg['width'], cfg['height'])
	if cfg['rows'] == 1 and cfg['columns'] == 1:
		gen_tile(name, dim, cfg['tiles'][0][0], fps)
	else:
		threads = [] # each tile video is generated in a separate thread
		for i in range(cfg['rows']):
			for j in range(cfg['columns']):
				filename = name + '_' + '{0:0=3d}'.format(i) + '_' + '{0:0=3d}'.format(j)
				threads.append(threading.Thread(target=gen_tile, args=(filename, dim, cfg['tiles'][i][j], fps)))
				threads[-1].start()
		for t in threads:
			t.join()

		ffmpeg_args = video.gen_ffmpeg_args_grid(name, (cfg['rows'], cfg['columns']), dim, cfg['padding'], cfg['padding_horiz_freq'], cfg['padding_vert_freq'], fps)
		print("ffmpeg args: " + str(ffmpeg_args))
		subprocess.call(ffmpeg_args) # run ffmpeg

# Generate entire video from config
def gen_video(config, output):
	with tempfile.TemporaryDirectory() as tmpdir:
		for idx, val in enumerate(config['sequence']):
			if val['type'] == 'cross':
				gen_cross_file(tmpdir + '/' + output + '_' + str(idx), (config['width'], config['height']), val['length'], val['thickness'], val['frames'], config['fps'])
			else:
				gen_grid(tmpdir + '/' + output + '_' + str(idx), val, config['fps'])
		subprocess.call(video.gen_ffmpeg_args_concat(tmpdir, output, len(config['sequence'])))

p = argparse.ArgumentParser()
p.add_argument('config', type=str, help='config file for generating video')
p.add_argument('output', type=str, help='output video basename')
args = p.parse_args()

with open(args.config) as config_file:
	gen_video(json.load(config_file), args.output)
