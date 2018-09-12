import cv2, sched, time, sys, os, requests, json, re
from subprocess import call
import firebase_admin
from firebase_admin import credentials, db
from six.moves import configparser
import six

print('Initialising...')

# Read config
if six.PY2:
    config = configparser.ConfigParser()
    config.read('config.ini')
    database_url = config.get('db', 'url')
    db_root = config.get('db', 'root')
    nalunet_url = config.get('nalunet', 'url')
else:
    config = configparser.ConfigParser(default_section=None)
    config.read('config.ini')
    database_url = config['db']['url']
    db_root = config['db']['root']
    nalunet_url = config['nalunet']['url']

# Setup: Firebase - Realtime Database (Note: We are not using Firestore)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase.json"
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : database_url
})
root = db.reference()

# Setup: Scheduler + vars
s = sched.scheduler(time.time, time.sleep)
failures = 0
cam_index = 0
restarted = True if 'restarted' in sys.argv else False
nalunet_url += '?cam=true' if 'cam' in sys.argv else '' # Optional JSON "img" debugger
fswebcam = True if 'fswebcam' in sys.argv else False # Use "fswebcam" arg to avoid using OpenCV
filename = 'snap.png'

# Setup: Webcam (OpenCV)
if not fswebcam:
    print('Webcam Starting...')
    cam = cv2.VideoCapture(cam_index)

def update_count(count):
    nalus_ref = root.child(db_root)
    nalus_ref.update({'count' : count})

def get_count():
	return root.child('nalus').get()

def run_opencv(sc):
    global failures
    global cam_index
    global cam
    global filename

    # Auto healing
    if failures >= 5:
        # Try to fix
        print ("Trying to fix...")
        if cam != None:
            cam.release()
            del cam
        cam = cv2.VideoCapture(cam_index)

    elif failures >= 10 and restarted == False:
        # Restart myself
        print ("Restarting myself...")
        os.execl('restart.sh', '')
        sys.exit()
    
    try:
        print('Snapping...')
        ret, frame = cam.read()
        
        if ret:
            # Take a snap
            cv2.imwrite(filename, frame)

            # Send to service
            print('- Detect')
            url = nalunet_url
            files = {'file': open(filename, 'rb')}
            r = requests.post(url, files=files)
            
            if 'cam' in sys.argv:
                print (r.text)

            bad_response = re.sub(r',? ?"img" ?: ?".*"', '', r.text, flags=re.S)
            response = json.loads(bad_response)
            
            # Store count
            if ('error' in response):
                print('- Error: ' + response['error'])
            else:
                print('- Count: ' + str(response['count']))
                update_count(response['count'])
                print('- Updated!')

            # Remove image
            os.remove(filename)

            # Schedule next execution
            print("Sleeping for a few seconds...\n")
            failures = 0
            s.enter(10, 1, run_opencv, (sc,))

        else:
            # Failed, schedule again in 10 seconds to see if it works...
            print('Failed to snap! Sleeping for a few seconds...')
            failures += 1
            if cam_index == -1:
                print ("Trying webcam index 0")
                cam_index = 0
            else:
                print ("Trying webcam index 1")
                cam_index = -1
            s.enter(10, 1, run_opencv, (sc,))

    except Exception as inst:
        # Failed, schedule again in 10 seconds to see if it works...
        print ('Exception:')
        print (inst)
        print ('Sleeping for a few seconds...')
        failures += 1
        s.enter(10, 1, run_opencv, (sc,))

def run_fswebcam(sc):
    global filename

    try:
        print('Snapping...')
        call(["fswebcam -r 1280x720 --no-banner " + filename], shell=True)

        # Send to service
        print('- Detect')
        url = nalunet_url
        files = {'file': open(filename, 'rb')}
        r = requests.post(url, files=files)
        
        if 'cam' in sys.argv:
            print (r.text)
        
        bad_response = re.sub(r',? ?"img" ?: ?".*"', '', r.text, flags=re.S)
        response = json.loads(bad_response)
            
        # Store count
        if ('error' in response):
            print('- Error: ' + response['error'])
        else:
            print('- Count: ' + str(response['count']))
            update_count(response['count'])
            print('- Updated!')

        # Remove image
        os.remove(filename)

        # Schedule next execution
        print("Sleeping for a few seconds...\n")
        failures = 0
        s.enter(10, 1, run_fswebcam, (sc,))

    except Exception as inst:
        # Failed, schedule again in 10 seconds to see if it works...
        print ('Exception:')
        print (inst)
        print ('Sleeping for a few seconds...')
        s.enter(10, 1, run_fswebcam, (sc,))

# Start program
try:
    if fswebcam:
        # FSWebCam mode
        s.enter(10, 1, run_fswebcam, (s,))
        s.run()

    else:
        # OpenCV mode
        s.enter(0, 1, run_opencv, (s,))
        s.run()

except KeyboardInterrupt:
    # Exit
    if not fswebcam:
        cam.release()
    sys.exit()
