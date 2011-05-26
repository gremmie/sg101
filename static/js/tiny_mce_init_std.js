tinyMCE.init({
   mode : "textareas",
   theme : "advanced",
   convert_urls: false,
   theme_advanced_toolbar_location : "top",
   theme_advanced_toolbar_align : "left",
   theme_advanced_buttons1 : "fullscreen,|,preview,|,bold,italic,underline,strikethrough,|,bullist,numlist,outdent,indent,|,undo,redo,|,link,unlink,anchor,|,image,cleanup,help,|,code",
   theme_advanced_buttons2 : "pastetext,pasteword,selectall",
   theme_advanced_buttons3 : "",
   auto_cleanup_word : true,
   plugins : "table,advhr,emotions,insertdatetime,preview,searchreplace,print,contextmenu,fullscreen,media,paste",
   paste_auto_cleanup_on_paste: true,
   plugin_insertdate_dateFormat : "%m/%d/%Y",
   plugin_insertdate_timeFormat : "%H:%M:%S",
   fullscreen_settings : {
      theme_advanced_path_location : "top",
      theme_advanced_buttons1 : "fullscreen,|,preview,|,cut,copy,paste,|,undo,redo,|,search,replace,|,code,|,cleanup,|,bold,italic,underline,strikethrough,|,forecolor,backcolor,|,justifyleft,justifycenter,justifyright,justifyfull,|,help",
      theme_advanced_buttons2 : "removeformat,styleselect,formatselect,fontselect,fontsizeselect,|,bullist,numlist,outdent,indent,|,link,unlink,anchor",
      theme_advanced_buttons3 : "sub,sup,|,image,insertdate,inserttime,|,tablecontrols,|,hr,advhr,visualaid,|,charmap,emotions,|,print",
      theme_advanced_buttons4 : "pastetext,pasteword,selectall"
   }
});
