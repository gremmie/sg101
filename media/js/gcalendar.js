var gcalTzInfo = {
    areas: ['Africa', 'America', 'Antarctica', 'Asia', 'Atlantic', 'Australia', 'Europe', 'Indian', 'Pacific', 'US'],
    locations: [['Abidjan', 'Accra', 'Addis Ababa', 'Algiers', 'Asmara', 'Bamako', 'Bangui', 'Banjul', 'Bissau', 'Blantyre', 'Brazzaville', 'Bujumbura', 'Cairo', 'Casablanca', 'Ceuta', 'Conakry', 'Dakar', 'Dar es Salaam', 'Djibouti', 'Douala', 'El Aaiun', 'Freetown', 'Gaborone', 'Harare', 'Johannesburg', 'Kampala', 'Khartoum', 'Kigali', 'Kinshasa', 'Lagos', 'Libreville', 'Lome', 'Luanda', 'Lubumbashi', 'Lusaka', 'Malabo', 'Maputo', 'Maseru', 'Mbabane', 'Mogadishu', 'Monrovia', 'Nairobi', 'Ndjamena', 'Niamey', 'Nouakchott', 'Ouagadougou', 'Porto-Novo', 'Sao Tome', 'Tripoli', 'Tunis', 'Windhoek'],
['Adak', 'Anchorage', 'Anguilla', 'Antigua', 'Araguaina', 'Argentina/Buenos Aires', 'Argentina/Catamarca', 'Argentina/Cordoba', 'Argentina/Jujuy', 'Argentina/La Rioja', 'Argentina/Mendoza', 'Argentina/Rio Gallegos', 'Argentina/Salta', 'Argentina/San Juan', 'Argentina/San Luis', 'Argentina/Tucuman', 'Argentina/Ushuaia', 'Aruba', 'Asuncion', 'Atikokan', 'Bahia', 'Barbados', 'Belem', 'Belize', 'Blanc-Sablon', 'Boa Vista', 'Bogota', 'Boise', 'Cambridge Bay', 'Campo Grande', 'Cancun', 'Caracas', 'Cayenne', 'Cayman', 'Chicago', 'Chihuahua', 'Costa Rica', 'Cuiaba', 'Curacao', 'Danmarkshavn', 'Dawson', 'Dawson Creek', 'Denver', 'Detroit', 'Dominica', 'Edmonton', 'Eirunepe', 'El Salvador', 'Fortaleza', 'Glace Bay', 'Godthab', 'Goose Bay', 'Grand Turk', 'Grenada', 'Guadeloupe', 'Guatemala', 'Guayaquil', 'Guyana', 'Halifax', 'Havana', 'Hermosillo', 'Indiana/Indianapolis', 'Indiana/Knox', 'Indiana/Marengo', 'Indiana/Petersburg', 'Indiana/Tell City', 'Indiana/Vevay', 'Indiana/Vincennes', 'Indiana/Winamac', 'Inuvik', 'Iqaluit', 'Jamaica', 'Juneau', 'Kentucky/Louisville', 'Kentucky/Monticello', 'La Paz', 'Lima', 'Los Angeles', 'Maceio', 'Managua', 'Manaus', 'Martinique', 'Mazatlan', 'Menominee', 'Merida', 'Mexico City', 'Miquelon', 'Moncton', 'Monterrey', 'Montevideo', 'Montreal', 'Montserrat', 'Nassau', 'New York', 'Nipigon', 'Nome', 'Noronha', 'North Dakota/Center', 'North Dakota/New Salem', 'Panama', 'Pangnirtung', 'Paramaribo', 'Phoenix', 'Port of Spain', 'Port-au-Prince', 'Porto Velho', 'Puerto Rico', 'Rainy River', 'Rankin Inlet', 'Recife', 'Regina', 'Resolute', 'Rio Branco', 'Santarem', 'Santiago', 'Santo Domingo', 'Sao Paulo', 'Scoresbysund', 'St Johns', 'St Kitts', 'St Lucia', 'St Thomas', 'St Vincent', 'Swift Current', 'Tegucigalpa', 'Thule', 'Thunder Bay', 'Tijuana', 'Toronto', 'Tortola', 'Vancouver', 'Whitehorse', 'Winnipeg', 'Yakutat', 'Yellowknife'],
['Casey', 'Davis', 'DumontDUrville', 'Mawson', 'McMurdo', 'Palmer', 'Rothera', 'Syowa', 'Vostok'],
['Aden', 'Almaty', 'Amman', 'Anadyr', 'Aqtau', 'Aqtobe', 'Ashgabat', 'Baghdad', 'Bahrain', 'Baku', 'Bangkok', 'Beirut', 'Bishkek', 'Brunei', 'Choibalsan', 'Chongqing', 'Colombo', 'Damascus', 'Dhaka', 'Dili', 'Dubai', 'Dushanbe', 'Gaza', 'Harbin', 'Ho Chi Minh', 'Hong Kong', 'Hovd', 'Irkutsk', 'Jakarta', 'Jayapura', 'Jerusalem', 'Kabul', 'Kamchatka', 'Karachi', 'Kashgar', 'Kathmandu', 'Kolkata', 'Krasnoyarsk', 'Kuala Lumpur', 'Kuching', 'Kuwait', 'Macau', 'Magadan', 'Makassar', 'Manila', 'Muscat', 'Nicosia', 'Novosibirsk', 'Omsk', 'Oral', 'Phnom Penh', 'Pontianak', 'Pyongyang', 'Qatar', 'Qyzylorda', 'Rangoon', 'Riyadh', 'Sakhalin', 'Samarkand', 'Seoul', 'Shanghai', 'Singapore', 'Taipei', 'Tashkent', 'Tbilisi', 'Tehran', 'Thimphu', 'Tokyo', 'Ulaanbaatar', 'Urumqi', 'Vientiane', 'Vladivostok', 'Yakutsk', 'Yekaterinburg', 'Yerevan'],
['Azores', 'Bermuda', 'Canary', 'Cape Verde', 'Faroe', 'Madeira', 'Reykjavik', 'South Georgia', 'St Helena', 'Stanley'],
['Adelaide', 'Brisbane', 'Broken Hill', 'Currie', 'Darwin', 'Eucla', 'Hobart', 'Lindeman', 'Lord Howe', 'Melbourne', 'Perth', 'Sydney'],
['Amsterdam', 'Andorra', 'Athens', 'Belgrade', 'Berlin', 'Brussels', 'Bucharest', 'Budapest', 'Chisinau', 'Copenhagen', 'Dublin', 'Gibraltar', 'Helsinki', 'Istanbul', 'Kaliningrad', 'Kiev', 'Lisbon', 'London', 'Luxembourg', 'Madrid', 'Malta', 'Minsk', 'Monaco', 'Moscow', 'Oslo', 'Paris', 'Prague', 'Riga', 'Rome', 'Samara', 'Simferopol', 'Sofia', 'Stockholm', 'Tallinn', 'Tirane', 'Uzhgorod', 'Vaduz', 'Vienna', 'Vilnius', 'Volgograd', 'Warsaw', 'Zaporozhye', 'Zurich'],
['Antananarivo', 'Chagos', 'Christmas', 'Cocos', 'Comoro', 'Kerguelen', 'Mahe', 'Maldives', 'Mauritius', 'Mayotte', 'Reunion'],
['Apia', 'Auckland', 'Chatham', 'Easter', 'Efate', 'Enderbury', 'Fakaofo', 'Fiji', 'Funafuti', 'Galapagos', 'Gambier', 'Guadalcanal', 'Guam', 'Honolulu', 'Johnston', 'Kiritimati', 'Kosrae', 'Kwajalein', 'Majuro', 'Marquesas', 'Midway', 'Nauru', 'Niue', 'Norfolk', 'Noumea', 'Pago Pago', 'Palau', 'Pitcairn', 'Ponape', 'Port Moresby', 'Rarotonga', 'Saipan', 'Tahiti', 'Tarawa', 'Tongatapu', 'Truk', 'Wake', 'Wallis'],
['Alaska', 'Arizona', 'Central', 'Eastern', 'Hawaii', 'Mountain', 'Pacific']],
    default_area: 9,
    default_location: 6
};

$(document).ready(function() {
    $('#id_description').markItUp(mySettings);
    $('#id_start_date').datepicker({constrainInput: true, 
       onClose: function () {
         var end = $('#id_end_date');
         if (this.value > end.val())
         {
            end.val(this.value);
         }
       }
       });
    $('#id_end_date').datepicker({constrainInput: true,
       onClose: function () {
         var start = $('#id_start_date');
         if (this.value < start.val())
         {
            start.val(this.value);
         }
       }
       });
    if ($('#id_all_day:checked').length)
    {
       $('#id_start_time').hide();
       $('#id_end_time').hide();
       $('#id_tz_stuff').hide();
    }
    $('#id_all_day').click(function () {
       $('#id_start_time').toggle();
       $('#id_end_time').toggle();
       $('#id_tz_stuff').toggle();
       });

    var tz_area = $('#id_tz_area')[0];
    var tz_loc = $('#id_tz_location')[0];
    tz_area.options.length = 0;
    for (var i = 0; i < gcalTzInfo.areas.length; ++i)
    {
       tz_area.options[i] = new Option(gcalTzInfo.areas[i]);     
    }

    var event_tz = $('#id_time_zone').val();
    if (event_tz == '')
    {
       tz_area.options.selectedIndex = gcalTzInfo.default_area;
    }
    else
    {
       var area_match = event_tz.match(/^(\w+)\/.*$/);
       if (area_match != null)
       {
          var i = gcalTzInfo.areas.indexOf(area_match[1]);
          tz_area.options.selectedIndex = (i != -1) ? i : gcalTzInfo.default_area;
       }
       else
       {
          tz_area.options.selectedIndex = gcalTzInfo.default_area;
       }
    }

    $('#id_tz_area').change(function () {
       tz_loc.options.length = 0;
       var area = tz_area.options.selectedIndex;
       for (var i = 0; i < gcalTzInfo.locations[area].length; ++i)
       {
          tz_loc.options[i] = new Option(gcalTzInfo.locations[area][i]);
       }
    }).change();

    if (event_tz == '')
    {
       tz_loc.options.selectedIndex = gcalTzInfo.default_location;
    }
    else
    {
       var loc_match = event_tz.match(/^[^\/]+\/(.*)$/);
       if (loc_match != null)
       {
          var loc = loc_match[1].replace(/_/g, ' ');
          var i = gcalTzInfo.locations[tz_area.options.selectedIndex].indexOf(loc);
          tz_loc.options.selectedIndex = (i != -1) ? i : gcalTzInfo.default_location;
       }
       else
       {
          tz_loc.options.selectedIndex = gcalTzInfo.default_location;
       }
    }

    $('#id_gcal_event_form').submit(function () {
       var area = $('#id_tz_area').val();
       var loc = $('#id_tz_location').val();
       var tz = area + '/' + loc.replace(/ /g, '_');
       $('#id_time_zone').val(tz);
       return true;
    });
});
