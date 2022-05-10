import os
import time
import sys
from flask import render_template, current_app, session
from flask_login import current_user
from rq import get_current_job
from app import create_app, db
from app.models import User, Task, Sample, Run, ReadSummary, PathoscopeSummary
import snakemake
import pyexcel as pe
import subprocess

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

def snake_hlb(snakefile,path,run):
	#Create run script
	script_path = os.path.join(path,'run_snakemake.py')
	command = ''.join(['snakemake.snakemake("',snakefile,'", workdir="',path,'", conda_prefix="/home/sonunziata/pipeline_environments", cores=40, use_conda=True, keepgoing=True, resources={"load":1})'])
	with open(script_path, 'w') as f:
		f.write("#!/usr/bin/env /home/sonunziata/miniconda3/envs/snakemake/bin/python\n")
		f.write("import snakemake\n")
		f.write(command)

	#Run snakemake pipeline
	subprocess.run(['python', script_path])
	#snakemake.snakemake(snakefile, workdir=path, conda_prefix="/home/sonunziata/pipeline_environments", cores=20, use_conda=True, keepgoing=True, resources={"load":1})

	#Process pipeline output
	output_path = os.path.join(path,"summary_output/virus_summary_output.xlsx")
	qc_path = os.path.join(path,"summary_output/multiqc_report.html")

	#Get excel output
	book = pe.get_book(file_name=output_path, sheets=['read_summary','pathoscope_mapping'])
	del book.read_summary.row[0]
	book.read_summary.colnames=['sample_name', 'raw_reads', 'trimmed_reads', 'host', 'viral', 'unmapped']
	del book.pathoscope_mapping.row[0]
	book.pathoscope_mapping.colnames=['sample_name', 'acc', 'ti', 'reads', 'bp_covered', 'coverage', 'classification', 'adapt_id', 'description', 'virus', 'seq']

	with app.app_context():
		#Save results file to database
		query = Run.query.filter_by(id=run).first()
		setattr(query, 'summary_output', output_path)
		db.session.commit()
		setattr(query, 'qc_output', qc_path)
		db.session.commit()

		#Save results rows to database
		def readsummary_init_func(row):
			s = Sample.query.filter_by(run_id=run).filter_by(sample_id=row['sample_name']).first()
			r = ReadSummary(row['sample_name'], row['raw_reads'], s)
			return r

		def pathosummary_init_func(row):
			s = Sample.query.filter_by(run_id=run).filter_by(sample_id=row['sample_name']).first()
			r = PathoscopeSummary(row['sample_name'], row['acc'], row['ti'], row['reads'], row['bp_covered'], row['coverage'], row['classification'], row['adapt_id'], row['description'], row['virus'], s)
			return r

		book.read_summary.save_to_database(
			session=db.session,
			table=ReadSummary,
			initializer=readsummary_init_func)

		book.pathoscope_mapping.save_to_database(
			session=db.session,
			table=PathoscopeSummary,
			initializer=pathosummary_init_func)

	#snakemake.snakemake(os.path.join(current_app.config['PIPELINE_FOLDER'], "test/Snakefile"),workdir=current_app.config['CONFIG_FOLDER'], report=os.path.join(current_app.config['RESULTS_FOLDER'], "report.html"))
	# with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv")) as f:
	# 	next(f)
	# 	sample_list = [line.rstrip() for line in f]
	# for id in sample_list:
	# 	sample_id = Sample.query.filter_by(sample_id=id).first()
	# 	assembly = Assembly(assembly_url = os.path.join(current_app.config['RESULTS_FOLDER'], id + ".fasta"), assembly_filename= (id + ".fasta"), author=user, sample = sample_id)
	# 	db.session.add(assembly)
	# 	db.session.commit()

def example(user_id,snakefile,path):
	try:
		user = User.query.get(user_id)
		_set_task_progress(0)
		snake_hlb(snakefile,path)
		_set_task_progress(100)
		print('Task completed')
	except:
		_set_task_progress(100)
		app.logger.error('Unhandled exception', exc_info=sys.exc_info())
