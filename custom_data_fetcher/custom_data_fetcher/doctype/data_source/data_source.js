frappe.ui.form.on("Data Source", {
    refresh(frm) {
        frm.add_custom_button(__('Trigger Source'), function () {
            frappe.call({
                method: "custom_data_fetcher.custom_data_fetcher.automation.trigger_data_source", 
                args: {
                    title:"3 idiots",
                    data_source:frm.doc.name
                    
                },
                callback: function(response) {
                        frappe.show_alert({
                            message: __('Source triggered successfully!'),
                            indicator: 'green'
                        });

                        console.log(response.message);
                    
                },
                error: function(err) {
                    frappe.show_alert({
                        message: __('Failed to trigger source. Please check the logs.'),
                        indicator: 'red'
                    });
                    console.error(err);
                }
            });
        });

        frm.add_custom_button(__("Background Jobs"), function () {
    frappe.set_route("List", "Background Job");
});

frm.add_custom_button(__("Movie Database"), function () {
    frappe.set_route("List", "Movie Database");
});

    },
});
