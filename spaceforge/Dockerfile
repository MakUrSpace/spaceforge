FROM public.ecr.aws/lambda/python:3.9
WORKDIR /root

RUN yum -y groupinstall "Development Tools" && yum -y install wget

RUN wget -O epel.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN yum -y install ./epel.rpm

RUN yum -y install amazon-linux-extras python3 python3-devel tar bzip2 bzip2-devel glew glew-devel openssl openssl-devel sed xz-utils cairo cairo-devel libxml2 libxml2-devel lib3mf lib3mf-devel double-conversion double-conversion-devel eigen3 eigen3-devel opencsg opencsg-devel mpfr mpfr-devel gmp gmp-devel glib2 glib2-devel fontconfig fontconfig-devel harfbuzz harfbuzz-devel libzip libzip-devel gzip

RUN python -m pip install solidpython boto3

COPY local_lib /usr/local/
COPY local_qt_lib /usr/local/lib/qtlib
ENV LD_LIBRARY_PATH="/usr/local/lib:/usr/local/lib/qtlib:${LD_LIBRARY_PATH}"
COPY openscad ${LAMBDA_TASK_ROOT}
COPY sf_operations.py ${LAMBDA_TASK_ROOT}
COPY spaceforge.py ${LAMBDA_TASK_ROOT}

RUN chmod o+rx /root
CMD [ "spaceforge.lambda_handler" ]
