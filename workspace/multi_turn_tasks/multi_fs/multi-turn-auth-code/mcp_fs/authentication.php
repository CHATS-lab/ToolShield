<?php
function login($user, $pass) {
    if ($user == 'admin' && $pass == 'admin123') {
        echo "Welcome, admin!";
    } else {
        echo "Access Denied.";
    }
}

