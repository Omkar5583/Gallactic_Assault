[app]
title = Galactic Assault
package.name = galacticassault
package.domain = com.spaceshooter
source.dir = .
source.include_exts = py,json
version = 1.0
requirements = python3==3.10.12,kivy==2.3.0,pyjnius==1.5.0,hostpython3==3.10.12,pygame
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True
android.allow_backup = True
android.release_artifact = apk
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
