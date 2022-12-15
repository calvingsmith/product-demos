from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: CISA Known Exploited Vulnerabilities
    plugin_type: inventory
    author:
      - Will Tome (wtome@redhat.com)
    short_description: Dynamic inventory plugin for the CISA Catalog of Known Exploited Vulnerabilities
    version_added: "n/a"
    extends_documentation_fragment:
        - constructed
    options:
        plugin:
            description: Token that ensures this is a source file for the plugin.
            required: true
            choices: ['redhatgov.tools.cisa']
        source:
            description: path to known_exploited_vulnerabilities.json
            type: string
    requirements:
        - python >= 3.8
        - requests >= 1.1
'''
EXAMPLES = r'''
# example cisa.yml file
---
plugin: redhatgov.tools.cisa
'''

from ansible.plugins.inventory import BaseFileInventoryPlugin, Constructable,to_safe_group_name
from ansible.errors import AnsibleError
from distutils.version import LooseVersion
import json


try:
    import requests
    if LooseVersion(requests.__version__) < LooseVersion('1.1.0'):
        raise ImportError
except ImportError:
    raise AnsibleError('This plugin requires python-requests 1.1 as a minimum version')


class InventoryModule(BaseFileInventoryPlugin, Constructable):

    NAME = 'redhatgov.tools.cisa'

    def verify_file(self, path):
      super(InventoryModule, self).verify_file(path)
      return path.endswith(('cisa.yml', 'cisa.yaml'))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        # load options from inventory file
        source = self.get_option('source')
        strict = self.get_option('strict')

        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

        if source is None:
            response = requests.get(url).json()
        else:
            f = open(source, "r")
            response = json.load(f)
            f.close()

        for entry in response['vulnerabilities']:
            if 'vendorProject' in entry and 'product' in entry:
                safe_name = to_safe_group_name('{} {}'.format(entry['vendorProject'].lower(),entry['product'].lower()))
                group_name = self.inventory.add_group(safe_name)
                for key in entry:
                    self.inventory.set_variable(group_name, key, entry[key])
                    self.inventory.set_variable(group_name, 'catalogVersion', response['catalogVersion'])
                    self.inventory.set_variable(group_name, 'dateReleased', response['dateReleased'])
            else:
                print("Skipping :{}".format(entry))