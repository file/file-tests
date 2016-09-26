<?php
// This script is setup as Webook endpoint
// configured to notify on each push:
//   https://github.com/file/file/settings/hooks
//
// The script will trigger travis build of file-tests repository passing
// commit=$commit of file repository that triggered the build
//
// References:
// https://developer.github.com/webhooks/
// https://gist.github.com/glensc/fb5b55f0d0abc962f3bfb0777ab5546a

// ruby -rsecurerandom -e 'puts SecureRandom.hex(20)'
define('GITHUB_HOOK_SECRET', '');
// obtained with 'travis login --org; travis token --org'
define('TRAVIS_CI_TOKEN', '');

// repo to trigger build on
define('TRAVIS_REPO', 'file/file-tests');
// and the branch name
define('TRAVIS_REPO_BRANCH', 'master');

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
	$res = UrlUtil::JsonRequest($url, $body, UrlUtil::HTTP_METHOD_POST, $options, $info, 1);

	// handle errors, like request_limit_reached
	if ($res['@type'] == 'error') {
		throw new RuntimeException($res['error_message']);
	}

	return $res;
}

function travis_trigger_build($payload) {
	$diff = $payload['compare'];
	$repo = $payload['repository']['full_name'];
	$commit = $payload['head_commit'];
	error_log("PUSH[$repo]: $diff");

	$branch = substr($payload['ref'], 11);
	$commit_id = substr($commit['id'], 0, 7);
	$commit_message = $commit['message'];

	// use shorter username if available
	if (isset($commit['author']['username'])) {
		$author = "@{$commit['author']['username']}";
	} else {
		$author = $commit['author']['name'];
	}

	// remove newlines, they look better then in travis
	$commit_message = preg_replace("/\s+/", ' ', $commit_message);

	// build message to be displayed in travis. try to be compact
	$message = "$repo $commit_id ($author)$commit_message";

	// as env gets overwritten, need to specifiy everything
	$env = array(
		'global' => array(
			"FILE_URL=git://github.com/file/file.git",
			"repository={$payload['repository']['clone_url']}",
			"commit=$commit_id",
		),
		'matrix' => array(
			"FILE_TESTS_URL=git://github.com/hanzz/file-trunk-tests.git",
			"FILE_TESTS_URL=http://git.fedorahosted.org/git/file-tests.git",
		),
	);

	$request = array(
		'message' => $message,
		'branch' => TRAVIS_REPO_BRANCH,
		'config' => array(
			'env' => $env,
		),
	);

	return travis_request(TRAVIS_REPO, TRAVIS_CI_TOKEN, $request);
}

$payload = get_github_payload(GITHUB_HOOK_SECRET, 1);
$res = travis_trigger_build($payload);
