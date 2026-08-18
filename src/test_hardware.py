from collectors.hardware import (
    get_hardware_info,
)

from pprint import pprint


hardware = get_hardware_info()


pprint(
    hardware,
    sort_dicts=False,
)