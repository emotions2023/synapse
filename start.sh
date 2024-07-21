#!/bin/bash
exec gunicorn -b :$PORT --access-logfile - --error-logfile - index:app
