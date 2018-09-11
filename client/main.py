import cv2, sched, time, sys, os, requests, json, re
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

# Add optional JSON "img" debugger
nalunet_url += '?cam=true' if 'cam' in sys.argv else ''

# If we are using another program to take "snap.png" pictures, you can send "camless" param to avoid taking pictures here
camless = True if 'camless' in sys.argv else False

# Setup: Firebase - Realtime Database (Note: We are not using Firestore)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase.json"
cred = credentials.Certificate("firebase.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : database_url
})
root = db.reference()

# Setup
s = sched.scheduler(time.time, time.sleep)
failures = 0
cam_index = 0
restarted = True if 'restarted' in sys.argv else False

# Setup: Webcam
if not camless:
    print('Webcam Starting...')
    cam = cv2.VideoCapture(cam_index)

def update_count(count):
    nalus_ref = root.child(db_root)
    nalus_ref.update({'count' : count})

def get_count():
	return root.child('nalus').get()

def snap(sc):
    global failures
    global cam_index
    global cam

    # Auto healing
    if failures >= 20 and restarted == True:
        # Reboot the machine :P
        print ("Reboot...")
        os.execl('sudo reboot.sh', '')

    elif failures >= 5:
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
            img_name = 'snap.png'
            cv2.imwrite(img_name, frame)

            # Send to service
            print('- Detect')
            url = nalunet_url
            files = {'file': open('snap.png', 'rb')}
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
            os.remove("snap.png")

            # Schedule next snap
            print("Sleeping for a few seconds...\n")
            failures = 0

            # Schedule next snap
            s.enter(10, 1, snap, (sc,))

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
            s.enter(10, 1, snap, (sc,))

    except Exception as inst:
        # Failed, schedule again in 10 seconds to see if it works...
        print ('Exception:')
        print (inst)
        print ('Sleeping for a few seconds...')
        failures += 1
        s.enter(10, 1, snap, (sc,))

def detect_only(sc):
    try:
        # Send to service
        print('- Detect')
        url = nalunet_url
        files = {'file': open('snap.png', 'rb')}
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

        # Schedule next execution
        s.enter(10, 1, detect_only, (sc,))

    except Exception as inst:
        # Failed, schedule again in 10 seconds to see if it works...
        print ('Exception:')
        print (inst)
        print ('Sleeping for a few seconds...')
        s.enter(10, 1, detect_only, (sc,))

# Start snapping
try:

    if camless:
        # Detection only
        s.enter(10, 1, detect_only, (s,))
        s.run()

    else:
        # Standard operation
        s.enter(0, 1, snap, (s,))
        s.run()

except KeyboardInterrupt:
    # Exit
    if not camless:
        cam.release()
    sys.exit()
