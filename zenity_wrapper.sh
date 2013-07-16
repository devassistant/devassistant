#!/bin/bash

sleep .1 && wmctrl -a Information -b add,above &
TEXT=`WINDOWID=$(xwininfo -root -int | awk '/xwininfo:/{print $4}') \
    zenity "$@" &`
echo $TEXT
