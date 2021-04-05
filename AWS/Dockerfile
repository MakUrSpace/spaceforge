FROM public.ecr.aws/lambda/python:3.8

COPY VatDrain.scad ./
RUN yum -y groupinstall "Development Tools"
RUN yum -y install amazon-linux-extras wget vim cmake git python3 python3-devel tar bzip2 bzip2-devel
RUN yum -y install glew glew-devel openssl openssl-devel
RUN wget https://github.com/Kitware/CMake/releases/download/v3.20.0/cmake-3.20.0.tar.gz
RUN tar -zxf cmake-3.20.tar.gz
RUN cd cmake-3.20 && ./bootstrap && make && make install && cd ~
RUN git clone https://code.qt.io/qt/qt5.git
RUN cd qt5 && git checkout 5.12 && perl init-repository
RUN cd ~ && mkdir qt5-build && cd qt5-build && ../qt5/configure -confirm-license -developer-build -opensource -nomake examples -nomake tests
RUN cd ~/qt5-build && make && make install
RUN echo 'export PATH=/root/qt5-build/qtbase/bin:$PATH' > ~/.bashrc
RUN wget https://dl.bintray.com/boostorg/release/1.74.0/source/boost_1_74_0.tar.gz
RUN git clone https://github.com/openscad/openscad.git
COPY spaceforge.py ./

CMD ["spaceforge.lambda_handler"]
