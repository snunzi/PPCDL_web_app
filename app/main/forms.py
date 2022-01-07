from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField, TextField, MultipleFileField
from wtforms.validators import ValidationError, DataRequired, Length, Optional
from flask_wtf.file import FileField, FileRequired
from app.models import User, Sample, Run
from werkzeug.utils import secure_filename

class CreateRun(FlaskForm):
    seq_platforms = [('Illumina', 'Illumina'), ('MinION', 'MinION')]
    ends = [('PE', 'PE'), ('SE', 'SE')]
    ext_ill = [('Yes','Yes'), ('No', 'No')]
    run_id = TextAreaField(('Run ID (For Illumina, use Illumina folder name i.g. YYMMDD_InstrumentID_RunID_FlowcellID)'), validators=[DataRequired()])
    seq_platform = SelectField('Platform', choices=seq_platforms, validators=[DataRequired()])
    PE_SE = SelectField('Sequencing Reads', choices=ends, validators=[DataRequired()])
    extension = SelectField('Is extension default Illumina format (_L00[1,2,3,4]_R[1,2]_001.fastq.gz)?', choices=ext_ill)
    extension_user = TextAreaField(('Enter the extension (i.g. .fastq.gz)'), validators=[Optional()])
    Description = TextAreaField(('Enter a short desciption of the run (i.g. Non-diagnostic Virus)'), validators=[DataRequired()])
    reads = FileField(validators=[FileRequired()])
    submit = SubmitField(('Submit'))

    def validate_run_id(self, run_id):
        run = Run.query.filter_by(run_id=run_id.data).first()
        if run is not None:
            raise ValidationError('That run id already exists in the database, please use a different id.')

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
