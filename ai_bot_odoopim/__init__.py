from . import controllers

def uninstall_ai_cleanup(env):
    """Cleanup function to remove AI Bot configuration keys on module uninstall."""
    # Remove AI Bot configuration parameters from ir.config_parameter
    env['ir.config_parameter'].sudo().search([('key', 'in', ['ai_bot.ai_bot_api_key', 'ai_bot.ai_bot_model'])]).unlink()

    print("AI Bot configuration keys removed during uninstall.")