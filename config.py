import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

UPLOAD_FOLDER = '/home/sonunziata/bioinformatic_analyses/web_gui_FY22/PPCDL_web_app/files/data'
CONFIG_FOLDER = '/home/sonunziata/bioinformatic_analyses/web_gui_FY22/PPCDL_web_app/files'
PIPELINE_FOLDER =  '/home/sonunziata/bioinformatic_analyses/web_gui_FY22/PPCDL_web_app/files/pipelines'
RESULTS_FOLDER = '/home/sonunziata/bioinformatic_analyses/web_gui_FY22/PPCDL_web_app/files/ref_annotation'

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    	'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_FOLDER
    CONFIG_FOLDER = CONFIG_FOLDER
    PIPELINE_FOLDER = PIPELINE_FOLDER
    RESULTS_FOLDER = RESULTS_FOLDER
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'
    SESSION_TYPE = 'filesystem'
