import os
import time
import sys
from flask import render_template, current_app, session
from flask_login import current_user
from rq import get_current_job
from app import create_app, db
from app.models import User, Task, Assembly, Sample, Run
import snakemake

app = create_app()
app.app_context().push()

def _set_task_progress(progress):
	job = get_current_job()
	if job:
		job.meta['progress'] = progress
		job.save_meta()
		task = Task.query.get(job.get_id())
		task.user.add_notification('task_progress', {'task_id': job.get_id(), 'progress': progress})
		if progress >= 100:
			task.complete = True
		db.session.commit()

def snake_hlb(user):
	snakemake.snakemake(os.path.join(current_app.config['PIPELINE_FOLDER'], "test/Snakefile"), workdir=current_app.config['CONFIG_FOLDER'])
	#snakemake.snakemake(os.path.join(current_app.config['PIPELINE_FOLDER'], "test/Snakefile"),workdir=current_app.config['CONFIG_FOLDER'], report=os.path.join(current_app.config['RESULTS_FOLDER'], "report.html"))
	with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv")) as f:
		next(f)
		sample_list = [line.rstrip() for line in f]
	for id in sample_list:
		sample_id = Sample.query.filter_by(sample_id=id).first()
		assembly = Assembly(assembly_url = os.path.join(current_app.config['RESULTS_FOLDER'], id + ".fasta"), assembly_filename= (id + ".fasta"), author=user, sample = sample_id)
		db.session.add(assembly)
		db.session.commit()

def example(user_id):
	try:
		user = User.query.get(user_id)
		_set_task_progress(0)
		snake_hlb(user)
		_set_task_progress(100)
		print('Task completed')
	except:
		_set_task_progress(100)
		app.logger.error('Unhandled exception', exc_info=sys.exc_info())
