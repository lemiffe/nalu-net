from flask import Flask, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
import os, socket, app, subprocess
import ascii

UPLOAD_FOLDER = '/darknet/data'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    
    count = 0
    img = None
    
    if request.method == 'POST':

        # TODO: Check Querystring
        render_image = True if request.args.get('cam') is not None else False
        
        # Did we get a file?
        if 'file' not in request.files:
            return(jsonify({"count": 0, "error": "file not in request"}))
        file = request.files['file']
        
        # If user does not select file, browser submits an empty part without filename
        if file.filename == '':
            return(jsonify({"count": 0, "error": "no filename provided"}))
        
        # Save the file
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return(jsonify({"count": 0, "error": "file does not exist"}))
        
        # Run Yolo
        output = subprocess.getoutput("cd darknet && ./darknet detect cfg/naluv1_tiny_net.cfg naluv1_tiny.weights data/" + filename + " -thresh 0.4")
        count = output.count('nalu: ')

        if render_image:
            # ASCII because... why not?
            img = ascii.handle_image_conversion('/darknet/data/' + filename)
            if img is not None:
                img = "<N>" + img.replace("\n", "<N>")

        # Remove image
        subprocess.getoutput("rm " + app.config['UPLOAD_FOLDER'] + "/" + filename)

    else:
        # Use test image
        output = subprocess.getoutput("cd darknet && ./darknet detect cfg/naluv1_tiny_net.cfg naluv1_tiny.weights data/test.jpg")
        count = output.count('nalu: ')
        
        if render_image:
            # ASCII because... why not?
            img = ascii.handle_image_conversion('/darknet/data/test.jpg')
            if img is not None:
                img = "<N>" + img.replace("\n", "<N>")
    
    response = jsonify({"count": count, "img": img})
    json_data = response.get_data(as_text=True)
    json_data_replaced = json_data.replace("<N>", "\n")
    response.set_data(json_data_replaced)
    return response

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
