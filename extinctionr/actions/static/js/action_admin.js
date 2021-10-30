$(function() {

    var virtual_label = "Meeting URL:"
    var virtual_help = "Enter a meeting URL (eg. zoom or jitsi meet)"

    // Find the virtual setting eheckbox.
    var $field = $('#id_location').closest('.field');
    var $label = $field.children('label');
    var $help = $field.find('.help');

    // Save current values.
    var location_label = $label.text();
    var location_help = $help.text();

    function set_labels(is_virtual) {
        if (is_virtual) {
            $label.text(virtual_label);
            $help.text(virtual_help);
        } else {
            $label.text(location_label);
            $help.text(location_help);
        }
    }

    $virtual = $('#id_virtual');

    $virtual.change(function () {
        set_labels(this.checked);
    });

    // Set initial labels.
    set_labels($virtual[0].checked);
});