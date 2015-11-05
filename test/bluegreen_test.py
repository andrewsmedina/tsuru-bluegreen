import unittest
from mock import MagicMock
from mock import Mock
import httpretty
from bluegreen import BlueGreen

class TestBlueGreen(unittest.TestCase):

  def setUp(self):
    config = {
      'name': 'test-app',
      'hooks': {'before_pre' : 'echo test', 'after_swap' : 'undefined_command'},
      'newrelic': {'api_key' : 'some-api-key', 'app_id' : '123'},
      'webhook': {'endpoint': 'http://example.com', 'payload_extras': 'key1=value1&key2=value2'}
    }

    self.bg = BlueGreen('token', 'tsuru.globoi.com', config)
    self.cnames = [u'cname1', u'cname2']

  @httpretty.activate
  def test_get_cname_returns_a_list_when_present(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto',
                           body='{"cname":["cname1", "cname2"]}')

    self.assertEqual(self.bg.get_cname('xpto'), self.cnames)

  @httpretty.activate
  def test_get_cname_returns_none_when_empty(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto',
                           body='{"cname":[]}')

    self.assertIsNone(self.bg.get_cname('xpto'))

  @httpretty.activate
  def test_remove_cname_return_true_when_can_remove(self):
    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/cname',
                           data='{"cname":["cname1", "cname2"]}',
                           status=200)

    self.assertTrue(self.bg.remove_cname('xpto', self.cnames))

  @httpretty.activate
  def test_remove_cname_return_false_when_cant_remove(self):
    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/cname',
                           data='{"cname":["cname1", "cname2"]}',
                           status=500)

    self.assertFalse(self.bg.remove_cname('xpto', self.cnames))

  @httpretty.activate
  def test_set_cname_return_true_when_can_set(self):
    httpretty.register_uri(httpretty.POST, 'http://tsuru.globoi.com/apps/xpto/cname',
                           data='{"cname":["cname1", "cname2"]}',
                           status=200)

    self.assertTrue(self.bg.set_cname('xpto', self.cnames))

  @httpretty.activate
  def test_set_cname_return_false_when_cant_set(self):
    httpretty.register_uri(httpretty.POST, 'http://tsuru.globoi.com/apps/xpto/cname',
                           data='{"cname":["cname1", "cname2"]}',
                           status=500)

    self.assertFalse(self.bg.set_cname('xpto', self.cnames))

  @httpretty.activate
  def test_env_set_return_true_when_can_set(self):
    httpretty.register_uri(httpretty.POST, 'http://tsuru.globoi.com/apps/xpto/env',
                           data='{"TAG":"tag_value"}',
                           status=200)

    self.assertTrue(self.bg.env_set('xpto', 'TAG', 'tag_value'))

  @httpretty.activate
  def test_env_set_return_false_when_cant_set(self):
    httpretty.register_uri(httpretty.POST, 'http://tsuru.globoi.com/apps/xpto/env',
                           data='{"TAG":"tag_value"}',
                           status=500)

    self.assertFalse(self.bg.env_set('xpto', 'TAG', 'tag_value'))

  @httpretty.activate
  def test_env_get_returns_a_value_when_present(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto/env',
                           data='["TAG"]',
                           body='[{"name":"TAG","public":true,"value":"1.0"}]')

    self.assertEqual(self.bg.env_get('xpto', 'TAG'), '1.0')

  @httpretty.activate
  def test_env_get_returns_none_when_null(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto/env',
                           data='["TAG"]',
                           body='null')

    self.assertIsNone(self.bg.env_get('xpto', 'TAG'))

  @httpretty.activate
  def test_env_get_returns_none_when_null(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto/env',
                           data='["TAG"]',
                           body='[]')

    self.assertIsNone(self.bg.env_get('xpto', 'TAG'))

  @httpretty.activate
  def test_total_units_empty_without_units(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto',
                           body='{"units":[]}',
                           status=500)

    self.assertEqual(self.bg.total_units('xpto'), {})

  @httpretty.activate
  def test_total_units_grouped_per_process_name(self):
    httpretty.register_uri(httpretty.GET, 'http://tsuru.globoi.com/apps/xpto',
                           body='{"units":[{"ProcessName": "web"}, {"ProcessName": "resque"}, {"ProcessName": "web"}]}',
                           status=500)

    self.assertEqual(self.bg.total_units('xpto'), {'web': 2, 'resque': 1})

  @httpretty.activate
  def test_remove_units_should_return_true_when_removes_web_units(self):
    self.bg.total_units = Mock(side_effect=self.mock_total_units([{'web': 2}, {'web': 0}]))

    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='',
                           status=200)

    self.assertTrue(self.bg.remove_units('xpto'))
    self.assertEqual({"units": ["2"], "process": ["web"]}, httpretty.last_request().querystring)

  @httpretty.activate
  def test_remove_units_should_return_true_when_removes_web_and_resque_units(self):
    self.bg.total_units = Mock(side_effect=self.mock_total_units([{'web': 4, 'resque': 2}, {'web': 0, 'resque': 2}, {'web': 0, 'resque': 0}]))

    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='',
                           status=200)

    self.assertTrue(self.bg.remove_units('xpto'))

    requests = httpretty.HTTPretty.latest_requests
    self.assertEqual(len(requests), 2)
    self.assertEqual({"units": ["4"], "process": ["web"]}, requests[0].querystring)
    self.assertEqual({"units": ["2"], "process": ["resque"]}, requests[1].querystring)

  @httpretty.activate
  def test_remove_units_should_allow_keep_units(self):
    self.bg.total_units = Mock(side_effect=self.mock_total_units([{'web': 4, 'resque': 2}, {'web': 1, 'resque': 2}, {'web': 1, 'resque': 1}]))

    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='',
                           status=200)

    self.assertTrue(self.bg.remove_units('xpto', 1))

    requests = httpretty.HTTPretty.latest_requests
    self.assertEqual(len(requests), 2)
    self.assertEqual({"units": ["3"], "process": ["web"]}, requests[0].querystring)
    self.assertEqual({"units": ["1"], "process": ["resque"]}, requests[1].querystring)

  @httpretty.activate
  def test_remove_units_should_return_false_when_doesnt_remove(self):
    self.bg.total_units = MagicMock(return_value={'web': 2})

    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='',
                           status=500)

    self.assertFalse(self.bg.remove_units('xpto'))

  @httpretty.activate
  def test_remove_units_should_return_false_when_doesnt_remove_all_process_types(self):
    self.bg.total_units = MagicMock(return_value={'web': 2, 'resque': 1})

    httpretty.register_uri(httpretty.DELETE, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='',
                           responses=[
                               httpretty.Response(body='', status=500),
                               httpretty.Response(body='', status=200)
                           ])

    self.assertFalse(self.bg.remove_units('xpto'))

    requests = httpretty.HTTPretty.latest_requests
    self.assertEqual(len(requests), 2)

  @httpretty.activate
  def test_add_units_should_return_true_when_adds(self):
    self.bg.total_units = MagicMock(side_effect=self.mock_total_units([1, 2]))

    httpretty.register_uri(httpretty.PUT, 'http://tsuru.globoi.com/apps/xpto/units?units=1',
                           data='1',
                           status=200)

    self.assertTrue(self.bg.add_units('xpto', 2))
    self.assertEqual({"units": ["1"]}, httpretty.last_request().querystring)

  @httpretty.activate
  def test_add_units_should_return_false_when_adds(self):
    self.bg.total_units = MagicMock(return_value=1)

    httpretty.register_uri(httpretty.PUT, 'http://tsuru.globoi.com/apps/xpto/units',
                           data='1',
                           status=500)

    self.assertFalse(self.bg.add_units('xpto', 2))

  @httpretty.activate
  def test_notify_newrelic_when_config_defined(self):
    httpretty.register_uri(httpretty.POST, 'http://api.newrelic.com/deployments.xml',
                           data='deployment[application_id]=some-api-key&deployment[revision]=1.0',
                           content_type='application/x-www-form-urlencoded',
                           forcing_headers={
                             'x-api-key': 'some-api-key'
                           },
                           status=200)

    self.assertTrue(self.bg.notify_newrelic('1.0'))

  def test_dont_notify_newrelic_when_config_undefined(self):
    self.bg.newrelic = {}
    self.assertFalse(self.bg.notify_newrelic('1.0'))

  @httpretty.activate
  def test_dont_notify_newrelic_when_wrong_api_key(self):
    httpretty.register_uri(httpretty.POST, 'http://api.newrelic.com/deployments.xml',
                           data='deployment[application_id]=some-api-key&deployment[revision]=1.0',
                           status=403)
    self.assertFalse(self.bg.notify_newrelic('1.0'))

  @httpretty.activate
  def test_dont_notify_newrelic_when_error(self):
    httpretty.register_uri(httpretty.POST, 'http://api.newrelic.com/deployments.xml',
                           data='deployment[application_id]=some-api-key&deployment[revision]=1.0',
                           status=500)
    self.assertFalse(self.bg.notify_newrelic('1.0'))

  @httpretty.activate
  def test_run_webhook_when_config_defined(self):
    httpretty.register_uri(httpretty.POST, 'http://example.com/',
                           data='key1=value1&key2=value2&tag=1.0',
                           content_type='application/x-www-form-urlencoded',
                           status=200)

    self.assertTrue(self.bg.run_webhook('1.0'))

  def test_dont_run_webhook_when_config_undefined(self):
    self.bg.webhook = {}
    self.assertFalse(self.bg.run_webhook('1.0'))

  @httpretty.activate
  def test_dont_run_webhook_when_error(self):
    httpretty.register_uri(httpretty.POST, 'http://example.com/',
                           data='key1=value1&key2=value2&tag=1.0',
                           status=500)
    self.assertFalse(self.bg.run_webhook('1.0'))

  def test_run_command_should_return_true_on_success(self):
    self.assertTrue(self.bg.run_command('echo test'))

  def test_run_command_should_return_false_on_error(self):
    self.assertFalse(self.bg.run_command('cat undefined_file'))

  def test_run_command_should_return_false_on_undefined_command(self):
    self.assertFalse(self.bg.run_command('undefined_command'))

  def test_run_command_should_accept_environment_variables(self):
    self.assertTrue(self.bg.run_command('./test/env_test.sh', {'VAR': '0'}))
    self.assertFalse(self.bg.run_command('./test/env_test.sh', {'VAR': '1'}))

  def test_run_hook_should_return_true_on_successful_command(self):
    self.assertTrue(self.bg.run_hook('before_pre'))

  def test_run_hook_should_return_false_on_failing_command(self):
    self.assertFalse(self.bg.run_hook('after_swap'))

  def test_run_hook_should_return_true_on_undefined_hook(self):
    self.assertTrue(self.bg.run_hook('after_pre'))

  def mock_total_units(self, values):
    calls = {'count': 0}
    def total_units(*args, **kwargs):
      result = values[calls['count']]
      calls['count'] += 1
      return result
    return total_units
