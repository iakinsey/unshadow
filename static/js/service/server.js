'use strict';


module.exports = function ($rootScope) {
    var self = {};

    self.send = function (service, method, data, callback) {
        $.ajax({
            url: location.origin + '/' + 'unshadow' + '/' + service + '/' + method,
            type: 'post',
            data: JSON.stringify(data),
            complete: function (result) {
                callback(result.responseJSON);
            },
            dataType: 'json',
            contentType: 'application/json'
        });
    };

    return self;
};
