#!/bin/sh

make init
make celery &
make start
