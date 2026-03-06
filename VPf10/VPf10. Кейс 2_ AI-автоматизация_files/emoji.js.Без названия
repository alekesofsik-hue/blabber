setEmojiCarret = function(node)
{
	window.setTimeout(function() {
		var sel, range;
		if (window.getSelection && document.createRange) {
			range = document.createRange();
			range.selectNodeContents(node);
			range.collapse(false);
			sel = window.getSelection();
			sel.removeAllRanges();
			sel.addRange(range);
		}
	}, 0);
}

var scriptEls = document.getElementsByTagName( 'script' );
var thisScriptEl = scriptEls[scriptEls.length - 1];
var scriptPath = thisScriptEl.src;
var scriptFolder = scriptPath.substr(0, scriptPath.lastIndexOf( '/' )+1 );

$.emojiarea.path = scriptFolder + 'packs/basic';
$.emojiarea.icons = {
	':fire:': 'fire.png',
	':smile:': 'smile.png',
	':angry:': 'angry.png',
	':flushed:': 'flushed.png',
	':blush:': 'blush.png',
	':laughing:': 'laughing.png',
	':smiley:': 'smiley.png',
	':smirk:': 'smirk.png',
	':heart_eyes:': 'heart_eyes.png',
	':kissing_heart:': 'kissing_heart.png',
	':kissing_closed_eyes:': 'kissing_closed_eyes.png',
	':bowtie:': 'bowtie.png',
	':relieved:': 'relieved.png',
	':satisfied:': 'satisfied.png',
	':grin:': 'grin.png',
	':wink:': 'wink.png',
	':relaxed:': 'relaxed.png',
	':stuck_out_tongue_winking_eye:': 'stuck_out_tongue_winking_eye.png',
	':stuck_out_tongue_closed_eyes:': 'stuck_out_tongue_closed_eyes.png',
	':grinning:': 'grinning.png',
	':kissing:': 'kissing.png',
	':kissing_smiling_eyes:': 'kissing_smiling_eyes.png',
	':stuck_out_tongue:': 'stuck_out_tongue.png',
	':sleeping:': 'sleeping.png',
	':worried:': 'worried.png',
	':frowning:': 'frowning.png',
	':anguished:': 'anguished.png',
	':open_mouth:': 'open_mouth.png',
	':grimacing:': 'grimacing.png',
	':confused:': 'confused.png',
	':hushed:': 'hushed.png',
	':expressionless:': 'expressionless.png',
	':unamused:': 'unamused.png',
	':sweat_smile:': 'sweat_smile.png',
	':sweat:': 'sweat.png',
	':disappointed_relieved:': 'disappointed_relieved.png',
	':weary:': 'weary.png',
	':pensive:': 'pensive.png',
	':disappointed:': 'disappointed.png',
	':confounded:': 'confounded.png',
	':fearful:': 'fearful.png',
	':cold_sweat:': 'cold_sweat.png',
	':persevere:': 'persevere.png',
	':cry:': 'cry.png',
	':sob:': 'sob.png',
	':joy:': 'joy.png',
	':astonished:': 'astonished.png',
	':scream:': 'scream.png',
	':neckbeard:': 'neckbeard.png',
	':tired_face:': 'tired_face.png',
	':rage:': 'rage.png',
	':triumph:': 'triumph.png',
	':sleepy:': 'sleepy.png',
	':yum:': 'yum.png',
	':mask:': 'mask.png',
	':sunglasses:': 'sunglasses.png',
	':dizzy_face:': 'dizzy_face.png',
	':imp:': 'imp.png',
	':smiling_imp:': 'smiling_imp.png',
	':neutral_face:': 'neutral_face.png',
	':no_mouth:': 'no_mouth.png',
	':innocent:': 'innocent.png',
	':alien:': 'alien.png',
	':yellow_heart:': 'yellow_heart.png',
	':blue_heart:': 'blue_heart.png',
	':purple_heart:': 'purple_heart.png',
	':heart:': 'heart.png',
	':green_heart:': 'green_heart.png',
	':broken_heart:': 'broken_heart.png',
	':heartbeat:': 'heartbeat.png',
	':heartpulse:': 'heartpulse.png',
	':two_hearts:': 'two_hearts.png',
	':revolving_hearts:': 'revolving_hearts.png',
	':cupid:': 'cupid.png',
	':sparkling_heart:': 'sparkling_heart.png',
	':sparkles:': 'sparkles.png',
	':star:': 'star.png',
	':boom:': 'boom.png',
	':exclamation:': 'exclamation.png',
	':question:': 'question.png',
	':zzz:': 'zzz.png',
	':sweat_drops:': 'sweat_drops.png',
	':musical_note:': 'musical_note.png',
	':thumbsup:': 'thumbsup.png',
	':thumbsdown:': 'thumbsdown.png',
	':ok_hand:': 'ok_hand.png',
	':punch:': 'punch.png',
	':v:': 'v.png',
	':wave:': 'wave.png',
	':hand:': 'hand.png',
	':point_up:': 'point_up.png',
	':point_down:': 'point_down.png',
	':point_left:': 'point_left.png',
	':point_right:': 'point_right.png',
	':clap:': 'clap.png',
	':muscle:': 'muscle.png',
	':metal:': 'metal.png',
	':running:': 'running.png',
	':girl:': 'girl.png',
	':boy:': 'boy.png',
	':woman:': 'woman.png',
	':man:': 'man.png',
	':baby:': 'baby.png',
	':smiley_cat:': 'smiley_cat.png',
	':scream_cat:': 'scream_cat.png',
	':see_no_evil:': 'see_no_evil.png',
	':hear_no_evil:': 'hear_no_evil.png',
	':speak_no_evil:': 'speak_no_evil.png',
	':kiss:': 'kiss.png',
	':eyes:': 'eyes.png',
	':love_letter:': 'love_letter.png',
	':speech_balloon:': 'speech_balloon.png',
	':thought_balloon:': 'thought_balloon.png',
	':sunny:': 'sunny.png',
	':cloud:': 'cloud.png',
	':snowflake:': 'snowflake.png',
	':zap:': 'zap.png',
	':cat:': 'cat.png',
	':dog:': 'dog.png',
	':rabbit:': 'rabbit.png',
	':monkey_face:': 'monkey_face.png',
	':bouquet:': 'bouquet.png',
	':tulip:': 'tulip.png',
	':four_leaf_clover:': 'four_leaf_clover.png',
	':cactus:': 'cactus.png',
	':rose:': 'rose.png',
	':sunflower:': 'sunflower.png',
	':globe_with_meridians:': 'globe_with_meridians.png',
	':crescent_moon:': 'crescent_moon.png',
	':earth_asia:': 'earth_asia.png',
	':gift_heart:': 'gift_heart.png',
	':bell:': 'bell.png',
	':christmas_tree:': 'christmas_tree.png',
	':gift:': 'gift.png',
	':balloon:': 'balloon.png',
	':computer:': 'computer.png',
	':tv:': 'tv.png',
	':telephone_receiver:': 'telephone_receiver.png',
	':speaker:': 'speaker.png',
	':hourglass:': 'hourglass.png',
	':key:': 'key.png',
	':mag:': 'mag.png',
	':birthday:': 'birthday.png',
	':house:': 'house.png',
	':rocket:': 'rocket.png',
	':airplane:': 'airplane.png',
	':car:': 'car.png',
	':ru:': 'ru.png',
	':de:': 'de.png',
	':cn:': 'cn.png',
	':us:': 'us.png',
	':fr:': 'fr.png',
	':it:': 'it.png',
	':es:': 'es.png',
	':jp:': 'jp.png',
	':gb:': 'gb.png'
};

$.emojiarea.entities = {
	':fire:': '&#128293',
	':joy:': '&#128514;',
	':heart:': '&#10084;&#65039;',
	':heart_eyes:': '&#128525;',
	':sob:': '&#128557;',
	':blush:': '&#128522;',
	':unamused:': '&#128530;',
	':kissing_heart:': '&#128536;',
	':two_hearts:': '&#128149;',
	':weary:': '&#128553;',
	':ok_hand:': '&#128076;',
	':pensive:': '&#128532;',
	':smirk:': '&#128527;',
	':grin:': '&#128513;',
	':wink:': '&#128521;',
	':thumbsup:': '&#128077;',
	':metal:': '&#129304;',
	':punch:': '&#128074;',
	':hand:': '&#9995;',
	':neckbeard:': '&#129492;',
	':bowtie:': '&#128084;',
	':satisfied:': '&#128518;',
	':relaxed:': '&#128522;',
	':relieved:': '&#128524;',
	':flushed:': '&#128563;',
	':see_no_evil:': '&#128584;',
	':cry:': '&#128546;',
	':sunglasses:': '&#128526;',
	':v:': '&#9996;',
	':eyes:': '&#128064;',
	':sweat_smile:': '&#128517;',
	':sparkles:': '&#10024;',
	':sleeping:': '&#128564;',
	':smile:': '&#128516;',
	':purple_heart:': '&#128156;',
	':broken_heart:': '&#128148;',
	':expressionless:': '&#128529;',
	':sparkling_heart:': '&#128150;',
	':blue_heart:': '&#128153;',
	':confused:': '&#128533;',
	':stuck_out_tongue_winking_eye:': '&#128540;',
	':disappointed:': '&#128542;',
	':yum:': '&#128523;',
	':neutral_face:': '&#128528;',
	':sleepy:': '&#128554;',
	':clap:': '&#128079;',
	':cupid:': '&#128152;',
	':heartpulse:': '&#128151;',
	':revolving_hearts:': '&#128158;',
	':speak_no_evil:': '&#128586;',
	':kiss:': '&#128139;',
	':point_right:': '&#128073;',
	':scream:': '&#128561;',
	':rage:': '&#128545;',
	':smiley:': '&#128515;',
	':tired_face:': '&#128555;',
	':rose:': '&#127801;',
	':stuck_out_tongue_closed_eyes:': '&#128541;',
	':muscle:': '&#128170;',
	':sunny:': '&#9728;&#65039;',
	':yellow_heart:': '&#128155;',
	':triumph:': '&#128548;',
	':laughing:': '&#128518;',
	':sweat:': '&#128531;',
	':point_left:': '&#128072;',
	':grinning:': '&#128512;',
	':mask:': '&#128567;',
	':green_heart:': '&#128154;',
	':wave:': '&#128075;',
	':persevere:': '&#128547;',
	':heartbeat:': '&#128147;',
	':kissing_closed_eyes:': '&#128538;',
	':stuck_out_tongue:': '&#128539;',
	':disappointed_relieved:': '&#128549;',
	':innocent:': '&#128519;',
	':confounded:': '&#128534;',
	':angry:': '&#128544;',
	':grimacing:': '&#128556;',
	':thumbsdown:': '&#128078;',
	':musical_note:': '&#127925;',
	':no_mouth:': '&#128566;',
	':point_down:': '&#128071;',
	':boom:': '&#128165;',
	':thought_balloon:': '&#128173;',
	':cold_sweat:': '&#128560;',
	':sweat_drops:': '&#128166;',
	':zzz:': '&#128164;',
	':airplane:': '&#9992;',
	':balloon:': '&#127880;',
	':star:': '&#11088;',
	':worried:': '&#128543;',
	':fearful:': '&#128552;',
	':four_leaf_clover:': '&#127808;',
	':alien:': '&#128125;',
	':cloud:': '&#9729;',
	':exclamation:': '&#10071;',
	':snowflake:': '&#10052;',
	':point_up:': '&#9757;',
	':kissing_smiling_eyes:': '&#128537;',
	':crescent_moon:': '&#127769;',
	':gift_heart:': '&#128157;',
	':gift:': '&#127873;',
	':anguished:': '&#128551;',
	':zap:': '&#9889;',
	':running:': '&#127939;',
	':sunflower:': '&#127803;',
	':bouquet:': '&#128144;',
	':dog:': '&#128054;',
	':tulip:': '&#127799;',
	':birthday:': '&#127874;',
	':cat:': '&#128049;',
	':dizzy_face:': '&#128565;',
	':open_mouth:': '&#128558;',
	':hushed:': '&#128559;',
	':christmas_tree:': '&#127876;',
	':astonished:': '&#128562;',
	':hear_no_evil:': '&#128585;',
	':cactus:': '&#127797;',
	':love_letter:': '&#128140;',
	':us:': '&#127482;&#127480;',
	':frowning:': '&#128550;',
	':rocket:': '&#128640;',
	':smiling_imp:': '&#128520;',
	':imp:': '&#128127;',
	':earth_asia:': '&#127759;',
	':speech_balloon:': '&#128172;',
	':scream_cat:': '&#128576;',
	':baby:': '&#128118;',
	':rabbit:': '&#128048;',
	':kissing:': '&#128535;',
	':tv:': '&#128250;',
	':smiley_cat:': '&#128570;',
	':man:': '&#128104;',
	':girl:': '&#128103;',
	':fr:': '&#127467;&#127479;',
	':woman:': '&#128105;',
	':key:': '&#128273;',
	':telephone_receiver:': '&#128222;',
	':computer:': '&#128187;',
	':question:': '&#10067;',
	':boy:': '&#128102;',
	':it:': '&#127470;&#127481;',
	':gb:': '&#127468;&#127463;',
	':house:': '&#127968;',
	':monkey_face:': '&#128053;',
	':car:': '&#128663;',
	':jp:': '&#127471;&#127477;',
	':bell:': '&#128276;',
	':globe_with_meridians:': '&#127760;',
	':hourglass:': '&#8987;',
	':ru:': '&#127479;&#127482;',
	':mag:': '&#128269;',
	':cn:': '&#127464;&#127475;',
	':speaker:': '&#128264;',
	':de:': '&#127465;&#127466;',
	':es:': '&#127466;&#127480;'
};

//$('.emoji-button').on('click', function() {
//    if ($(this).siblings('.emoji-wysiwyg-editor').length == 0) {
//        $(this).siblings('textarea.emoji-area').emojiarea({
//            button: '.emoji-button',
//            //buttonPosition: 'before'
//        });
//    }
//});

//$('.emoji-text').emoji();

//$('.emoji-textarea').emojiButton();

//eachAndRunOneTimeOnElement(
//	$('.emoji-text'),
//	'emoji-text-handler',
//	function($el) {
//		$el.emoji();
//	}
//);
//eachAndRunOneTimeOnElement(
//	$('.emoji-textarea'),
//	'emoji-btn-handler',
//	function($el) {
//		$el.emojiButton();
//	}
//);

(function () {
	// весь хелпер вынужденная, мера, потому что был глобальный bing emoji по селекторам и пытаюсь как то это исправить
	var EmojiHelper = {};
	EmojiHelper.initEmojies = function($el) {
		window.eachAndRunOneTimeOnElement(
			$el.find('.emoji-text'),
			'emoji-text-handler',
			function ($el) {
				$el.emoji();
				return $el;
			}
		);
	};
	EmojiHelper.initEmojiTextAreas = function ($el) {
		window.eachAndRunOneTimeOnElement(
			$el.find('.emoji-textarea'),
			'emoji-textarea-handler',
			function ($el) {
				$el.emojiButton();
				// todo треш, зависит от предыдущего вызова неявно, плюс несовсем понятно, как оно раньше работало
				$el.parents('.emoji-container').find('.emoji-button').click(function(e){
					var $this = $(this);
					//var $parent = $($this.parents('.new-comment').get(0));
					var $textarea = $this.siblings('textarea.emoji-textarea');
					if (!$el.data('sibling')) {
						$el.data('sibling', 1);
						$textarea.emojiarea({
							button: '.emoji-button'
						});
						setEmojiCarret($textarea.siblings('.emoji-wysiwyg-editor').get(0));
					}
				});
				return $el;
			}
		);
	};
	window.GcEmojiHelper = EmojiHelper;
})();
