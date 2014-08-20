var getGuid = (function () {
    function s4() {
        return Math.floor((1 + Math.random()) * 0x10000)
                   .toString(16)
                   .substring(1);
    }
    return function () {
        return s4() + s4() + '-' + s4() + '-' + s4() + '-' +
               s4() + '-' + s4() + s4() + s4();
    };
})();

var getCookie = function (cname) {
    var name = cname + "=",
        ca = document.cookie.split(';'),
        i,
        c;
    for (i = 0; i < ca.length; i++) {
        c = ca[i];
        while (c.charAt(0) === ' ') { c = c.substring(1); }
        if (c.indexOf(name) !== -1) { return c.substring(name.length, c.length); }
    }
    return "";
};

var uuid = getCookie('uuid');
if (uuid === '') {
    var guid = getGuid();
    document.cookie = 'uuid=' + guid;
}
