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

DOCKER_IMAGE_NAME="rts"
DOCKER_IMAGE_TAG="latest"
DOCKER_FILE_NAME="dockerfile"
DOCKER_CONTAINER_NAME="rts"
# Path to the ssh directory for the test system user on the host
SSH_PATH="/rtos/.ssh"
# Log, DB and Config path
SYS_PATH="/rtos"
MSP_SERIAL_PORT_NAME="ttyACM"
PICO_SCOPE_USB_NAME="PicoScope"

##################### END ######################

ROOT_DIRECTORY="$(dirname "$(realpath "${BASH_SOURCE:-$0}")")"
COMMAND_PARAM="$1 $2 $3 $4 $5 $6 $7 $8"
DOCKER_MODE="-it"

if [ $# -eq 0 ]
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
docker build -t $DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG "$ROOT_DIRECTORY" -f $DOCKER_FILE_NAME
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
    LINKED_DEVICE_STR="$LINKED_DEVICE_STR --device=/dev/$DEVICE"
  done

  echo "[INFO] Found $ACM_DEVICE_CNT possible serial connections to MSP boards."

  # Get connected PicoScopes
  SCOPE_DEVICES=$( lsusb | grep $PICO_SCOPE_USB_NAME | while read -r LINE ; do
    TOKEN=( $LINE )
    USB_BUS=${TOKEN[1]}
    USB_DEVICE=$(echo ${TOKEN[3]} | sed 's/://')
    echo " --device=/dev/bus/usb/$USB_BUS/$USB_DEVICE"
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
    LINKED_DEVICE_STR="$LINKED_DEVICE_STR $DEVICE"
  done
}

DOCKER_RET_CODE=0
start_container() {
  ARGS="$LINKED_DEVICE_STR --rm $DOCKER_MODE --name $DOCKER_CONTAINER_NAME -v $SYS_PATH:/host -v $SSH_PATH:/root/.ssh"
  IMG="$DOCKER_IMAGE_NAME:$DOCKER_IMAGE_TAG"
  CMD="python3 main.py"
  echo "[INFO] Start docker container."
  echo "[INFO]    Arguments: $ARGS"
  echo "[INFO]    Image: $IMG"
  echo "[INFO]    Command: $CMD"
  echo "[INFO]    Command Parameters: $COMMAND_PARAM"
  docker run $ARGS $IMG $CMD $COMMAND_PARAM
  DOCKER_RET_CODE=$?
  echo "[INFO] Container started. Use 'docker attach rts' to interact with the testsystem or 'docker attach --sig-proxy=false rts' to inspect the log output."
}

get_device_string
start_container
if [ $DOCKER_RET_CODE -eq 0 ]
then
  exit 0
elif [ $DOCKER_RET_CODE -eq 2 ]
then
  echo "[WARNING] Failed to detect PicoScopes. This may happen after connecting the PicoScopes."
  echo "[INFO] Trying to get new device names and restarting."
  get_device_string
  start_container
  if [ $DOCKER_RET_CODE -eq 0 ]
  then
    exit 0
  fi
fi

echo "[ERROR] Starting the test system failed with exit code $DOCKER_RET_CODE."
