/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState } from "@odoo/owl";

// Define our custom component
class SupabindDashboard extends Component {
    setup() {
        // Use the state to hold the URL, making it reactive
        this.state = useState({
            iframeURL: "https://onboarder.odoopim.com",
        });
    }
}

// Link the component to its XML template
SupabindDashboard.template = "supabind_dashboard.SupabindDashboard";

// Register the component with the client action registry.
// The key 'supabind_dashboard.SupabindDashboard' must match the 'tag' in the XML action.
registry.category("actions").add("supabind_dashboard.SupabindDashboard", SupabindDashboard);