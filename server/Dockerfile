FROM python:3.7
MAINTAINER Josip Janzic <josip@jjanzic.com>

RUN apt-get update && \
        apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev

RUN pip install numpy

# OPENCV

WORKDIR /
ENV OPENCV_VERSION="3.4.2"
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DWITH_CUDA=OFF \
  -DWITH_OPENGL=ON \
  -DWITH_OPENCL=ON \
  -DWITH_IPP=ON \
  -DWITH_TBB=ON \
  -DWITH_EIGEN=ON \
  -DWITH_V4L=ON \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3.7 -c "import sys; print(sys.prefix)") \
  -DPYTHON_EXECUTABLE=$(which python3.7) \
  -DPYTHON_INCLUDE_DIR=$(python3.7 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3.7 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
  .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

# DARKNET + YOLO

RUN \
  apt-get update && apt-get install -y \
  autoconf \
        automake \
  libtool \
  build-essential \
  git

RUN \
  apt-get install -y \
  wget

RUN \
  git clone https://github.com/pjreddie/darknet && \
  cd darknet && \
  make

# COPY SERVER
ADD . /

# INSTALL
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# COPY MODEL
COPY ./model/coco.names /darknet/data/
COPY ./model/naluv1_tiny_net.cfg /darknet/cfg/
COPY ./model/naluv1_tiny.weights /darknet/
COPY ./model/obj.data /darknet/data/
COPY ./model/obj.names /darknet/data/

# COPY TEST IMAGE
COPY ./model/test.jpg /darknet/data/

# START SERVER
EXPOSE 3038
CMD ["python", "app.py"]
