from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
import redis
import rq
import json
from time import time

@login.user_loader
def load_user(id):
	return User.query.get(int(id))

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	runs = db.relationship('Run', backref='author', lazy='dynamic')
	notifications = db.relationship('Notification', backref='user', lazy='dynamic')
	tasks = db.relationship('Task', backref='user', lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def add_notification(self, name, data):
		self.notifications.filter_by(name=name).delete()
		n = Notification(name=name, payload_json=json.dumps(data), user=self)
		db.session.add(n)
		return n

	def launch_task(self, name, description, path, *args, **kwargs):
		rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id, path, *args, **kwargs)
		task = Task(id=rq_job.get_id(), name=name, description=description, path=path, user=self)
		db.session.add(task)
		return task

	def get_tasks_in_progress(self):
		return Task.query.filter_by(user=self, complete=False).all()

	def get_task_in_progress(self, name):
		return Task.query.filter_by(name=name, user=self, complete=False).first()

class Notification(db.Model):
		id = db.Column(db.Integer, primary_key=True)
		name = db.Column(db.String(128), index=True)
		user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
		timestamp = db.Column(db.Float, index=True, default=time)
		payload_json = db.Column(db.Text)

		def get_data(self):
			return json.loads(str(self.payload_json))

class Run(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	run_id = db.Column(db.String(140), index=True, unique=True)
	concat = db.Column(db.Boolean, default=False)
	seq_platform = db.Column(db.String(140))
	share = db.Column(db.String(140))
	run_type = db.Column(db.String(140))
	PE_SE = db.Column(db.String(140))
	extension = db.Column(db.String(140))
	extension_R1_user = db.Column(db.String(140))
	extension_R2_user = db.Column(db.String(140))
	description = db.Column(db.String(140))
	summary_output = db.Column(db.String(140))
	qc_output = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	samples = db.relationship('Sample', backref='run_name', lazy='dynamic', cascade="all,delete")
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Run {}>'.format(self.run_id)

	def to_dict(self):
		return {
			'id': self.id,
			'extension_R1_user': self.extension_R1_user,
			'extension_R2_user': self.extension_R2_user,
			'PE_SE': self.PE_SE,
			'share': self.share,
			'run_id': self.run_id,
			'seq_platform': self.seq_platform,
			'description': self.description,
			'summary_output': self.summary_output,
			'qc_output': self.qc_output,
			'timestamp': str(self.timestamp),
		}

class Sample(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_id = db.Column(db.String(140), index=True)
	R1_path = db.Column(db.String(140))
	R2_path = db.Column(db.String(140))
	host = db.Column(db.String(140))
	notes = db.Column(db.String())
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	run_id = db.Column(db.Integer, db.ForeignKey('run.id'))

	def __repr__(self):
		return '<Sample {}>'.format(self.sample_id)

	def to_dict(self):
		return {
		'sample_id': self.sample_id,
		'host': self.host,
		'notes': self.notes,
		'run_name': self.run_name
		}

class ReadSummary(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_name = db.Column(db.String(140))
	raw_reads = db.Column(db.String(140))

	sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'),nullable=False)
	sample = db.relationship('Sample', backref=db.backref('readsummarys', lazy='dynamic', cascade="all,delete"))

	def __init__(self, sample_name, raw_reads, sample):
		self.sample_name = sample_name
		self.raw_reads = raw_reads
		self.sample = sample

	def __repr__(self):
		return '<ReadSummary %r>' % self.sample_name

class PathoscopeSummary(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_name = db.Column(db.String(140))
	acc = db.Column(db.String(140))
	ti = db.Column(db.String(140))
	reads = db.Column(db.String(140))
	bp_covered = db.Column(db.String(140))
	coverage = db.Column(db.String(140))
	classification = db.Column(db.String(140))
	adapt_id = db.Column(db.String(140))
	description = db.Column(db.String(140))
	virus = db.Column(db.String(140))

	sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'),nullable=False)
	sample = db.relationship('Sample', backref=db.backref('pathoscopesummarys', lazy='dynamic', cascade="all,delete"))

	def __init__(self, sample_name, acc, ti, reads, bp_covered, coverage, classification, adapt_id, description, virus, sample):
		self.sample_name = sample_name
		self.acc = acc
		self.ti = ti
		self.reads = reads
		self.bp_covered = bp_covered
		self.coverage = coverage
		self.classification = classification
		self.adapt_id = adapt_id
		self.description = description
		self.virus = virus
		self.sample = sample

	def to_dict(self):
		return {
		'sample_name': self.sample_name,
		'acc': self.acc,
		'ti': self.ti,
		'reads': self.reads,
		'bp_covered': self.bp_covered,
		'coverage': self.coverage,
		'classification': self.classification,
		'adapt_id': self.adapt_id,
		'description': self.description,
		'virus': self.virus
		}

	def __repr__(self):
		return '<PathoscopeSummary %r>' % self.sample_name

class BlastnFull(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_name = db.Column(db.String(140))
	contig_id = db.Column(db.String(140))
	acc = db.Column(db.String(140))
	percent_id = db.Column(db.String(140))
	virus_length = db.Column(db.String(140))
	contig_length = db.Column(db.String(140))
	alignment_length = db.Column(db.String(140))
	evalue = db.Column(db.String(140))
	bitscore = db.Column(db.String(140))
	fold_cov = db.Column(db.String(140))
	classification = db.Column(db.String(140))
	description = db.Column(db.String(140))
	virus = db.Column(db.String(140))
	adapt_id = db.Column(db.String(140))
	seq = db.Column(db.String())

	sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'),nullable=False)
	sample = db.relationship('Sample', backref=db.backref('blastnfulls', lazy='dynamic', cascade="all,delete"))


	def __init__(self, sample_name, contig_id, acc, percent_id , virus_length, contig_length, alignment_length, evalue, bitscore, fold_cov, classification, description, virus, adapt_id, seq, sample):
		self.sample_name = sample_name
		self.contig_id = contig_id
		self.acc = acc
		self.percent_id = percent_id
		self.virus_length = virus_length
		self.contig_length = contig_length
		self.alignment_length = alignment_length
		self.evalue = evalue
		self.bitscore = bitscore
		self.fold_cov = fold_cov
		self.classification = classification
		self.description = description
		self.virus = virus
		self.adapt_id = adapt_id
		self.seq = seq
		self.sample = sample

	def to_dict(self):
		return {
		'sample_name': self.sample_name,
		'contig_id': self.contig_id,
		'acc': self.acc,
		'percent_id': self.percent_id,
		'virus_length': self.virus_length,
		'contig_length': self.contig_length,
		'alignment_length': self.alignment_length,
		'evalue': self.evalue,
		'bitscore': self.bitscore,
		'fold_cov': self.fold_cov,
		'classification': self.classification,
		'description': self.description,
		'virus': self.virus,
		'adapt_id': self.adapt_id,
		'seq': self.seq
		}

	def __repr__(self):
		return '<BlastnFull %r>' % self.sample_name

class Task(db.Model):
	id = db.Column(db.String(36), primary_key=True)
	name = db.Column(db.String(128), index=True)
	description = db.Column(db.String(128))
	path = db.Column(db.String(140))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	complete = db.Column(db.Boolean, default=False)

	def get_rq_job(self):
		try:
			rq_job = rq.job.Job.fetch(self.id, connection=current_app.redis)
		except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
			return None
		return rq_job

	def get_progress(self):
		job = self.get_rq_job()
		return job.meta.get('progress', 0) if job is not None else 100
