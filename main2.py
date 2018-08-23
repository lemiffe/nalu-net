import cv2
import sched, time

# Setup
s = sched.scheduler(time.time, time.sleep)
cam = cv2.VideoCapture(0)

def snap(sc):
    ret, frame = cam.read()
    if ret:
        img_name = "snap.png"
        cv2.imwrite(img_name, frame)
        print("Written!")
        s.enter(5, 1, snap, (sc,))

s.enter(5, 1, snap, (s,))
s.run()

cam.release()
print("dead")
