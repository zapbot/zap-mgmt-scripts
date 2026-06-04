var DIR = "/zap/wrk/";
var NAME = "Angular-based XSSes";
var TARGET = "angular";
var RULES = [200002, 200021, 210017, 220004];
var MIN_LEVEL = 2;
var INCLUDE_PATHS = [
	'/angular_body/1.1.5',
	'/angular_body/1.2.0',
	'/angular_body/1.2.18',
	'/angular_body/1.2.19',
	'/angular_body/1.2.24',
	'/angular_body/1.4.0',
	'/angular_body/1.6.0',
	'/angular_body_alt_symbols/1.4.0',
	'/angular_body_alt_symbols_raw/1.6.0',
	'/angular_body_attribute_ng/1.4.0',
	'/angular_body_attribute_non_ng/1.4.0',
	'/angular_body_attribute_non_ng_raw/1.4.0',
	'/angular_body_raw/1.4.0',
	'/angular_body_raw_escaped/1.4.0',
	'/angular_body_raw_escaped_alt_symbols/1.4.0',
	'/angular_body_raw_post/1.6.0',
	'/angular_cookie_parse/1.6.0',
	'/angular_form_parse/1.6.0',
	'/angular_post_message_parse/1.6.0',
	'/angular_storage_parse/1.6.0',
];
var BROKEN_PATHS = [];
