import datetime
import uuid
import json
import pandas as pd
import os
from os import listdir
from os.path import isfile, join


df = pd.read_json('data/responses.json')
df.to_csv (r'data/responses.csv', index = None)
