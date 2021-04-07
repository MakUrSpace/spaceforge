FROM public.ecr.aws/lambda/python:3.8
WORKDIR /root

RUN yum -y groupinstall "Development Tools" && yum -y install wget

RUN wget -O epel.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum -y install ./epel.rpm

RUN yum -y install amazon-linux-extras vim cmake git python3 python3-devel tar bzip2 bzip2-devel glew glew-devel openssl openssl-devel sed xz-utils cairo cairo-devel libxml2 libxml2-devel lib3mf lib3mf-devel double-conversion double-conversion-devel eigen3 eigen3-devel opencsg opencsg-devel mpfr mpfr-devel gmp gmp-devel glib2 glib2-devel fontconfig fontconfig-devel harfbuzz harfbuzz-devel libzip libzip-devel gzip

RUN git clone https://gitlab.kitware.com/cmake/cmake.git && cd cmake && ./bootstrap && make -j4 && make install

RUN git clone https://code.qt.io/qt/qt5.git && cd qt5 && git checkout 5.12 && perl init-repository
RUN mkdir qt5-build && cd qt5-build && ../qt5/configure -confirm-license -developer-build -opensource -nomake examples -nomake tests
RUN cd qt5-build && make -j4 && make install
RUN export PATH="/root/qt5-build/qtbase/bin:${PATH}"
RUN echo 'export PATH=/root/qt5-build/qtbase/bin:$PATH' > ~/.bashrc

RUN wget https://dl.bintray.com/boostorg/release/1.74.0/source/boost_1_74_0.tar.gz && tar -zxf boost_1_74_0.tar.gz && cd boost_1_74_0 && ./bootstrap.sh && ./b2 install

RUN wget https://github.com/CGAL/cgal/releases/download/releases%2FCGAL-4.9.1/CGAL-4.9.1.tar.xz
RUN tar -xf CGAL-4.9.1.tar.xz && cd CGAL-4.9.1 && cmake . && make -j4 && make install

RUN wget https://www.riverbankcomputing.com/static/Downloads/QScintilla/2.11/QScintilla_gpl-2.11.tar.gz && tar -zxf QScintilla_gpl-2.11.tar.gz
RUN cd QScintilla_gpl-2.11/Qt4Qt5 && qmake qscintilla.pro && make -j4 && make install
RUN export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && echo 'export LD_LIBRARY_PATH:/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
 
RUN git clone https://github.com/openscad/openscad.git
RUN cd openscad && qmake openscad.pro
RUN sed -i 's/-mt//g' openscad/Makefile 
RUN cd openscad && make -j4 && make install

COPY spaceforge.py ./
CMD ["spaceforge.lambda_handler"]
