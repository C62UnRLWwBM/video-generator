# Video generator

The script `make_video.py` generates videos from a JSON file. See sample.json
for the structure of the input. The images used are taken from the
[PASCAL VOC2012](http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html)
dataset.

## Dependencies

* [Python 3](https://www.python.org/)
* [FFmpeg](https://ffmpeg.org/)
* [NumPy](http://www.numpy.org/)
* [OpenCV 3](http://opencv.org/) (with Python 3 bindings)
* [Pillow](https://python-pillow.org/)

# experiment.lua

This is the script for recording keypresses. See inside for instructions. It
runs inside the video player [mpv](https://mpv.io/).
