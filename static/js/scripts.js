
$(document).ready(function() {

    // Demo #1
    // we use an inline data source in the example, usually data would be fetched from a server
    var data = [], totalPoints = 300;
    function getRandomData() {
        if (data.length > 0)
            data = data.slice(1);
    
        // do a random walk
        while (data.length < totalPoints) {
            var prev = data.length > 0 ? data[data.length - 1] : 50;
            var y = prev + Math.random() * 10 - 5;
            if (y < 0)
                y = 0;
            if (y > 100)
                y = 100;
            data.push(y);
        }
    
        // zip the generated y values with the x values
        var res = [];
        for (var i = 0; i < data.length; ++i)
            res.push([i, data[i]])
        return res;
    }
    
    // setup control widget
    var updateInterval = 80;
    $("#updateInterval").val(updateInterval).change(function () {
        var v = $(this).val();
        if (v && !isNaN(+v)) {
            updateInterval = +v;
        if (updateInterval < 1)
            updateInterval = 1;
        if (updateInterval > 2000)
            updateInterval = 2000;
        $(this).val("" + updateInterval);
        }
    });
    
    // setup plot
    var options = {
        series: { color: '#389abe' }, // drawing is faster without shadows
        yaxis: { min: 0, max: 100 },
        xaxis: { show: false },
        grid: { backgroundColor: 'transparent', color: '#b2b2b2', borderColor: '#e7e7e7', borderWidth: 1 }
    };
    var plot = $.plot($("#demo-1"), [ getRandomData() ], options);
    
    function update() {
        plot.setData([ getRandomData() ]);
        // since the axes don't change, we don't need to call plot.setupGrid()
        plot.draw();
        setTimeout(update, updateInterval);
    }
    
    update();

});

$(document).ready(function() {
    
    $('.todo-block input[type="checkbox"]').click(function(){
        $(this).closest('tr').toggleClass('done');
    });
    $('.todo-block input[type="checkbox"]:checked').closest('tr').addClass('done');
    
});



$(document).ready(function(){
    
    $.jGrowl("Hello stranger!", { 
        theme: 'lindworm',
        life: 2500
    });
    
    $.jGrowl("This notification will live a little longer. This is default style.", {
        beforeClose: function() {
            return false;
        }
    });
    
    $.jGrowl.defaults.closerTemplate = '<div>hide all notifications</div>';
    
});

$(document).ready(function() {

    // Sample line chart
    $('.sparkline.line').sparkline('html', {
        height: '45px',
        width: '90px',
        lineColor: '#6CC84C',
        fillColor: '#b1dfa1',
        spotColor: '#3a87ad',
        minSpotColor: false,
        maxSpotColor: false,
        spotRadius: 3
    });
    
    // Sample bar chart
    $('.sparkline.bar').sparkline([17, 23, 18, 14, 18, 19, 13], {
        type: 'bar',
        height: '45px',
        barWidth: '8px',
        barColor: '#3a87ad',
        tooltipFormat: '{{offset:names}}: {{value}} orders',
        tooltipValueLookups: {
        names: {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday'
            }
        }
    });
    
});