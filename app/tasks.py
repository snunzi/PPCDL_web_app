import os
import time
import sys
from flask import render_template, current_app, session
from flask_login import current_user
from rq import get_current_job
from app import create_app, db
from app.models import User, Task, Sample, Run, ReadSummary, PathoscopeSummary, BlastnFull
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

def snake_minmeta(snakefile,path,run):
	#Create run script
	script_path = os.path.join(path,'run_snakemake.py')
	command = ''.join(['snakemake.snakemake("',snakefile,'", workdir="',path,'", conda_prefix="/home/sonunziata/pipeline_environments", cores=40, use_conda=True, keepgoing=True, resources={"load":1})'])
	with open(script_path, 'w') as f:
		f.write("#!/usr/bin/env /home/sonunziata/miniconda3/envs/snakemake/bin/python\n")
		f.write("import snakemake\n")
		f.write(command)

	#Run snakemake pipeline
	subprocess.run(['python', script_path])

	#Process pipeline output
	output_path = os.path.join(path,"summary_output/mapping_summary.xlsx")

	with app.app_context():
		#Save results file to database
		query = Run.query.filter_by(id=run).first()
		setattr(query, 'summary_output', output_path)
		db.session.commit()

def snake_illmeta(snakefile,path,run):
	#Create run script
	script_path = os.path.join(path,'run_snakemake.py')
	command = ''.join(['snakemake.snakemake("',snakefile,'", workdir="',path,'", conda_prefix="/home/sonunziata/pipeline_environments", cores=40, use_conda=True, keepgoing=True, resources={"load":1})'])
	with open(script_path, 'w') as f:
		f.write("#!/usr/bin/env /home/sonunziata/miniconda3/envs/snakemake/bin/python\n")
		f.write("import snakemake\n")
		f.write(command)

	#Run snakemake pipeline
	subprocess.run(['python', script_path])

	#Process pipeline output
	output_path = os.path.join(path,"dada2_summary.xlsx")

	with app.app_context():
		#Save results file to database
		query = Run.query.filter_by(id=run).first()
		setattr(query, 'summary_output', output_path)
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
	book = pe.get_book(file_name=output_path, sheets=['read_summary','pathoscope_mapping', 'blastn_full'])
	del book.read_summary.row[0]
	book.read_summary.colnames=['sample_name', 'raw_reads', 'trimmed_reads', 'host', 'viral', 'unmapped']
	del book.pathoscope_mapping.row[0]
	book.pathoscope_mapping.colnames=['sample_name', 'acc', 'ti', 'reads', 'bp_covered', 'genome_length', 'coverage', 'classification', 'adapt_id', 'description', 'virus', 'seq']
	del book.blastn_full.row[0]
	book.blastn_full.colnames=['sample_name', 'Contig_ID', 'Viral_Hit', 'pident', 'Viral_Hit_length', 'Contig_length', 'Alignment_Length', 'evalue', 'bitscore','align_range', 'Fold_Cov', 'Classification', 'Description', 'Virus', 'Adapt_ID', 'Sequence']

	with app.app_context():
		#Save results file to database
		query = Run.query.filter_by(run_id=run).first()
		setattr(query, 'summary_output', output_path)
		db.session.commit()
		setattr(query, 'qc_output', qc_path)
		db.session.commit()

		#Save results rows to database
		def readsummary_init_func(row):
			s = Sample.query.filter_by(run_id=query.id).filter_by(sample_id=row['sample_name']).first()
			r = ReadSummary(row['sample_name'], row['raw_reads'], s)
			return r

		def pathosummary_init_func(row):
			s = Sample.query.filter_by(run_id=query.id).filter_by(sample_id=row['sample_name']).first()
			r = PathoscopeSummary(row['sample_name'], row['acc'], row['ti'], row['reads'], row['bp_covered'], row['coverage'], row['classification'], row['adapt_id'], row['description'], row['virus'], s)
			return r

		def blastnfull_init_func(row):
			s = Sample.query.filter_by(run_id=query.id).filter_by(sample_id=row['sample_name']).first()
			r = BlastnFull(row['sample_name'], row['Contig_ID'], row['Viral_Hit'], row['pident'], row['Viral_Hit_length'], row['Contig_length'], row['Alignment_Length'], row['evalue'], row['bitscore'], row['Fold_Cov'], row['Classification'], row['Description'], row['Virus'], row['Adapt_ID'], row['Sequence'], s)
			return r

		book.read_summary.save_to_database(
			session=db.session,
			table=ReadSummary,
			initializer=readsummary_init_func)

		book.pathoscope_mapping.save_to_database(
			session=db.session,
			table=PathoscopeSummary,
			initializer=pathosummary_init_func)

		book.blastn_full.save_to_database(
			session=db.session,
			table=BlastnFull,
			initializer=blastnfull_init_func)