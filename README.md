# NaluNet

Nalu Detection System built in Python3 + Darknet + Yolo V3


## Server (Darknet + Flask)

Details:
- Flask API + Darknet + Yolo V3 + Nalu Model
- It's purpose is when you call the endpoint with an image it will return the count of Nalu's it finds
- It has no data retention and no 3rd party calls

Installing:
- cd server
- docker build -t nalunet .
- docker run -p 3038:80 nalunet
- Or on production: docker run -p 3038:80 -p 80:80 -d nalunet

Running:
- curl -F "file=@/Users/user/Desktop/dog.png" localhost:3038


## Client (Webcam + Detect)

Details:
- Python3 + OpenCV
- It's purpose is to take a picture from a webcam periodically, call the server's endpoint, store the count (locally or in firebase), and delete the picture

Installation:
- pip3 install firebase_admin
- Method 1 (Raspberry PI): fswebcam (instead of OpenCV)
	- This method is to be used if you don't have as powered USB hub (webcam + opencv + v4l can be flaky)
	- sudo apt-get install fswebcam
	- When running the client add "fswebcam" to the args, e.g. `python main.py fswebcam`
- Method 2 (OSX): OpenCV installation
	- brew install opencv
	- echo /usr/local/opt/opencv/lib/python3.6/site-packages >> /usr/local/lib/python3.6/site-packages/opencv3.pth
- Method 3: OpenCV on Debian/Ubuntu (only if using the python script for the webcam instead of the script from "Method 1")
	- https://milq.github.io/install-opencv-ubuntu-debian/
	- Or try pip install opencv
	- Crontab: `@reboot cd /home/pi/nalu-net/client && python main.py &`

Running locally:
- python main.py (or python3)

Crontab:
```
Start after booting up: @reboot cd /home/pi/apps/nalu-net/client && python main.py fswebcam &
Auto-pull changes: */5 * * * * cd /home/pi/apps/nalu-net && git pull origin master

To reboot every night use sudo crontab -e: 0 1 * * * /sbin/shutdown -r
```


### Training the model

- Install "Yolo V3" (only necessary for training the model)
	- https://pjreddie.com/darknet/yolo/
- git clone https://github.com/pjreddie/darknet
- cd darknet
- make
- wget https://pjreddie.com/media/files/yolov3.weights

