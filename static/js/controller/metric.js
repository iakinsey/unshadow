'use strict';


module.exports = function ($scope, server) {
    function renderGraph (stage, metric, data) {
        var chartContainer = $('<div></div>')
            .attr('class', 'graph')
            .css('width', '850px')
            .css('height', '450px')
            .appendTo($('#charts'));

        $.plot(chartContainer, [{
            data: data, 
            label: stage + " " + metric
        }], {
            xaxes: [{mode: "time"}]
        });
    }

    function renderGraphs() {
        var start = new Date(),
            end = new Date();

        end.setDate(end.getDate() - 1);

        server.send('metric', 'list_metrics', {}, function (results) {
            for (var index = 0; index < results.length; index += 1) {
                var metric = results[index];

                server.send('metric', 'get_data', {
                    metric_id: metric.id,
                    start: start,
                    end: end
                }, renderGraph.bind(this, metric.stage, metric.metric));
            }
        });
    }

        /*
        var d1 = [];

        for (var i = 0; i < 14; i += 0.5) {
            d1.push([i, Math.sin(i)]);
        }
        $.plot('#chart-box', [d1]);
        */

        renderGraphs();
};
