FROM ubuntu:latest
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install git -y
RUN apt-get update
RUN apt-get install python3.8 -y --fix-missing
RUN apt install python3-pip -y

RUN git clone https://github.com/xWasp97x/Greenhouse.git
WORKDIR ./Greenhouse

CMD /bin/sh entrypoint.sh