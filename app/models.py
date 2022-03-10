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
	seq_platform = db.Column(db.String(140))
	PE_SE = db.Column(db.String(140))
	extension = db.Column(db.String(140))
	extension_R1_user = db.Column(db.String(140))
	extension_R2_user = db.Column(db.String(140))
	description = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	samples = db.relationship('Sample', backref='run_name', lazy='dynamic')
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Run {}>'.format(self.run_id)

	def to_dict(self):
		return {
			'id': self.id,
			'extension_R1_user': self.extension_R1_user,
			'extension_R2_user': self.extension_R2_user,
			'PE_SE': self.PE_SE,
			'run_id': self.run_id,
			'seq_platform': self.seq_platform,
			'description': self.description,
			'timestamp': str(self.timestamp),
		}

class Sample(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_id = db.Column(db.String(140), index=True)
	R1_path = db.Column(db.String(140))
	R2_path = db.Column(db.String(140))
	host = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	run_id = db.Column(db.Integer, db.ForeignKey('run.id'))

	def __repr__(self):
		return '<Sample {}>'.format(self.sample_id)

	def to_dict(self):
		return {
		'sample_id': self.sample_id,
		'host': self.host
		}


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
