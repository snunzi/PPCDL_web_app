import os
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, send_from_directory, json
from flask_login import current_user, login_required
from app import db
from app.models import User, Sample, Run
from app.main import bp
from app.main.forms import AssemblyForm, ConfigForm, CreateRun, PipelineForm, VirusConfigForm
from werkzeug.utils import secure_filename
from Bio import SeqIO
import snakemake
import pathlib
import fileinput
import sys
from threading import Thread
from app.tasks import snake_hlb


@bp.route('/')
@bp.route('/index')
@login_required
def index():
	return render_template('index.html')

@bp.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	return render_template('user.html', samples=Sample.query.order_by(Sample.timestamp.desc()).all())


@bp.route('/user/<username>/CreateRun', methods=['GET', 'POST'])
@login_required
def run(username):
	form = CreateRun()
	if form.validate_on_submit():
		path = os.path.join(current_app.config['UPLOAD_FOLDER'],form.run_id.data,'data')
		os.makedirs(path)
		files_filenames = []
		for f in form.reads.data:
			f_filename = secure_filename(f.filename)
			f.save(os.path.join(path, f_filename))
			files_filenames.append(f_filename)
		samples = list(set([sub.replace(form.extension_R1_user.data, "").replace(form.extension_R2_user.data, "")
			for sub in files_filenames]))


		run = Run(run_id=form.run_id.data, seq_platform=form.seq_platform.data, PE_SE=form.PE_SE.data, extension=form.extension.data, extension_R1_user=form.extension_R1_user.data, extension_R2_user=form.extension_R2_user.data, description=form.Description.data, author=current_user)

		db.session.add(run)
		db.session.commit()

		for s in samples:
			R1 = os.path.join(path, s + form.extension_R1_user.data)
			R2 = os.path.join(path, s + form.extension_R2_user.data)
			samp = Sample(sample_id=s, R1_path=R1, R2_path=R2, run_name=run, host='arabidopsis')
			db.session.add(samp)
			db.session.commit()

		flash('Your run is now uploaded!')
		return redirect(url_for('main.index'))
	return render_template("run.html", user=user, form=form)

@bp.route('/user/<username>/BrowseRuns', methods=['GET', 'POST'])
@login_required
def browseruns(username):
	user = User.query.filter_by(username=username).first_or_404()
	if request.method == 'POST':
		run_list = request.form.getlist('chkbox')
		run = run_list[0]
		analy_run = Run.query.filter_by(id=run).first()
		sample_ids = Sample.query.filter_by(run_id=analy_run.id).all()
		#path = os.path.join(current_app.config['UPLOAD_FOLDER'],form.run_id.data,'data')
		with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv"), 'w') as filehandle:
			filehandle.write("sample\n")
			for listitem in sample_ids:
				filehandle.write('%s\n' % listitem.sample_id)
				#print("This is the file " + listitem, file=sys.stderr)
		return redirect(url_for('main.pipeline', username=current_user.username, run=run))
	return render_template('browseruns.html')

@bp.route('/user/rundata')
@login_required
def rundata():
	query = Run.query

	# search filter
	search = request.args.get('search[value]')
	if search:
		query = query.filter(db.or_(
			Run.description.like(f'%{search}%'),
			Run.run_id.like(f'%{search}%')
	))
	total_filtered = query.count()

	# sorting
	order = []
	i = 0
	while True:
		col_index = request.args.get(f'order[{i}][column]')
		if col_index is None:
			break
		col_name = request.args.get(f'columns[{col_index}][data]')
		if col_name not in ['run_id', 'timestamp']:
			col_name = 'run_id'
		descending = request.args.get(f'order[{i}][dir]') == 'desc'
		col = getattr(Run, col_name)
		if descending:
			col = col.desc()
		order.append(col)
		i += 1
	if order:
		query = query.order_by(*order)

	# pagination
	start = request.args.get('start', type=int)
	length = request.args.get('length', type=int)
	query = query.offset(start).limit(length)

	# response
	return {
		'data': [run.to_dict() for run in query],
		'recordsFiltered': total_filtered,
		'recordsTotal': Run.query.count(),
		'draw': request.args.get('draw', type=int),
	}

@bp.route('/user/<username>/RunSamples/<runname>')
@login_required
def runsamples(username,runname):
	user = User.query.filter_by(username=username).first_or_404()
	run = Run.query.filter_by(run_id=runname).first_or_404()
	samples = Sample.query.filter_by(run_id=run.id).all()
	return render_template('runsamples.html', user=user, runname=runname, samples=samples)

@bp.route('/user/<username>/UpdateSamples', methods=['POST'])
@login_required
def updatesample(username):
		pk = request.form['pk']
		name = request.form['name']
		value = request.form['value']
		sample = db.session.query(Sample).filter_by(id=pk).first()
		if name == 'host':
			setattr(sample, 'host', value)
		elif name == 'email':
			cur.execute("UPDATE employee SET email = %s WHERE id = %s ", (value, pk))
		db.session.commit()
		return json.dumps({'status':'OK'})


@bp.route('/user/<username>/Pipeline/<run>', methods = ['GET', 'POST'])
@login_required
def pipeline(username, run):
	form = PipelineForm()
	if form.validate_on_submit():
		return redirect(url_for('main.viruspipe', username=current_user.username, run=run))
	return render_template("pipeline.html", user=user, form=form, run=run)


@bp.route('/user/<username>/VirusPipe/<run>', methods = ['GET', 'POST'])
@login_required
def viruspipe(username, run):
	form = VirusConfigForm()
	if form.validate_on_submit():
		if current_user.get_task_in_progress('example'):
			flash(('An analysis is already in progress, please wait'))
		else:
			#Get the Run
			query = Run.query.filter_by(id=run).first()
			run_dict = query.to_dict()
			path = os.path.join(current_app.config['UPLOAD_FOLDER'],run_dict['run_id'])

			#Generate Sample file
			samples = Sample.query.filter_by(run_id=run).all()
			with open(os.path.join(path, "samples.tsv"), 'w') as sample_file:
				print("sample\thost", file=sample_file)
				for sample in samples:
					sample_dict = sample.to_dict()
					print(sample_dict['sample_id'] + "\t" + sample_dict['host'], file=sample_file)

			#Generate config file
			config_dict = request.form.to_dict()
			config_dict.update(run_dict)
			del config_dict['id']
			del config_dict['description']
			with open(os.path.join(path, "config.yaml"), 'w') as config_file:
				for line in fileinput.input(os.path.join(current_app.config['CONFIG_FOLDER'], "pipelines/virus/config.yaml"), inplace=False):
					line = line.rstrip()
					if not line:
						continue
					for f_key, f_value in config_dict.items():
						if f_key in line:
							line = line.replace(f_key, str(f_value))
					print(line, file = config_file)
		snakefile = os.path.join(current_app.config['PIPELINE_FOLDER'], "virus/Snakefile")
		thread = Thread(target=snake_hlb, args=(snakefile,path,query))
		thread.start()
			#snakemake.snakemake(os.path.join(current_app.config['PIPELINE_FOLDER'], "test/Snakefile"), workdir=path)
			#current_user.launch_task('example', ('Creating your assembly...'), path)
			#db.session.commit()
		return redirect(url_for('main.index', username=current_user.username))
	return render_template("viruspipe.html", user=user, form=form)
