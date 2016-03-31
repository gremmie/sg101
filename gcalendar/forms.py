"""
Forms for the gcalendar application.
"""
import datetime
import pytz
from django import forms

from core.html import ImageCheckError
from core.html import image_check
from core.markup import site_markup
from gcalendar.models import Event


TIME_CHOICES = (
    ('00:00', '12:00 am (00:00)'),
    ('00:30', '12:30 am (00:30)'),
    ('01:00', '1:00 am (01:00)'),
    ('01:30', '1:30 am (01:30)'),
    ('02:00', '2:00 am (02:00)'),
    ('02:30', '2:30 am (02:30)'),
    ('03:00', '3:00 am (03:00)'),
    ('03:30', '3:30 am (03:30)'),
    ('04:00', '4:00 am (04:00)'),
    ('04:30', '4:30 am (04:30)'),
    ('05:00', '5:00 am (05:00)'),
    ('05:30', '5:30 am (05:30)'),
    ('06:00', '6:00 am (06:00)'),
    ('06:30', '6:30 am (06:30)'),
    ('07:00', '7:00 am (07:00)'),
    ('07:30', '7:30 am (07:30)'),
    ('08:00', '8:00 am (08:00)'),
    ('08:30', '8:30 am (08:30)'),
    ('09:00', '9:00 am (09:00)'),
    ('09:30', '9:30 am (09:30)'),
    ('10:00', '10:00 am (10:00)'),
    ('10:30', '10:30 am (10:30)'),
    ('11:00', '11:00 am (11:00)'),
    ('11:30', '11:30 am (11:30)'),
    ('12:00', '12:00 am (12:00)'),
    ('12:30', '12:30 am (12:30)'),
    ('13:00', '1:00 pm (13:00)'),
    ('13:30', '1:30 pm (13:30)'),
    ('14:00', '2:00 pm (14:00)'),
    ('14:30', '2:30 pm (14:30)'),
    ('15:00', '3:00 pm (15:00)'),
    ('15:30', '3:30 pm (15:30)'),
    ('16:00', '4:00 pm (16:00)'),
    ('16:30', '4:30 pm (16:30)'),
    ('17:00', '5:00 pm (17:00)'),
    ('17:30', '5:30 pm (17:30)'),
    ('18:00', '6:00 pm (18:00)'),
    ('18:30', '6:30 pm (18:30)'),
    ('19:00', '7:00 pm (19:00)'),
    ('19:30', '7:30 pm (19:30)'),
    ('20:00', '8:00 pm (20:00)'),
    ('20:30', '8:30 pm (20:30)'),
    ('21:00', '9:00 pm (21:00)'),
    ('21:30', '9:30 pm (21:30)'),
    ('22:00', '10:00 pm (22:00)'),
    ('22:30', '10:30 pm (22:30)'),
    ('23:00', '11:00 pm (23:00)'),
    ('23:30', '11:30 pm (23:30)'),
)


class EventEntryForm(forms.ModelForm):
    what = forms.CharField(widget=forms.TextInput(attrs={'size': 60}))
    start_date = forms.DateField(widget=forms.TextInput(attrs={'size': 10}))
    start_time = forms.TimeField(required=False, widget=forms.Select(choices=TIME_CHOICES))
    end_date = forms.DateField(widget=forms.TextInput(attrs={'size': 10}))
    end_time = forms.TimeField(required=False, widget=forms.Select(choices=TIME_CHOICES))
    time_zone = forms.CharField(required=False, widget=forms.HiddenInput())
    where = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': 60}))
    description = forms.CharField(
            required=False,
            widget=forms.Textarea(attrs={
                'class': 'markItUp smileyTarget',
                'id': 'id_body',    # needed for image related js
                }))

    DATE_FORMAT = '%m/%d/%Y'    # must match the jQuery UI datepicker config
    TIME_FORMAT = '%H:%M'
    DEFAULT_START_TIME = '19:00'
    DEFAULT_END_TIME = '20:00'

    class Meta:
        model = Event
        fields = ('what', 'start_date', 'start_time', 'end_date', 'end_time',
            'all_day', 'time_zone', 'where', 'description', 'create_forum_thread')

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance', None)

        if len(args) == 0:      # no POST arguments
            if instance is None:
                init_day = datetime.date.today().strftime(self.DATE_FORMAT)
                if 'start_date' not in initial:
                    initial['start_date'] = init_day
                if 'end_date' not in initial:
                    initial['end_date'] = init_day
                if 'start_time' not in initial:
                    initial['start_time'] = self.DEFAULT_START_TIME
                if 'end_time' not in initial:
                    initial['end_time'] = self.DEFAULT_END_TIME
            else:
                initial['start_date'] = instance.start_date.strftime(self.DATE_FORMAT)
                initial['end_date'] = instance.end_date.strftime(self.DATE_FORMAT)
                if instance.all_day:
                    initial['start_time'] = self.DEFAULT_START_TIME
                    initial['end_time'] = self.DEFAULT_END_TIME
                else:
                    if 'start_time' not in initial:
                        initial['start_time'] = instance.start_time.strftime(self.TIME_FORMAT)
                    if 'end_time' not in initial:
                        initial['end_time'] = instance.end_time.strftime(self.TIME_FORMAT)

            kwargs['initial'] = initial

        super(EventEntryForm, self).__init__(*args, **kwargs)

        # We don't want the user to create a forum thread on an existing event
        if instance is not None:
            del self.fields['create_forum_thread']

    def clean_description(self):
        description = self.cleaned_data['description']
        self.html = ''
        if description:
            self.html = site_markup(description, relative_urls=False)
            try:
                image_check(self.html)
            except ImageCheckError as ex:
                raise forms.ValidationError(str(ex))
        return description

    def clean(self):
        start_date = self.cleaned_data.get('start_date')
        start_time = self.cleaned_data.get('start_time')
        all_day = self.cleaned_data.get('all_day')
        end_date = self.cleaned_data.get('end_date')
        end_time = self.cleaned_data.get('end_time')

        if start_date and start_time and (all_day or (end_date and end_time)):
            if all_day:
                start = start_date
                end = end_date
            else:
                start = datetime.datetime.combine(start_date, start_time)
                end = datetime.datetime.combine(end_date, end_time)
            if start > end:
                raise forms.ValidationError("The start date of the event "
                        "is after the ending time!")

        return self.cleaned_data

    def clean_time_zone(self):
        tz = self.cleaned_data['time_zone']
        try:
            pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            raise forms.ValidationError("Invalid timezone.")
        return tz

