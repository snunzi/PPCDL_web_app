from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_wtf.file import FileField, FileRequired
from app.models import User, Sample
from werkzeug.utils import secure_filename

class CreateSample(FlaskForm):
    seq_kits = [('TruSeq', 'TruSeq'), ('Nextera', 'Nextera'), ('SureSelect','SureSelect')]
    seq_platforms = [('HiSeq','HiSeq'), ('MiSeq', 'MiSeq'), ('NextSeq', 'NextSeq')]
    seq_locations = [('GeneWiz', 'GeneWiz'), ('SeqMatic', 'SeqMatic'), ('Beltsville-S&T', 'Beltsville-S&T')]
    ends = [('PE', 'PE'), ('SE', 'SE')]
    sample_id = TextAreaField(('Sample ID'), validators=[DataRequired()])
    insert_size = TextAreaField(('Insert Size'), validators=[DataRequired()])
    seq_kit = SelectField('Sequencing Kit', choices=seq_kits, validators=[DataRequired()])
    seq_platform = SelectField('Platform', choices=seq_platforms, validators=[DataRequired()])
    seq_location = SelectField('Sequencing Lab', choices=seq_locations, validators=[DataRequired()])
    PE_SE = SelectField('Sequencing Reads', choices=ends, validators=[DataRequired()])
    sample_read1 = FileField(validators=[FileRequired()])
    submit = SubmitField(('Submit'))
    
    def validate_sample_id(self, sample_id):
        sample = Sample.query.filter_by(sample_id=sample_id.data).first()
        if sample is not None:
            raise ValidationError('Please use a different sample name.')

class AssemblyForm(FlaskForm):
    tasks = [('assembly', 'assembly')]
    task = SelectField('Task', choices=tasks)
    submit = SubmitField(('Submit'))

class ConfigForm(FlaskForm):
    ref_proteomes = [('A4', 'A4'), ('psy62', 'psy62'), ('JXGC','JXGC'), ('Ishi-1','Ishi-1'), ('gxpsy','gxpsy')]
    ref_proteome = SelectField('Reference Genome', choices=ref_proteomes, validators=[DataRequired()])
    submit = SubmitField(('Submit'))

