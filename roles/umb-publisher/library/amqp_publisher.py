# Copyright (c) 2019 Red Hat
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

try:
    from proton import Message
    from proton import SSLDomain
    from proton.handlers import MessagingHandler
    from proton.reactor import Container
    HAS_PROTON = True
except ImportError:
    HAS_PROTON = False


DOCUMENTATION = '''
---
module: amqp_publisher
short_description: Publish an AMQP message
options:
  urls:
    description:
      - The AMQP urls
    required: True
  ca:
    description:
      - The TLS Certificate Authority.
  cert:
    description:
      - The TLS client certificate.
  key:
    description:
      - The TLS client key.
  source:
    required: True
    description:
      - The link source name.
  address:
    required: True
    description:
      - The link address name.
  body:
    required: True
    description:
      - The message body.
requirements:
    - "python >= 2.7"
    - "proton"
'''

EXAMPLES = '''
- name: Publish a AMQP message
  amqp_publisher:
    urls:
      - amqps://broker01.example.com
      - amqps://broker02.example.com
    address: /topic/VirtualTopic.qe.ci.zuul
    body:
      build: os-release-4243
      arch: x86_64
      hash: sha256://...
'''


class Publisher(MessagingHandler):
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.sent = False
        self.confirmed = False

    def on_start(self, event):
        conn = event.container.connect(
            urls=self.params['urls'],
            ssl_domain=self.params['ssl_domain'])
        event.container.create_sender(conn)

    def on_sendable(self, event):
        while event.sender.credit and not self.sent:
            event.sender.send(Message(
                body=self.params['body'],
                address=self.params['address']))
            self.sent = True

    def on_accepted(self, event):
        self.confirmed = True
        event.connection.close()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            urls=dict(required=True, type='list'),
            ca=dict(type='path'),
            cert=dict(type='path'),
            key=dict(type='path'),
            address=dict(required=True, type='str'),
            body=dict(required=True, type='dict'),
        )
    )
    if not HAS_PROTON:
        module.fail_json(msg='proton is required for this module')

    if module.params['ca']:
        domain = SSLDomain(SSLDomain.MODE_CLIENT)
        if not module.params['cert'] or not module.params['key']:
            module.fail_json(msg='cert and key are required for ssl')
        domain.set_trusted_ca_db(module.params['ca'])
        domain.set_credentials(
            module.params['cert'], module.params['key'], None)
        domain.set_peer_authentication(SSLDomain.VERIFY_PEER)
    else:
        domain = None
    module.params['ssl_domain'] = domain

    publisher = Publisher(module.params)
    Container(publisher).run()
    if publisher.confirmed:
        module.exit_json(changed=True)
    else:
        module.fail_json(msg='failed to publish the message')


if __name__ == '__main__':
    main()
