"""Tests for tools/fix_s3_content_types.py.

A real boto3 client, stubbed at its network edge, so botocore checks the
arguments of the copy that a mock would take from anything.

"""
import importlib.util
import os
import unittest
from unittest.mock import Mock, patch

import boto3
from botocore.stub import Stubber

TOOL = os.path.join(os.path.dirname(__file__), '..', '..', 'tools',
                    'fix_s3_content_types.py')
spec = importlib.util.spec_from_file_location('fix_s3_content_types', TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

BUCKET = 'bucket'
PHOTO = 'a' * 22 + '.jpg'
UUID_PHOTO = 'b' * 32 + '.png'
THUMB = 'a' * 22 + 't.jpg'
BASE = 'https://example.com/'
PUBLIC = {'Grantee': {'Type': 'Group', 'URI': tool.ALL_USERS}, 'Permission': 'READ'}
OWNER = {'Grantee': {'Type': 'CanonicalUser', 'ID': 'me'}, 'Permission': 'FULL_CONTROL'}


def head(content_type='binary/octet-stream', **extra):
    return {'ContentType': content_type, 'ETag': '"e"', 'ContentLength': 5,
            'Metadata': {'user': 'x'}, **extra}


def client():
    return boto3.client('s3', region_name='us-west-1', aws_access_key_id='a',
                        aws_secret_access_key='s')


class SelectionTests(unittest.TestCase):

    def test_photos_of_either_key_length_are_repaired(self):
        self.assertEqual(tool.repair_type(PHOTO, head()), 'image/jpeg')
        self.assertEqual(tool.repair_type(UUID_PHOTO, head('application/octet-stream')),
                         'image/png')

    def test_a_thumbnail_is_left_alone(self):
        self.assertIsNone(tool.repair_type(THUMB, head()))

    def test_a_photo_already_typed_is_left_alone(self):
        self.assertIsNone(tool.repair_type(PHOTO, head('image/jpeg')))
        # Not the type the key calls for today, but nothing a browser minds.
        self.assertIsNone(tool.repair_type('a' * 22 + '.bmp', head('image/x-ms-bmp')))

    def test_a_key_naming_no_type_is_left_alone(self):
        self.assertIsNone(tool.repair_type('a' * 22, head()))
        self.assertIsNone(tool.repair_type('a' * 22 + '.jpg fog', head()))


class CopyTests(unittest.TestCase):

    def test_the_copy_keeps_the_acl_the_metadata_and_the_headers(self):
        c = client()
        with Stubber(c) as stubber:
            stubber.add_response('copy_object', {}, {
                'Bucket': BUCKET, 'Key': PHOTO,
                'CopySource': {'Bucket': BUCKET, 'Key': PHOTO},
                'CopySourceIfMatch': '"e"',
                'MetadataDirective': 'REPLACE',
                'Metadata': {'user': 'x'},
                'ContentType': 'image/jpeg',
                'ACL': 'public-read',
                'CacheControl': 'max-age=60',
            })
            tool.copy_with_type(c, BUCKET, PHOTO, head(CacheControl='max-age=60'),
                                'image/jpeg')
            stubber.assert_no_pending_responses()


class VerifyTests(unittest.TestCase):

    def check(self, after=None, status=200, served='image/jpeg'):
        c = Mock()
        c.head_object.return_value = after or head('image/jpeg')
        response = Mock(status_code=status, headers={'Content-Type': served})
        with patch.object(tool.requests, 'head', return_value=response) as public:
            tool.verify(c, BUCKET, PHOTO, head(), 'image/jpeg', BASE + PHOTO)
        public.assert_called_once_with(BASE + PHOTO, timeout=30)

    def test_a_good_repair_passes(self):
        self.check()

    def test_each_way_of_going_wrong_stops_the_run(self):
        cases = {
            'type': {'after': head('binary/octet-stream')},
            'bytes': {'after': {**head('image/jpeg'), 'ETag': '"other"'}},
            'length': {'after': {**head('image/jpeg'), 'ContentLength': 4}},
            'metadata': {'after': {**head('image/jpeg'), 'Metadata': {}}},
            # Keeping the right type, so that only the status can catch it.
            'made private': {'status': 403},
            'public type': {'served': 'binary/octet-stream'},
        }
        for name, kwargs in cases.items():
            with self.subTest(name), self.assertRaises(tool.RepairFailed):
                self.check(**kwargs)


class RunTests(unittest.TestCase):

    def fake(self, public=True):
        c = Mock()
        c.get_paginator.return_value.paginate.return_value = [
            {'Contents': [{'Key': PHOTO}, {'Key': THUMB}, {'Key': UUID_PHOTO}]}]
        c.head_object.side_effect = lambda Bucket, Key: head()
        c.get_object_acl.return_value = {'Grants': [OWNER, PUBLIC] if public else [OWNER]}
        return c

    @patch.object(tool, 'verify')
    def test_a_dry_run_writes_nothing(self, verify):
        c = self.fake()
        self.assertEqual(tool.run(c, BUCKET, BASE, apply=False, limit=0), 2)
        c.copy_object.assert_not_called()
        verify.assert_not_called()

    @patch.object(tool, 'verify')
    def test_apply_copies_each_photo_and_checks_it(self, verify):
        c = self.fake()
        self.assertEqual(tool.run(c, BUCKET, BASE, apply=True, limit=0), 2)
        self.assertEqual(sorted(call.kwargs['Key'] for call in c.copy_object.call_args_list),
                         sorted([PHOTO, UUID_PHOTO]))
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(verify.call_args_list[0].args[-1], BASE + 'bucket/' + PHOTO)

    @patch.object(tool, 'verify')
    def test_the_limit_stops_early(self, verify):
        c = self.fake()
        self.assertEqual(tool.run(c, BUCKET, BASE, apply=True, limit=1), 1)
        self.assertEqual(c.copy_object.call_count, 1)

    @patch.object(tool, 'verify')
    def test_a_photo_that_is_not_public_is_not_published(self, verify):
        c = self.fake(public=False)
        self.assertEqual(tool.run(c, BUCKET, BASE, apply=True, limit=0), 0)
        c.copy_object.assert_not_called()

    @patch.object(tool, 'verify', side_effect=tool.RepairFailed('no'))
    def test_the_first_failure_stops_the_run(self, verify):
        c = self.fake()
        with self.assertRaises(tool.RepairFailed):
            tool.run(c, BUCKET, BASE, apply=True, limit=0)
        self.assertEqual(c.copy_object.call_count, 1)
