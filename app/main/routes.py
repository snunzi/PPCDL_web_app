import os
from flask import render_template, flash, redirect, url_for, request, send_from_directory, current_app, send_from_directory
from flask_login import current_user, login_required
from app import db
from app.models import User, Sample
from app.main import bp
from app.main.forms import CreateSample, AssemblyForm, ConfigForm
from werkzeug.utils import secure_filename
from Bio import SeqIO
import snakemake
import pathlib
import fileinput


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


@bp.route('/user/<username>/CreateSample', methods=['GET', 'POST'])
@login_required
def sample(username):
	form = CreateSample()
	if form.validate_on_submit():
		f = form.sample_read1.data
		filename = secure_filename(f.filename)

		sample_id = form.sample_id.data + '.fasta'
		#pathlib.Path(current_app.config['UPLOAD_FOLDER'], sample_id).mkdir(exist_ok=True)
		f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], sample_id))

		sample = Sample(sample_id=form.sample_id.data, insert_size=form.insert_size.data, seq_kit=form.seq_kit.data, seq_platform=form.seq_platform.data, seq_location=form.seq_location.data, PE_SE=form.PE_SE.data, author=current_user)

		db.session.add(sample)
		db.session.commit()
		flash('Your sample is now uploaded!')
		return redirect(url_for('main.index'))
	return render_template("sample.html", user=user, form=form)

@bp.route('/user/<username>/Assemble_Sample', methods = ['GET', 'POST'])
@login_required
def assemble_sample(username):
	if request.method == 'POST':
		sample_list = request.form.getlist('chkbox')
		with open(os.path.join(current_app.config['CONFIG_FOLDER'], "samples.tsv"), 'w') as filehandle:
			filehandle.write("sample\n")
			for listitem in sample_list:
				filehandle.write('%s\n' % listitem)
		print(request.form.getlist('chkbox'))
		return redirect(url_for('main.config', username=current_user.username))
	return render_template("assemble_sample.html", samples=Sample.query.order_by(Sample.timestamp.desc()).all())

@bp.route('/user/<username>/Config', methods = ['GET', 'POST'])
@login_required
def config(username):
	form = ConfigForm()
	config_file = os.path.join(current_app.config['CONFIG_FOLDER'], "config.yaml")
	if form.validate_on_submit():
		if current_user.get_task_in_progress('example'):
			flash(('An assembly is already in progress, please wait'))
		else:
			config_dict = request.form.to_dict()
			with open(os.path.join(current_app.config['CONFIG_FOLDER'], "config.yaml"), 'w') as config_file:
				for line in fileinput.input(os.path.join(current_app.config['CONFIG_FOLDER'], "pipelines/test/config.yaml"), inplace=False):
					line = line.rstrip()
					if not line:
						continue
					for f_key, f_value in config_dict.items():
						if f_key in line:
							line = line.replace(f_key, f_value)
					print(line, file = config_file)
			current_user.launch_task('example', ('Creating your assembly...'))
			db.session.commit()
		return redirect(url_for('main.index'))
	return render_template("config.html", user=user, form=form)

@bp.route('/user/assemblies/<path:filename>')
@login_required
def assembly_file(filename):
    return send_from_directory(current_app.config['RESULTS_FOLDER'],
                               filename, as_attachment=False)
