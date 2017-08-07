require([
  'jquery',
], function ($) {
  'use strict';
  $(document).ready(function () {
    $('.area-notify .subscription-button').click(function (e) {
      e.preventDefault();
      $.ajax($(this).attr('href'), {
        dataType: 'json',
      })
      .done(function (data) {
        $('.notify-message').remove();
        if (data.status === 'error') {
          var $html = $('<div/>', {
            class: 'notify-message alert alert-danger',
            role: 'alert',
            html: '<span class="glyphicon glyphicon-alert" aria-hidden="true"></span> ' + data.message,
          });
          $html.hide().prependTo('dd.subscribeable-areas').fadeIn();

          setTimeout(function () {
            $html.fadeOut();
            setTimeout(function () {
              $html.remove();
            }, 1000);
          }, 5000);

          return;
        }

        var $target = $('[data-groupid="' + data.group_id + '"] span.glyphicon');
        if ($target.length > 0) {
          if (data.subscribed) {
            $target.removeClass('glyphicon-unchecked');
            $target.addClass('glyphicon-check');
          } else {
            $target.addClass('glyphicon-unchecked');
            $target.removeClass('glyphicon-check');
          }
        }

      })
      .fail(function (err) {
        console.error(err);
      });
    });
  });
});
