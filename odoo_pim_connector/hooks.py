import logging
_logger = logging.getLogger(__name__)

def _update_coming_soon_status(env):
    """
    This hook programmatically sets the 'Coming Soon' status for specific connectors.
    This is more reliable than data files with noupdate="1".
    """
    _logger.info("Running post-init hook to set 'Coming Soon' status.")
    
    platforms_to_disable = [
        'odoo_pim_connector.platform_credentials_magento',
        'odoo_pim_connector.platform_credentials_akeneo',
        'odoo_pim_connector.platform_credentials_shopify',
    ]

    for xml_id in platforms_to_disable:
        record = env.ref(xml_id, raise_if_not_found=False)
        if record:
            record.write({'is_coming_soon': True})
            _logger.info(f"Marked '{record.name}' as 'Coming Soon'.")