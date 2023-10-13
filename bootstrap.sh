#!/bin/bash
##
## Copyright 2023 EAS Group
##
## Permission is hereby granted, free of charge, to any person obtaining a copy 
## of this software and associated documentation files (the “Software”), to deal 
## in the Software without restriction, including without limitation the rights 
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
## copies of the Software, and to permit persons to whom the Software is 
## furnished to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in 
## all copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
## SOFTWARE.
##


#################### CONFIG ####################

DOCKER_IMAGE_NAME="attest"
DOCKER_IMAGE_TAG="latest"
DOCKER_FILE="dockerfile"
DOCKER_CONTAINER_NAME="attest"
MSP_SERIAL_PORT_NAME="ttyACM"
PICO_SCOPE_USB_NAME="PicoScope"

##################### END ######################

DOCKER_BUILD_CONTEXT="."
DOCKER_RUN_ARGS=""
DOCKER_MODE=""

DOCKER_COMPOSE_FILE="_docker-compose.yml"

while test $# -gt 0
do 
  case "$1" in
    (--dockerfile) DOCKER_FILE="$2"
      shift
      ;;
    (*) DOCKER_RUN_ARGS="$DOCKER_RUN_ARGS $1"
  esac
  shift
done

if [ -z $DOCKER_RUN_ARGS ]
then
  DOCKER_MODE="-d"
fi

if ! type "lsusb" > /dev/null; then
  echo "[WARN] lsusb is not installed. Try to install it from usbutils."
  apt-get update && apt-get install -y usbutils
  if ! type "lsusb" > /dev/null; then
    echo "[ERROR] Failed to install usbutils."
    exit 1
  fi
else
  echo "[INFO] lsusb is installed."
fi

if ! type "docker" > /dev/null; then
  echo "[ERROR] docker is not installed. Install docker first and run the start script again."
else
  echo "[INFO] docker is installed."
fi

echo "[INFO] Building docker image..."
docker build -t $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG "$DOCKER_BUILD_CONTEXT" -f $DOCKER_FILE
if [ $? -ne 0 ]; then
  echo "[ERROR] Building docker image failed."
  exit 2
else
  echo "[INFO] Building docker image finished."
fi

get_device_string(){
  # Get all possible serial connections to MSP boards
  ACM_DEVICES=$(ls /dev | grep $MSP_SERIAL_PORT_NAME)
  ACM_DEVICE_CNT=0
  LINKED_DEVICE_STR=""

  for DEVICE in $ACM_DEVICES
  do
    ACM_DEVICE_CNT=$(( $ACM_DEVICE_CNT + 1 ))
    LINKED_DEVICE_STR="${LINKED_DEVICE_STR}      - /dev/${DEVICE}:/dev/${DEVICE}"$'\n'
  done

  echo "[INFO] Found $ACM_DEVICE_CNT possible serial connections to MSP boards."

  # Get connected PicoScopes
  SCOPE_DEVICES=$( lsusb | grep $PICO_SCOPE_USB_NAME | while read -r LINE ; do
    TOKEN=( $LINE )
    USB_BUS=${TOKEN[1]}
    USB_DEVICE=$(echo ${TOKEN[3]} | sed 's/://')
    echo "/dev/bus/usb/$USB_BUS/$USB_DEVICE"
  done )

  if [ ${#SCOPE_DEVICES[@]} -eq 0 ] && [ $$ACM_DEVICE_CNT -eq 0 ]
  then
    echo "[ERROR] No devices found. Connect MSPs and PicoScopes to the host."
    exit 3
  else
    echo "[INFO] Found ${#SCOPE_DEVICES[@]} connected PicoScope(s)."
  fi

  for DEVICE in $SCOPE_DEVICES
  do
    LINKED_DEVICE_STR="${LINKED_DEVICE_STR}      - ${DEVICE}:${DEVICE}"$'\n'
  done
}

cp docker-compose-template.yml $DOCKER_COMPOSE_FILE
awk -v r=$LINKED_DEVICE_STR '{gsub(/{DEVICES}/,r)}1' $DOCKER_COMPOSE_FILE
sed -i -e "s%{ARGS}%$ARGS%g" $DOCKER_COMPOSE_FILE
sed -i -e "s%{ATTEST_IMG}%$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG%g" $DOCKER_COMPOSE_FILE

DOCKER_RET_CODE=0
start_docker() {
  echo "[INFO] Start docker compose."
  docker compose -f $DOCKER_COMPOSE_FILE up $DOCKER_MODE 
  DOCKER_RET_CODE=$?
  echo "[INFO] Containers started. Use 'docker attach --sig-proxy=false $DOCKER_CONTAINER_NAME' to inspect the log output."
}

get_device_string
start_docker
if [ $DOCKER_RET_CODE -eq 0 ]
then
  exit 0
fi

echo "[ERROR] Starting the test system failed with exit code $DOCKER_RET_CODE."