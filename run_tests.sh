#!/bin/bash

#Set the PYTHONPATH to the project root directory
export PYTHONPATH=$(pwd)

#Run pytest with coverage
pytest --cov=src --cov-report=html