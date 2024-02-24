function btn_loading(elem) {
  $(elem).attr("data-original-text", $(elem).html());
  $(elem).prop("disabled", true);
  $(elem).html('<i class="spinner-border spinner-border-sm"></i> Loading...');
}

function btn_loaded(elem) {
  $(elem).prop("disabled", false);
  $(elem).html($(elem).attr("data-original-text"));
}

$.ajaxSetup({
  statusCode: {
    401: function () {
      location.replace("/login");
    },
  },
});
