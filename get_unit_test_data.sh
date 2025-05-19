#!/bin/bash --posix
#The test data files for running the tests of the score-hv repository
#To copy a file to a local directory. cd to local directory then type:
aws s3 sync s3://noaa-reanalyses-pds/score_suite/test_data/ tests/data/ --no-sign-request

