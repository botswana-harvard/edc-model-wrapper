from datetime import timedelta
from django.test import TestCase, tag
from edc_base.utils import get_utcnow

from ..wrappers import ModelWrapper, ModelWithLogWrapper
from .models import Example, ExampleLog, ExampleLogEntry, ParentExample


class ExampleModelWrapper(ModelWrapper):
    model = 'edc_model_wrapper.example'
    next_url_name = 'edc-model-wrapper:listboard_url'
    next_url_attrs = ['f1']
    querystring_attrs = ['f2', 'f3']


class ParentExampleModelWrapper(ModelWrapper):

    model = 'edc_model_wrapper.parentexample'
    next_url_name = 'edc-model-wrapper:listboard_url'
    next_url_attrs = ['f1']
    querystring_attrs = ['f2', 'f3']


class ExampleLogEntryModelWrapper(ModelWrapper):

    model = 'edc_model_wrapper.examplelogentry'
    next_url_name = 'edc-model-wrapper:listboard_url'
    next_url_attrs = ['example_identifier', 'example_log']
    querystring_attrs = ['f2', 'f3']


class ParentExampleModelWithLogWrapper(ModelWithLogWrapper):

    model_wrapper_cls = ParentExampleModelWrapper
    log_entry_model_wrapper_cls = ExampleLogEntryModelWrapper

    parent_model_wrapper_cls = ExampleModelWrapper
    related_lookup = 'example'


class TestModelWithLogWrapper(TestCase):

    def test_wrapper_object(self):
        example = Example.objects.create()
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(wrapper.object, example)

    def testwrapper_fields(self):
        example = Example.objects.create()
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertIsNotNone(wrapper.f1)
        self.assertIsNotNone(wrapper.f2)
        self.assertIsNotNone(wrapper.f3)
        self.assertIsNotNone(wrapper.revision)
        self.assertIsNotNone(wrapper.hostname_created)
        self.assertIsNotNone(wrapper.hostname_modified)
        self.assertIsNotNone(wrapper.user_created)
        self.assertIsNotNone(wrapper.user_modified)
        self.assertIsNotNone(wrapper.created)
        self.assertIsNotNone(wrapper.modified)
        self.assertTrue(bool(wrapper))
        self.assertTrue(wrapper.object.wrapped)

    def test_wrapper_repr(self):
        example = Example.objects.create()
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertTrue(repr(wrapper))

    def test_wrapper_log(self):
        example = Example.objects.create()
        log = ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(wrapper.log.object.example, log.example)

    def test_wrapper_log_entry(self):
        example = Example.objects.create()
        log = ExampleLog.objects.create(example=example)
        log_entry = ExampleLogEntry.objects.create(example_log=log)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(
            wrapper.log_entry.object.example_log,
            log_entry.example_log)

    def test_wrapper_fills_log_entry(self):
        """Asserts adds a non-persisted instance of log entry
        if a persisted one does not exist.
        """
        example = Example.objects.create()
        example_log = ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertIsNone(wrapper.log_entry.object.id)
        self.assertEqual(
            example_log,
            wrapper.log_entry.object.example_log)

    def test_wrapper_fills_log(self):
        """Asserts adds a non-persisted instance of log
        if a persisted one does not exist.
        """
        example = Example.objects.create()
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertIsNone(wrapper.log.object.id)
        self.assertEqual(example, wrapper.log.object.example)

    def test_wrapper_fills_log_and_logentry(self):
        """Asserts adds a non-persisted instance of log and log entry
        if a persisted ones do not exist.
        """
        example = Example.objects.create()
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertIsNone(wrapper.log.object.id)
        self.assertIsNone(wrapper.log_entry.object.id)

    def test_wrapper_has_log_by_model_name(self):
        example = Example.objects.create()
        log = ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(wrapper.examplelog, log)

    def test_wrapper_has_logentry_by_model_name(self):
        example = Example.objects.create()
        log = ExampleLog.objects.create(example=example)
        log_entry = ExampleLogEntry.objects.create(example_log=log)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(wrapper.examplelogentry, log_entry)

    def test_wrapper_no_entries(self):
        example = Example.objects.create()
        ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(wrapper.log_entries, [])

    def test_wrapper_multpile_log_entries(self):
        example = Example.objects.create()
        example_log = ExampleLog.objects.create(example=example)
        ExampleLogEntry.objects.create(example_log=example_log)
        ExampleLogEntry.objects.create(example_log=example_log)
        ExampleLogEntry.objects.create(example_log=example_log)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(len(wrapper.log_entries), 3)

    def test_wrapper_picks_most_recent_log_entry(self):
        example = Example.objects.create()
        example_log = ExampleLog.objects.create(example=example)
        report_datetime = get_utcnow() - timedelta(days=1)
        ExampleLogEntry.objects.create(
            example_log=example_log,
            report_datetime=get_utcnow() - timedelta(days=3))
        ExampleLogEntry.objects.create(
            example_log=example_log,
            report_datetime=get_utcnow() - timedelta(days=2))
        ExampleLogEntry.objects.create(
            example_log=example_log,
            report_datetime=report_datetime)
        wrapper = ModelWithLogWrapper(
            model_obj=example, next_url_name='listboard')
        self.assertEqual(
            wrapper.log_entry.object.report_datetime, report_datetime)


class TestModelWithLogWrapperUrls(TestCase):

    def test_unrelated_wrapper_log(self):
        example = Example.objects.create()
        parent_example = ParentExample.objects.create(example=example)
        log = ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=parent_example, related_lookup='example', next_url_name='listboard')
        self.assertEqual(wrapper.log.object.example, log.example)

    def test_wrapper_urls(self):
        example = Example.objects.create()
        example_log = ExampleLog.objects.create(example=example)
        wrapper = ModelWithLogWrapper(
            model_obj=example,
            next_url_attrs=['example_identifier', 'example_log'],
            next_url_name='listboard_url')
        self.assertIn(
            f'example_log={example_log.id}',
            wrapper.log_entry.next_url)
        self.assertIn(
            'listboard_url',
            wrapper.log_entry.next_url.split('&')[0])

        self.assertIn(
            'example_log',
            wrapper.log_entry.next_url.split('&')[0])

        self.assertIn(
            'example_identifier',
            wrapper.log_entry.next_url.split('&')[0])

        self.assertIn(
            f'example_identifier={example.example_identifier}',
            wrapper.log_entry.next_url)

    def test_wrapper_next_url(self):
        example_identifier = '111111111'
        example = Example.objects.create(example_identifier=example_identifier)
        example_log = ExampleLog.objects.create(example=example)
        ExampleLogEntry.objects.create(example_log=example_log)
        wrapper = ModelWithLogWrapper(
            model_obj=example,
            next_url_attrs=['example_identifier', 'example_log'],
            next_url_name='edc-model-wrapper:listboard_url')
        self.assertIsNotNone(wrapper.next_url)
        self.assertTrue(wrapper.next_url != '')
        self.assertEqual(
            wrapper.next_url,
            f'edc-model-wrapper:listboard_url,example_identifier,example_log'
            f'&example_identifier={example_identifier}&example_log={str(example_log.id)}')
