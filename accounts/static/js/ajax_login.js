$(function() {
   var loginError = $('#login-error');
   var userBox = $('#ajax-login-username');
   var passBox = $('#ajax-login-password');
   var loginDialog = $('#login-dialog').dialog({
      autoOpen: false,
      height: 375,
      width: 380,
      modal: true,
      buttons: [
         {
            id: "login-button",
            text: "Login",
            click: function() {
               loginError.text('').hide();
               $("#login-button").button("disable");
               $.ajax({
                  url: '/accounts/login/ajax/',
                  type: 'POST',
                  data: {
                     username: userBox.val(),
                     password: passBox.val(),
                     csrfmiddlewaretoken: csrf_token
                  },
                  dataType: 'json',
                  success: function(data, textStatus) {
                     $("#login-button").button("enable");
                     if (data.success) {
                        loginDialog.dialog("close");
                        if (window.location.pathname == "/accounts/logout/") {
                           window.location.replace("/");
                        }
                        else {
                           $('#header-nav').html(data.navbar_html);
                        }
                     }
                     else {
                        loginError.text(data.error).show();
                        userBox.val('');
                        passBox.val('');
                        userBox.focus();
                     }
                  },
                  error: function (xhr, textStatus, ex) {
                     $("#login-button").button("enable");
                     if (xhr.status == 403) {
                        loginDialog.dialog("close");
                        alert("Oops, we are detecting some strange behavior and are blocking this action. If you feel this is an error, please feel free to contact us. Thank you.");
                        window.location.href = "/";
                     }
                     else {
                        loginError.text('Oops, an error occurred. If this problem persists, please contact us.').show();
                     }
                  }
               });
            }
         },
         {
            id: "cancel-button",
            text: "Cancel",
            click: function() {
               loginDialog.dialog("close");
            }
         }
      ],
      focus: function() {
         $(':input', this).keyup(function(event) {
            if (event.keyCode == 13) {
                var loginButton = $("#login-button");
                if (!loginButton.button("option", "disabled")) {
                   loginButton.click();
                }
            }
         });
      }
   });
   $('#login-link').click(function() {
      loginError.text('').hide();
      loginDialog.dialog("open");
      return false;
   });
});
