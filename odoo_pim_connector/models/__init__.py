# The order of imports here MATTERS.

# 1. Import the base models first.
from . import platform_credentials

# 2. Import the wizard base (if it exists)
from .. import wizards

# 3. Import the models that DEPEND on the base models.
from . import sync_log
from . import field_mapping

# 4. Import models that are separate or inherit from Odoo models.
from . import product_template
from . import push_to_channel_wizard # This is a transient model, order is less critical

from . import platform_mapping

from . import n8n_workflow_config
# from . import pim_dashboard