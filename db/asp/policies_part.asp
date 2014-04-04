<!DOCTYPE HTML>

<html lang="en">


<!-- extra lang tag was here --><head>
<title>Web Site Policies and Important Links [NEI Tools]</title>
<meta name="description" content="Eye health information and resources for the public and professionals." />
<meta name="keywords" content="eye, health, research, information" />


<meta name="creator" content="National Eye Institute" />
<meta name="language" content="English" />

<meta name="MSSmartTagsPreventParsing" content="TRUE" />
<meta name="viewport" content="initial-scale=1, width=device-width" />

<script language="javascript" type="text/javascript" src="/js/leavesite.js"></script>

<script type="text/javascript" src="/js/textsize.js"></script>
<script type="text/javascript" src="/js/cookies.js"></script>
<script type="text/javascript" src="/js/jquery.js"></script>
<script src="http://sf1-na.readspeaker.com/script/5823/ReadSpeaker.js?pids=embhl" type="text/javascript"></script>



<link rel="stylesheet" type="text/css" href="/css/Reset.css" />
<link rel="stylesheet" type="text/css" href="/css/BaseStyles.css" />
<link rel="stylesheet" type="text/css" href="/css/nei.css" />
<link rel="stylesheet" type="text/css" href="/css/media.css" />

<link rel="stylesheet" type="text/css" href="/css/dropdown_nav5.css" />
<link rel="stylesheet" type="text/css" media="print" href="/css/print.css" />

<script type="text/javascript" async src="//assets.pinterest.com/js/pinit.js"></script>


<!--google analytics start-->
<script type="text/javascript">

  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-1875828-4']);
  _gaq.push(['_setDomainName', '.nei.nih.gov']);
  _gaq.push(['_trackPageview']);

  (function() {
    var ga = document.createElement('script'); 
        ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();



</script>



<script type="text/javascript">
/*Google Analytics Automatic External Link, Downloads, Mailto Tracking- jQuery GA Async Version*/
if (typeof jQuery != 'undefined') {
    jQuery(document).ready(function($) {
        var filetypes = /\.(zip|exe|pdf|doc|xls|ppt|mp3)$/i;
        var baseHref = '';
        if (jQuery('base').attr('href') != undefined)
            baseHref = jQuery('base').attr('href');
        jQuery('a').each(function() {
            var href = jQuery(this).attr('href');
            if (href && (href.match(/^https?\:/i)) && (!href.match(document.domain))) {
                jQuery(this).click(function() {
                    var extLink = href.replace(/^https?\:\/\//i, '');
                    _gaq.push(['_trackEvent', 'External', 'Link Click', extLink]);
                    if (jQuery(this).attr('target') != undefined && jQuery(this).attr('target').toLowerCase() != '_blank') {
                        setTimeout(function() { location.href = href; }, 200);
                        return false;
                    }
                });
            }
             else if (href && href.toLowerCase().match('.*nih.gov.*') && href.toLowerCase().indexOf('nei.nih.gov') == -1) {
jQuery(this).click(function() {
//Exit link tracking for other .nih.gov domains (excludes nei.nih.gov)
var extLink = href.replace(/^https?\:\/\//i, '');
_gaq.push(['_trackEvent', 'External', 'Link Click', extLink]); 
                });
            }
            else if (href && href.match(/^mailto\:/i)) {
                jQuery(this).click(function() {
                    var mailLink = href.replace(/^mailto\:/i, '');
                    _gaq.push(['_trackEvent', 'Email', 'mailto', mailLink]);
                });
            }
            else if (href && href.match(filetypes)) {
                jQuery(this).click(function() {
                    var extension = (/[.]/.exec(href)) ? /[^.]+$/.exec(href) : undefined;
                    var filePath = href;
                    _gaq.push(['_trackEvent', 'Download',extension+ ' Click', filePath]);
                    i