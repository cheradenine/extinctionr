$(function() {
    let textColor = (r, g, b) => {
        let luminance = (0.299 * r + 0.587 * g + 0.114 * b)/255;
        return (luminance > 0.5) ? 'black' : 'white';
    }
    let parseColor = (rgb) => {
        let vals = [];
        let css = '';
        if (rgb[0] == '#') {
            let val = parseInt(rgb.slice(1), 16);
            // Split into bytes
            vals = [
                (val >> 16) & 0xff,
                (val >> 8) & 0xff,
                val & 0xff
            ]
            css = rgb;
        } else {
            rgb = rgb.substr(4).split(")")[0].split(',');
            vals = rgb.map(v => { return parseInt(v); });
            let hex = vals.map(v => {
                x = v.toString(16);
                return (x.length == 1) ? "0"+x:x;
            });
            css = '#' + hex.join('');
        }
        return {
            rgb: vals,
            css: css
        }
    }

    $('.xr-color-picker .cell').each(function() {
        let $cell = $(this);

        // Get the input control we're attached to.
        let inputId = $cell.closest('.field').children('label').attr('for');
        let $input = $('#' + inputId);

        // Get the dropdown we're part of:
        let $dropdown = $cell.closest('.dropdown');
        let $label = $dropdown.children('.button');

        let bg = parseColor($cell.css('background-color'));
        let fore = textColor(...bg.rgb);

        let cur = $input.val();
        if (cur && cur[0] == '#') {
            let curbg = parseColor(cur);
            let curfore = textColor(...curbg.rgb);
            $dropdown.css('background-color', curbg.css);
            $label.css('color', curfore);
        }

        $cell.on('click', function() {
            $input.val(bg.css);

            $dropdown.css('background-color', bg.css);
            $label.css('color', fore);

            // close the dropdown
            $dropdown.removeClass('open');
            $(document).off('click.dropdown.cancel');    
        });
    });
});