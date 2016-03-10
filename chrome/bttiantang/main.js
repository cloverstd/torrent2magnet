$(function() {
    var $tinfo = $('.tinfo');
    function createBtn() {
        var $div = $('<div style="float:right;"><button class="to-magnet">获取磁力链接</button></div>');
        return $div;
    }
    function createMiRouteBtn() {
        var $div = $('<div style="float:right;"><a target="_blank" class="miroute-down" href="javascript:void(0)">下载到小米路由器</button></a>');
        return $div;
    }
    $.each($tinfo, function(e) {
        $(this).prepend(createBtn());
        $(this).prepend(createMiRouteBtn());
        var $a = $(this).children('a');
        var url = $a.attr('href');
        $a.data('href', url);
        $a.attr('href', "javascript:;");
        $a.removeAttr('target');
        // $a.addClass('to-magnet');
    });

    function getMagnet(url, cb) {
        $.get(url, function(res) {
            var downloadUrl = res.match(/<form action="(.*)" method="post">/)[1];
            var input_id = res.match(/<input type="hidden" value="(\d+)" name="id">/)[1];
            var input_uhash = res.match(/<input type="hidden" value="([a-zA-Z0-9]+)" name="uhash">/)[1];
            var data = {
                "url": downloadUrl,
                "id": input_id,
                "uhash": input_uhash,
                "imageField.x": 84,
                "imageField.y": 44
            };
            $.post("http://t.2.m.hui.lu/api/torrent/bttiantang", data, function(res) {
                console.log(res);
                if ($.isFunction(cb)) {
                    cb(res);
                }
            });
        });
    }

    $('.tinfo').on('click', '.miroute-down', function(e) {
        var $a = $(this).parent().parent().children('a');
        var url = $a.data('href');
        var _this = $(this);
        _this.prop('disabled', true);
        getMagnet(url, function(res) {
            // window.location.href = 'http://d.miwifi.com/d2r/?url=' + Base64.encodeURI(res.data.magnet) + "&src=demo";
            _this.attr('href', 'http://d.miwifi.com/d2r/?url=' + Base64.encodeURI(res.data.magnet) + "&src=demo");
            _this.text('再次点击下载');
        });
    });
    $('.tinfo').on('click', '.to-magnet', function(e) {
        var $a = $(this).parent().parent().children('a');
        var url = $a.data('href');
        var _this = $(this);
        _this.prop('disabled', true);
        getMagnet(url, function(res) {
            var $input = $("<input class='magnet-link'/>");
            $input.val(res.data.magnet);
            _this.parent().append($input);
            _this.remove();
        })
    });

    $('.tinfo').on('mouseenter', '.magnet-link', function() {
        $(this).select();
    });
    $('.tinfo').on('mouseleave', '.magnet-link', function() {
        $(this).blur();
    });
});

