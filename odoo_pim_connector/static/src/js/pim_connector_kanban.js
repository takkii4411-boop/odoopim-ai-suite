/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PIMDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");

        this.state = useState({
            dashboardData: {},
            loading: true,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        const data = await this.rpc("/web/dataset/call_kw", {
            model: "platform.credentials",
            method: "search_read",
            args: [[], ["name", "platform", "category"]],
            kwargs: {},
        });

        this.state.dashboardData = data;
        this.state.loading = false;
    }

    static template = xml/* xml */`
        <div class="o_pim_dashboard">
            <h2>Hello from PIM Dashboard!</h2>
        </div>
    `;

}

// 🔑 Register as an action so services exist
registry.category("actions").add("pim_dashboard", PIMDashboard);
