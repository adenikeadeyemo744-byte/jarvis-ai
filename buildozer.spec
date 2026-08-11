[app]
title = Jarvis
package.name = jarvis
package.domain = org.deathstorm
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,requests,edge-tts,pyjnius
orientation = portrait
fullscreen = 0

android.permissions = RECORD_AUDIO,INTERNET,CALL_PHONE,CAMERA,ACCESS_FINE_LOCATION,ACCESS_NETWORK_STATE,VIBRATE,FLASHLIGHT

android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2