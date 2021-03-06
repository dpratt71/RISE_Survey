import csv
from celery import Celery
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

from .utils import sanitize

app = Celery('tasks', broker='redis://localhost//', backend='redis://localhost')


@app.task
def import_csv_data(survey, survey_fields, field_response, mode="pre"):
    if mode == 'pre':
        path = survey.pre_file.path
        pre = True
        post = False
    else:
        path = survey.post_file.path
        pre = False
        post = True
    logger.debug('Importing data from {0}'.format(path))
    data = [row for row in csv.reader(open(path, 'rU'))]
    # throw away the first two headers
    ids = data.pop(0)
    names = data.pop(0)
    logger.debug('Data = {0}'.format(data))
    for row in data:
        index = 0
        for f in row:
            try:
                text = sanitize(names[index])
                qid = ids[index]
            except IndexError:
                pass
            if text and qid:
                field, _created = survey_fields.objects.get_or_create(survey=survey,
                                                                    text=text,
                                                                    qualtrics_id=str(qid))
                response = field_response.objects.create(respone_id=row[0],
                                                         survey_field=field,
                                                         response=f,
                                                         is_pre=pre,
                                                         is_post=post)
                response.save()
                index += 1
