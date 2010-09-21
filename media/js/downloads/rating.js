function dlRatingOver(event)
{
    var div = $(this).parent('div');
    var stars = $('img', div);
    for (var i = 0; i <= event.data; ++i)
    {
        var star = $(stars[i]);
        star.attr('src', '/media/downloads/stars/rating_over.gif');
    }
}

function dlRatingOut(event)
{
    var div = $(this).parent('div');
    var stars = $('img', div);
    for (var i = 0; i <= event.data; ++i)
    {
        var star = $(stars[i]);
        star.attr('src', '/media/downloads/stars/rating_' + star.attr('class') + '.gif');
    }
}

function dlRatingClick(event)
{
    var star = $(this);
    var id = star.attr('id');
    if (id.match(/star-(\d+)-(\d+)/))
    {
        $.ajax({
            url: '/downloads/rate/', 
            type: 'POST',
            data: { id: RegExp.$1, rating: parseInt(RegExp.$2)  + 1},
            dataType: 'text',
            success: function(rating) {
                rating = parseFloat(rating);
                if (rating < 0)
                {
                    alert("You've already rated this download.");
                    return;
                }
                alert('Thanks for rating this download!');
                var div = star.parent('div');
                var stars = $('img', div);
                rating = parseFloat(rating);
                for (var i = 0; i < 5; ++i)
                {
                    var s = $(stars[i]);
                    s.removeClass(s.attr('class'));
                    if (rating >= 1.0)
                    {
                        s.attr('src', '/media/downloads/stars/rating_on.gif');
                        s.addClass('on')
                        rating -= 1.0;
                    }
                    else if (rating >= 0.5)
                    {
                        s.attr('src', '/media/downloads/stars/rating_half.gif');
                        s.addClass('half')
                        rating = 0;
                    }
                    else
                    {
                        s.attr('src', '/media/downloads/stars/rating_off.gif');
                        s.addClass('off')
                    }
                }
            },
            error: function (xhr, textStatus, ex) {
                alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                   xhr.responseText);
            }
        });
    }
}

$(document).ready(function() {
    $('.rating').each(function(n) {
        var div = $(this);
        var id = div.attr('id');
        var numeric_id = -1;
        if (id.match(/rating-(\d+)/))
        {
            numeric_id = RegExp.$1;
        }
        var rating = div.html();
        div.html('');
        for (var i = 0; i < 5; ++i)
        {
            var star = $('<img />');
            if (rating >= 1)
            {
                star.attr('src', '/media/downloads/stars/rating_on.gif');
                star.addClass('on')
                --rating;
            }
            else if (rating >= 0.5)
            {
                star.attr('src', '/media/downloads/stars/rating_half.gif');
                star.addClass('half')
                rating = 0;
            }
            else
            {
                star.attr('src', '/media/downloads/stars/rating_off.gif');
                star.addClass('off')
            }
            star.attr('alt', 'star');
            star.attr('id', 'star-' + numeric_id + '-' + i);
            star.bind('mouseover', i, dlRatingOver);
            star.bind('mouseout', i, dlRatingOut);
            star.click(dlRatingClick);
            div.append(star);
        }
    });
});
