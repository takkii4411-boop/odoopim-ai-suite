/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, onMounted, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class ProductionDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action"); // Add action service for navigation
        this.root = useRef("root");
        this.lineChart = null;
        this.barChart = null;

        // Refs for search and dropdown
        this.refs = {
            searchInput: useRef("searchInput"),
            filterDropdown: useRef("filterDropdown"),
        };

        this.allKpiData = [
            { title: "Total Sync", value: 0, model: "ai.enrichment.queue.log" },
            { title: "Total Updated Product", value: 0, model: "ai.enrichment.queue.log" },
            { title: "Total Failed Product", value: 0, model: "ai.enrichment.queue.log" },
            { title: "Available Enrichment Attribute", value: 0, model: "product.attribute" },
            { title: "Available AI Providers", value: 0, model: "ai.enrichment.config" },
            { title: "Overall Enrichment Products", value: 0 },
        ];

        this.state = {
            kpiData: [...this.allKpiData],
        };

        onWillStart(async () => {
            await this.loadProductCount();
            this.state.syncData = await this.orm.call(
                "ai.enrichment.queue.log",
                "get_sync_data_for_chart",
                [],
                { limit: 20 } // optional
            );
        });

        onMounted(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            this.renderLineChart();
            this.renderBarChart();
        });
    }

    // Add click handler for KPI cards
    onKpiClick(kpi) {
        if (kpi.model) {
            let action = {
                type: "ir.actions.act_window",
                name: kpi.title,
                res_model: kpi.model,
                views: [[false, "list"], [false, "form"]],
                domain: [],
                target: "current",
                context: {},
            };

            // 🔥 Activate search filters by name
            if (kpi.title === "Total Sync") {
                action.context = { search_default_done: 1 };
            }

            if (kpi.title === "Total Updated Product") {
                action.domain = [["update_success_count", ">", 0]];   // ✅ apply filter condition
                action.context = {
                    search_default_update_success: 1,                 // ✅ show filter chip in UI
                };
            }

            if (kpi.title === "Total Failed Product") {
                action.context = {
                    // search_default_done: 1,                       // ✅ adds "Done" filter
                    search_default_update_failed: 1,                 // ✅ adds "Failed Products" filter
                };
            }

            if (kpi.title === "Available Enrichment Attribute") {
                action.domain = [["is_ai_enrichable", "=", true]];  // ✅ actual filter condition
                action.context = {
                    search_default_is_ai_enrichable: 1,              // ✅ highlights filter chip in UI
                };
            }

            this.action.doAction(action);
        }
    }

    async loadProductCount() {
        console.log("=== LOADING DASHBOARD DATA ===");

        try {
            // Load all counts in parallel for better performance
            const [
                productCount,
                providerCount,
                syncStats,
                updateSuccessStats,
                updateFailedStats,
                enrichableFields,
            ] = await Promise.all([
                this.orm.call("ai.enrichment.wizard", "get_product_count", [[]]),
                this.orm.call("ai.enrichment.wizard", "get_ai_provider_count", [[]]),
                this.orm.call("ai.enrichment.wizard", "get_sync_count", [[]]),
                this.orm.call("ai.enrichment.wizard", "get_update_success_count", [[]]),
                this.orm.call("ai.enrichment.wizard", "get_update_failed_count", [[]]),
                this.orm.call("ai.enrichment.wizard", "get_enrichable_fields_count", [[]]),
            ]);

            console.log("Product count:", productCount);
            console.log("AI Provider count:", providerCount);
            console.log("Sync count:", syncStats);
            console.log("Update success count:", updateSuccessStats);
            console.log("Update failed count:", updateFailedStats);
            console.log("Enrichable fields count:", enrichableFields);

            // Extract values from returned objects
            const productCountValue = productCount.product_count || 0;
            const aiProviderCountValue = providerCount.ai_provider_count || 0;
            const syncCountValue = syncStats.sync_count || 0;
            const updateSuccessCountValue = updateSuccessStats.update_success_count || 0;
            const updateFailedCountValue = updateFailedStats.update_failed_count || 0;
            const enrichableFieldsCountValue = enrichableFields.enrichable_fields_count || 0;

            // Update KPI data
            this.allKpiData = this.allKpiData.map((kpi) => {
                if (kpi.title === "Total Sync") {
                    return { ...kpi, value: syncCountValue };
                }
                if (kpi.title === "Total Updated Product") {
                    return { ...kpi, value: updateSuccessCountValue };
                }
                if (kpi.title === "Total Failed Product") {
                    return { ...kpi, value: updateFailedCountValue };
                }
                if (kpi.title === "Available Enrichment Attribute") {
                    return { ...kpi, value: enrichableFieldsCountValue };
                }
                if (kpi.title === "Available AI Providers") {
                    return { ...kpi, value: aiProviderCountValue };
                }
                if (kpi.title === "Overall Enrichment Products") {
                    return { ...kpi, value: productCountValue };
                }
                return kpi;
            });

            this.state.kpiData = [...this.allKpiData];
        } catch (error) {
            console.error("Method call failed:", error);

            // Fallback: Use direct counts
            try {
                const directSyncStats = await this.orm.searchCount("ai.enrichment.queue.log", []);
                const directEnrichableFields = await this.orm.searchCount("product.attribute", [
                    ["is_ai_enrichable", "=", true],
                    ["display_type", "in", ["text", "textarea"]],
                ]);

                // For failed count, sum the field values
                const logs = await this.orm.searchRead(
                    "ai.enrichment.queue.log",
                    [],
                    ["update_failed_count"]
                );
                const directFailedCount = logs.reduce(
                    (sum, log) => sum + (log.update_failed_count || 0),
                    0
                );

                // For success count, sum the field values
                const successLogs = await this.orm.searchRead(
                    "ai.enrichment.queue.log",
                    [],
                    ["update_success_count"]
                );
                const directSuccessCount = successLogs.reduce(
                    (sum, log) => sum + (log.update_success_count || 0),
                    0
                );

                const directProviderCount = await this.orm.searchCount("ai.enrichment.config", []);
                const directProductCount = await this.orm.searchCount("product.product", []);

                console.log(
                    "Direct counts - Products:",
                    directProductCount,
                    "Providers:",
                    directProviderCount,
                    "Sync:",
                    directSyncStats,
                    "Success:",
                    directSuccessCount,
                    "Failed:",
                    directFailedCount,
                    "Enrichable fields:",
                    directEnrichableFields
                );

                this.allKpiData = this.allKpiData.map((kpi) => {
                    if (kpi.title === "Total Sync") {
                        return { ...kpi, value: directSyncStats || 0 };
                    }
                    if (kpi.title === "Total Updated Product") {
                        return { ...kpi, value: directSuccessCount || 0 };
                    }
                    if (kpi.title === "Total Failed Product") {
                        return { ...kpi, value: directFailedCount || 0 };
                    }
                    if (kpi.title === "Available Enrichment Attribute") {
                        return { ...kpi, value: directEnrichableFields || 0 };
                    }
                    if (kpi.title === "Available AI Providers") {
                        return { ...kpi, value: directProviderCount || 0 };
                    }
                    if (kpi.title === "Overall Enrichment Products") {
                        return { ...kpi, value: directProductCount || 0 };
                    }
                    return kpi;
                });

                this.state.kpiData = [...this.allKpiData];
            } catch (fallbackError) {
                console.error("Fallback also failed:", fallbackError);
            }
        }
    }

    onSearchInput() {
        const query = this.refs.searchInput.el.value.toLowerCase();
        const selected = this.refs.filterDropdown.el.value;

        this.state.kpiData = this.allKpiData.filter((kpi) => {
            const matchesSearch = kpi.title.toLowerCase().includes(query);
            const matchesDropdown = selected ? kpi.title === selected : true;
            return matchesSearch && matchesDropdown;
        });
    }

    onDropdownChange() {
        this.onSearchInput();
    }

    renderLineChart() {
        const syncData = this.state.syncData || [];

        const syncIds = syncData.map((item) => item.sync_id);
        const successData = syncData.map((item) => item.success_count);
        const failedData = syncData.map((item) => item.failed_count);

        const ctx = this.root.el.querySelector("#lineChart").getContext("2d");
        if (this.lineChart) this.lineChart.destroy();

        this.lineChart = new window.Chart(ctx, {
            type: "line",
            data: {
                labels: syncIds,
                datasets: [
                    {
                        label: "Success Count",
                        data: successData,
                        borderColor: "#28a745",
                        backgroundColor: "rgba(0, 86, 179, 0.1)",
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: "#28a745",
                        pointRadius: 5,
                        pointHoverRadius: 7,
                    },
                    {
                        label: "Failed Count",
                        data: failedData,
                        borderColor: "#dc3545",
                        backgroundColor: "rgba(255, 102, 0, 0.1)",
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: "#dc3545",
                        pointRadius: 5,
                        pointHoverRadius: 7,
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                        },
                    },
                    title: {
                        display: true,
                    },
                    tooltip: {
                        mode: "index",
                        intersect: false,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Count",
                            font: { weight: "bold" },
                        },
                        ticks: {
                            stepSize: 5,
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: "Sync ID",
                            font: { weight: "bold" },
                        },
                    },
                },
                interaction: {
                    intersect: false,
                    mode: "nearest",
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const record = syncData[index];

                        if (record?.id) {
                            this.action.doAction({
                                type: "ir.actions.act_window",
                                res_model: "ai.enrichment.queue.log",
                                res_id: record.id,
                                views: [[false, "form"]],
                                target: "current",
                            });
                        }
                    }
                },
            },
        });
    }

    async renderBarChart() {
        const updateData = await this.orm.call(
            "ai.enrichment.queue.log",
            "get_update_trends",
            [],
            { days: 10 }
        );

        const formattedDates = updateData.map((item) => {
            const date = new Date(item.date);
            return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        });

        const updateCounts = updateData.map((item) => item.count);

        const ctx = this.root.el.querySelector("#barChart").getContext("2d");
        if (this.barChart) this.barChart.destroy();

        this.barChart = new window.Chart(ctx, {
            type: "bar",
            data: {
                labels: formattedDates,
                datasets: [
                    {
                        label: "Product Update Count",
                        data: updateCounts,
                        backgroundColor: "#4CAF50",
                        borderColor: "#388E3C",
                        borderWidth: 1,
                        borderRadius: 4,
                        hoverBackgroundColor: "#2E7D32",
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                        },
                    },
                    title: {
                        display: true,
                        font: { size: 16 },
                    },
                    tooltip: {
                        callbacks: {
                            title: function (tooltipItems) {
                                const dataIndex = tooltipItems[0].dataIndex;
                                const fullDate = new Date(updateData[dataIndex].date);
                                return fullDate.toLocaleDateString("en-US", {
                                    weekday: "long",
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                });
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: "Product Update Count",
                            font: { weight: "bold" },
                        },
                        ticks: { precision: 0 },
                    },
                    x: {
                        title: {
                            display: true,
                            text: "Date",
                            font: { weight: "bold" },
                        },
                    },
                },
                onClick: (event, elements) => {
                    if (elements.length > 0) {
                        const index = elements[0].index;
                        const clickedDateData = updateData[index];

                        if (clickedDateData && clickedDateData.date) {
                            const selectedDate = clickedDateData.date;
                            const dateObj = new Date(selectedDate);

                            const formattedDate = dateObj.toLocaleDateString("en-US", {
                                day: "2-digit",
                                month: "short",
                                year: "numeric",
                            });

                            const startDate = `${selectedDate} 00:00:00`;
                            const endDate = `${selectedDate} 23:59:59`;

                            this.action.doAction({
                                type: "ir.actions.act_window",
                                name: `Sync Logs - ${formattedDate}`,
                                res_model: "ai.enrichment.queue.log",
                                views: [[false, "list"], [false, "form"]],
                                domain: [
                                    ["create_date", ">=", startDate],
                                    ["create_date", "<=", endDate],
                                ],
                                target: "current",
                                context: {
                                    search_default_group_by_create_date: true,
                                    search_default_done: 1,
                                },
                            });
                        }
                    }
                },
            },
        });
    }
}

ProductionDashboard.template = "AI_Enrichment.ProductionDashboardMain";
registry.category("actions").add("ai_enrichment_dashboard_action", ProductionDashboard);
