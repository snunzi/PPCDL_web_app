from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField, TextField, MultipleFileField, RadioField
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
    extension_R1_user = TextAreaField(('Enter the R1 extension (i.g. _R1.fastq.gz)'), default='_L001_R1_001.fastq.gz', validators=[Optional()])
    extension_R2_user = TextAreaField(('Enter the R2 extension (i.g. _R2.fastq.gz)'),default='_L001_R2_001.fastq.gz', validators=[Optional()])
    Description = TextAreaField(('Enter a short desciption of the run (i.g. Non-diagnostic Virus)'), validators=[DataRequired()])
    reads = MultipleFileField()
    submit = SubmitField(('Submit'))

    def validate_run_id(self, run_id):
        run = Run.query.filter_by(run_id=run_id.data).first()
        if run is not None:
            raise ValidationError('That run id already exists in the database, please use a different id.')

class SearchRuns(FlaskForm):
    choices = [('run_id', 'run_id'),
               ('Description', 'Description')]
    select = SelectField('Search for a Run:', choices=choices)
    search = StringField('')

class AssemblyForm(FlaskForm):
    tasks = [('assembly', 'assembly')]
    task = SelectField('Task', choices=tasks)
    submit = SubmitField(('Submit'))

class ConfigForm(FlaskForm):
    ref_proteomes = [('A4', 'A4'), ('psy62', 'psy62'), ('JXGC','JXGC'), ('Ishi-1','Ishi-1'), ('gxpsy','gxpsy')]
    ref_proteome = SelectField('Reference Genome', choices=ref_proteomes, validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class PipelineForm(FlaskForm):
    pipeline_choices = [('virus_id', 'Virus ID'), ('ill_meta', 'Illumina Metabarcoding')]
    pipeline = SelectField('Analysis Pipeline', choices=pipeline_choices, validators=[DataRequired()])
    submit = SubmitField(('Submit'))

class VirusConfigForm(FlaskForm):
    library_choices = [('total','RiboZero RNA'),('small','Small RNA')]
    library_type = SelectField('Library Type', choices=library_choices, validators=[DataRequired()])
    blastx_run = RadioField('Perform blastx on Contigs?', choices=[('blastx','Yes'),('dont','No')])
    reads_out = RadioField('Output viral read fasta?', choices=[('output','Yes'),('dont','No')])
    submit = SubmitField(('Run'))
