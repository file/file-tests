<?php
// https://developer.github.com/webhooks/
// https://gist.github.com/glensc/fb5b55f0d0abc962f3bfb0777ab5546a

// ruby -rsecurerandom -e 'puts SecureRandom.hex(20)'
define('GITHUB_HOOK_SECRET', '');
// obtained with 'travis login --org; travis token --org'
define('TRAVIS_CI_TOKEN', '');

// repo to trigger build on
define('TRAVIS_REPO', 'glensc/file-tests');
// and the branch name
define('TRAVIS_REPO_BRANCH', 'new-logic');

set_exception_handler(function($e) {
	header('HTTP/1.1 500 Internal Server Error');
	error_log(basename(__FILE__, '.php') . ': '. $e->getMessage());
	die("Error on line {$e->getLine()}: " . htmlspecialchars($e->getMessage()));
});

// https://developer.github.com/v3/activity/events/types/#pushevent
// X-Hub-Signature: sha1=ffd1a5f14b30eaaaca1e84499c372743302bc47d
function get_github_payload($secret, $assoc = false) {
	if (!isset($_SERVER['HTTP_X_GITHUB_EVENT'])) {
		throw new InvalidArgumentException('No event');
	}
	$eventType = $_SERVER['HTTP_X_GITHUB_EVENT'];
	if ($eventType != 'push') {
		throw new InvalidArgumentException("Invalid Event: $eventType");
	}

	if (!isset($_SERVER['HTTP_X_HUB_SIGNATURE'])) {
		throw new InvalidArgumentException("HTTP header 'X-Hub-Signature' is missing");
	}

	if (!extension_loaded('hash')) {
		throw new InvalidArgumentException("Missing 'hash' extension to check the secret code validity.");
	}

	# https://developer.github.com/v3/repos/hooks/#create-a-hook
	# The value of this header is computed as the HMAC hex digest of the body, using the secret as the key.
	list($algo, $hash) = explode('=', $_SERVER['HTTP_X_HUB_SIGNATURE'], 2);
	if (!in_array($algo, hash_algos(), true)) {
		throw new Exception("Hash algorithm '$algo' is not supported.");
	}

	$rawPost = file_get_contents('php://input');
	if ($hash !== hash_hmac($algo, $rawPost, $secret)) {
		throw new InvalidArgumentException("Hook secret ($algo) does not match");
	}

	if (isset($_POST['payload'])) {
		// for urlencoded data
		$payload = $_POST['payload'];
	} else {
		// for application/json
		$payload = $rawPost;
	}

	return json_decode($payload, $assoc);
}

function travis_request($repo, $token, $request) {
	require_once 'UrlUtil.php';
	$headers = array(
	  "Content-Type: application/json",
	  "Accept: application/json",
	  "Travis-API-Version: 3",
	  "Authorization: token $token",
	);
	$url = sprintf("https://api.travis-ci.org/repo/%s/requests", urlencode($repo));
	$body = json_encode(array('request' => $request));

	$params = array();
	$options = array(
		CURLOPT_HTTPHEADER => $headers,
	);
	return UrlUtil::JsonRequest($url, $body, UrlUtil::HTTP_METHOD_POST, $options);
}

function travis_trigger_build($payload) {
	$diff = $payload['compare'];
	$repo = $payload['repository']['full_name'];
	$commit = $payload['head_commit'];
	error_log("PUSH[$repo]: $diff");

	$branch = substr($payload['ref'], 11);
	$commit_id = substr($commit['id'], 0, 7);
	$commit_message = $commit['message'];
	$author = $commit['author']['name'];

	$message = "$author($repo:$commit_id): $commit_message";
	$request = array(
		'message' => $message,
		'branch' => TRAVIS_REPO_BRANCH,
		'config' => array(
			'env' => array(
				'global' => array(
					"repository={$payload['repository']['clone_url']}",
					"commit=$commit_id",
				),
			),
		),
	);

	return travis_request(TRAVIS_REPO, TRAVIS_CI_TOKEN, $request);
}

$payload = get_github_payload(GITHUB_HOOK_SECRET, 1);
$res = travis_trigger_build($payload);
