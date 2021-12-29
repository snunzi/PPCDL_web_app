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
	assemblies = db.relationship('Assembly', backref='author', lazy='dynamic')
	samples = db.relationship('Sample', backref='author', lazy='dynamic')
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

	def launch_task(self, name, description, *args, **kwargs):
		rq_job = current_app.task_queue.enqueue('app.tasks.' + name, self.id,*args, **kwargs)
		task = Task(id=rq_job.get_id(), name=name, description=description, user=self)
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

class Sample(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	sample_id = db.Column(db.String(140), index=True, unique=True)
	insert_size = db.Column(db.String(140))
	seq_kit = db.Column(db.String(140))
	seq_platform = db.Column(db.String(140))
	seq_location = db.Column(db.String(140))
	PE_SE = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	assemblies = db.relationship('Assembly', backref='sample')

	def __repr__(self):
		return '<Sample {}>'.format(self.sample_id)

class Assembly(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	assembly_filename = db.Column(db.String, default=None, nullable=True)
	assembly_url = db.Column(db.String, default=None, nullable=True)
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	sample_id = db.Column(db.Integer, db.ForeignKey('sample.id'))

	def __repr__(self):
		return '<Assembly {}>'.format(self.assembly_filename)

class Task(db.Model):
	id = db.Column(db.String(36), primary_key=True)
	name = db.Column(db.String(128), index=True)
	description = db.Column(db.String(128))
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
