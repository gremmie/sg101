// -------------------------------------------------------------------
// markItUp!
// -------------------------------------------------------------------
// Copyright (C) 2008 Jay Salvat
// http://markitup.jaysalvat.com/
// -------------------------------------------------------------------
// MarkDown tags example
// http://en.wikipedia.org/wiki/Markdown
// http://daringfireball.net/projects/markdown/
// -------------------------------------------------------------------
// Feel free to add more tags
// -------------------------------------------------------------------
mySettings = {
	previewParserPath: '/comments/markdown/',
	previewParserVar: 'data',
    previewInWindow: false,
    previewAutoRefresh: false,
    previewPosition: 'after',
	onShiftEnter:		{keepDefault:false, openWith:'\n\n'},
	markupSet: [
		{name:'Bold', key:'B', openWith:'**', closeWith:'**'},
		{name:'Italic', key:'I', openWith:'_', closeWith:'_'},
		{name:'Strike', key:'S', openWith:'---', closeWith:'---'},
		{separator:'---------------' },
		{name:'Bulleted List', openWith:'- ' },
		{name:'Numeric List', openWith:function(markItUp) {
			return markItUp.line+'. ';
		}},
		{separator:'---------------' },
		{name:'Picture', key:'P', replaceWith:'![image]([![Url:!:http://]!])'},
		{name:'Link', key:'L', openWith:'[', closeWith:']([![Url:!:http://]!])', placeHolder:'Your text to link here...' },
		{separator:'---------------'},	
		{name:'Quotes', openWith:'> '},
		{name:'Code Block / Code', openWith:'(!(\t|!|`)!)', closeWith:'(!(`)!)'},
		{separator:'---------------'},
        {name:'Smilies', className:'smilies', dropMenu: [
            {name:'Argh', replaceWith:' :argh: ', className:'col1-1' },
            {name:'Grin', replaceWith:' :-D ', className:'col1-2' },
            {name:'Razz', replaceWith:' :-P ', className:'col1-3' },
            {name:'Confused', replaceWith:' o_O ', className:'col1-4' },
            {name:'Cool', replaceWith:' 8^) ', className:'col1-5' },
            {name:'Cry', replaceWith:' :-( ', className:'col2-1' },
            {name:'Dead', replaceWith:' x_x ', className:'col2-2' },
            {name:'Embarrassed', replaceWith:' :-# ', className:'col2-3' },
            {name:'LOL', replaceWith:' :lol: ', className:'col2-4' },
            {name:'Mad', replaceWith:' X-( ', className:'col2-5' },
            {name:'No', replaceWith:' :no: ', className:'col3-1' },
            {name:'None', replaceWith:' :-| ', className:'col3-2' },
            {name:'Shock', replaceWith:' :shock: ', className:'col3-3' },
            {name:'Sigh', replaceWith:' :sigh: ', className:'col3-4' },
            {name:'Smile', replaceWith:' :-) ', className:'col3-5' },
            {name:'Uh-oh', replaceWith:' :uh-oh: ', className:'col4-1' },
            {name:'Whatever', replaceWith:' :whatever: ', className:'col4-2' },
            {name:'Wink', replaceWith:' ;-) ', className:'col4-3' },
            {name:'Yes', replaceWith:' :yes: ', className:'col4-4' },
            {name:'Sleep', replaceWith:' :sleep: ', className:'col4-5' }
            ]
        },
		{separator:'---------------'},
		{name:'Preview', call:'preview', className:"preview"}
	]
}

// mIu nameSpace to avoid conflict.
miu = {
	markdownTitle: function(markItUp, char) {
		heading = '';
		n = $.trim(markItUp.selection||markItUp.placeHolder).length;
		for(i = 0; i < n; i++) {
			heading += char;
		}
		return '\n'+heading;
	}
}

$(document).ready(function() {
   $('.markItUp').markItUp(mySettings);

   $('#smileys_dialog_popup').dialog({autoOpen:false});
   var firstTimeSmiley = true;
   $('#more_smileys_link').click(function () {
       $('#smileys_dialog_popup').dialog('open');
       var smileyTarget = $('.smileyTarget')[0];
       if (firstTimeSmiley) {
         $.ajax({
            url: '/smiley/farm/extra/',
            type: 'GET',
            dataType: 'html',
            success: function(data, textStatus) {
               var img = $('#smiley_busy');
               img.hide();
               img.after(data);
               $('#smileys_dialog_popup .smiley_farm img').click(function() {
                  smileyTarget.value += ' ' + this.alt + ' ';
                  smileyTarget.focus();
               });
               firstTimeSmiley = false;
            },
            error: function (xhr, textStatus, ex) {
               alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
            }
         });
       }
       return false;
   });
   $('#markdown_help_dialog_popup').dialog({autoOpen: false, width: 720, height: 600});
   var firstTimeMdHelp = true;
   $('#markdown_help_link').click(function () {
       $('#markdown_help_dialog_popup').dialog('open');
       if (firstTimeMdHelp) {
         $.ajax({
            url: '/core/markdown_help/',
            type: 'GET',
            dataType: 'html',
            success: function(data, textStatus) {
               var img = $('#markdown_busy');
               img.hide();
               img.after(data);
               firstTimeMdHelp = false;
            },
            error: function (xhr, textStatus, ex) {
               alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
            }
         });
       }
       return false;
   });
});
