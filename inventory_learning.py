from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from collections import namedtuple
from ansible.executor.playbook_executor import PlaybookExecutor
from callback import PlaybookResultsCollector
import os

SCRIPT_DIR = '.'
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
ANSIBLE_PLAYBOOK_PATH=ROOT_DIR

print(ROOT_DIR)
print(ANSIBLE_PLAYBOOK_PATH)




class DynamicInventory(InventoryManager):
    """
    Subclass of `InventoryManager` to create and manage inventory
    """

    def __init__(self, loader, sources, resource):
        """create inventory
        """
        super(DynamicInventory, self).__init__(loader=loader, sources=sources)
        self.__resource = resource
        self.__manage_inventory()

    def __manage_inventory(self):
        """manage inventory - a) add groups and assign hosts to it b) add host variables
        """
        for k, v in self.__resource.items():
            group = k
            host_list = v["hosts"]
            self.__add_group(group)
            for host in host_list:
                self.__add_host(host, group)
                self.__add_host_variables(host)
    
    def __add_host_variables(self, host):
        """setting host variables dynamically. It's a very rigid way of
        setting variables.isn't it? :-/
        """
        super(DynamicInventory, self).get_host(host).vars["ansible_user"] = "navi"
        super(DynamicInventory, self).get_host(host).vars["ansible_ssh_pass"] = "navi"

    def __add_host(self, host, group):
        """calling InventoryManager's add_host method
        """
        super(DynamicInventory, self).add_host(host, group)

    def __add_group(self, group_name):
        """calling InventoryManager's add_group method
        """
        super(DynamicInventory, self).add_group(group_name)


class Inventory(object):
    def __init__(self, resource):
        """creates `DataLoader`, `DynamicInventory` and `VariableManager` objects
        and bundles them together as one single Inventory object
        """
        # dummy inventory file, which is currently not being used because we are using dynamic
        # inventory...but somehow I couldn't bypass this setting.
        self.dummy_inventory = ("hosts_all")
        # DataLoader object - takes care of finding and reading yaml, json and ini files
        self.loader = DataLoader()

        # DynamicInventory object
        self.inventory = DynamicInventory(loader=None, sources=self.dummy_inventory, resource=resource)

        # VariableManager object - it takes care of merging all the different sources to
        # give you a unifed view of variables available in each context
        self.variable_manager = VariableManager(self.loader, self.inventory)

    def extra_vars(self, extra_vars):
        """sets extra variable i.e. to be passed along with ansible-playbook command
        """
        self.variable_manager.extra_vars = extra_vars

hosts_list={
    "juniper_srx": {
                    "hosts": [
                        "host1.oracle.com",
                        "host2.oracle.com"
                    ]
                }
            }

#import pdb;pdb.set_trace()
#obj=Inventory(hosts_list)



class Playbook(Inventory):
    """This class facilitates the complete workflow of creating inventory, running playbook and
    collecting results via callbacks
    """
    def __init__(self, resource, **meta):
        """
         Constructor of `Playbook` class. Initializes base class
        `Inventory` to set inventory and variables

        Args:
            resource (:obj:`dict`): dynamic inventory structure.
            **meta: metadata information as keyword arguments.

        Returns:
            None
        """
        super(Playbook, self).__init__(resource)
        self.__callback = None
        #self.resource = resource #FIXME
        self.__meta = meta

    def run_playbook(self, playbook_name="site.yml", ev=None, tag=()):
        """Run playbook with all the required data.
        Instantiate callbacks for handling data as they come in.
        """

        self.playbook = os.path.join(ANSIBLE_PLAYBOOK_PATH, playbook_name)
        self.extra_vars(ev)

        # since API is constructed for CLI it expects certain options to always be set
        # named tuple 'fakes' the args parsing options object
        Options = namedtuple(
            "Options",
            [
                "connection",
                "module_path",
                "forks",
                "become",
                "become_method",
                "become_user",
                "check",
                "diff",
                "listhosts",
                "listtasks",
                "listtags",
                "syntax",
                "tags",
                "verbose",
            ],
        )

        self.options = Options(
            connection="ssh",
            module_path="%s/" % ('.'),
            forks=100,
            become=None,
            become_method=None,
            become_user=None,
            check=False,
            diff=False,
            listhosts=False,
            listtasks=False,
            listtags=False,
            syntax=False,
            # tags=(
            #    'srx_ab_configuration','srx_app_configuration'
            # ),
            tags=tag,
            verbose=False,
        )

        try:
            # Instantiate our callback for handling results as they come in.
            # Ansible expects this to be one of its main display outlets
            self.__callback = PlaybookResultsCollector(**self.__meta)

            executor = PlaybookExecutor(
                playbooks=[self.playbook],
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords={},
            )

            executor._tqm._stdout_callback = self.__callback
            results = executor.run()
        except Exception as err:
              print(err)
              raise

    def get_playbook_result(self):
        """returns playbook execution result"""

        self.results_raw = {
            "skipped": {},
            "failed": {},
            "ok": {},
            "status": {},
            "unreachable": {},
            "changed": {},
        }
        for host, result in self.__callback.task_ok.items():
            self.results_raw["ok"][host] = result

        for host, result in self.__callback.task_failed.items():
            self.results_raw["failed"][host] = result

        # for host, result in self.__callback.task_status.items():
        #    self.results_raw['status'][host] = result

        for host, result in self.__callback.task_changed.items():
            self.results_raw["changed"][host] = result

        for host, result in self.__callback.task_skipped.items():
            self.results_raw["skipped"][host] = result

        for host, result in self.__callback.task_unreachable.items():
            self.results_raw["unreachable"][host] = result
        return self.results_raw



hosts_list={
    "juniper_srx": {
                    "hosts": [
                        "rabbitmq-2",
                        "diyvb2"
                    ]
                }
            }


"""configs={"host1":
               {"adress_book":[
                     "address_book-1 creation command 1",
                     "address_book-2 creation command"
                  ],
                  "applications":[
                     [
                        "application-1 creation command part 1/2",
                        "application-1 creation command part 2/2"
                     ]
                  ],
                  "policies":[
                     [
                        "policy-1 creation command part 1/2",
                        "policy-1 creation command part 2/2"
                     ]
                  ]
               }
            }"""


configs={"rabbitmq-2":
             {"cmd":"ls"},
          "diyvb2":
             {"cmd":"ls"}
        }

#import pdb;pdb.set_trace()
pb = Playbook(hosts_list)
pb.run_playbook("site.yml", {"configs": configs})
data = pb.get_playbook_result()
print(data)
print("\n\n\n")

# data['ok']['rabbitmq-2'][3]._result
for k,v in data.items():
    for k1,v1 in v.items():
        for item in v1:
           if 'stdout_lines' in item._result:
               print(k1)
               print(item._result['stdout_lines'])
               print
