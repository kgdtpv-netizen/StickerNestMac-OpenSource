#!/bin/zsh
set -euo pipefail

root="$(cd "$(dirname "$0")" && pwd)"
app="$root/build/异形贴纸排版.app"
contents="$app/Contents"
macos="$contents/MacOS"
resources="$contents/Resources"
build_dir="$root/.build"
module_cache="$build_dir/ModuleCache"
executable="StickerNestMac"
icon_generator="$build_dir/GenerateIcon"
marketing_version="1.1.244"
build_number="$(date +%Y%m%d%H%M%S)"

rm -rf "$app"
mkdir -p "$macos" "$resources" "$module_cache"

swiftc \
  -O \
  -module-cache-path "$module_cache" \
  -framework AppKit \
  "$root/Tools/GenerateIcon.swift" \
  -o "$icon_generator"

rm -rf "$resources/AppIcon.iconset"
"$icon_generator" "$resources"
if ! /usr/bin/iconutil -c icns "$resources/AppIcon.iconset" -o "$resources/AppIcon.icns"; then
  echo "warning: iconutil failed; continuing without regenerated AppIcon.icns" >&2
fi

# Keep the public bundle allowlisted. Do not copy Resources wholesale: local,
# ignored profiles may exist there and must never be included accidentally.
cp "$root/Tools/analyze_manual_layouts.py" "$resources/analyze_manual_layouts.py"
cp "$root/Tools/auto_nest.py" "$resources/auto_nest.py"

swiftc \
  -O \
  -parse-as-library \
  -target arm64-apple-macosx14.0 \
  -module-cache-path "$module_cache" \
  -framework SwiftUI \
  -framework AppKit \
  -framework Metal \
  -framework UniformTypeIdentifiers \
  "$root"/Sources/*.swift \
  -o "$macos/$executable"

cp "$root/Info.plist" "$contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $marketing_version" "$contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $build_number" "$contents/Info.plist"

xattr -cr "$app"
codesign --force --deep --sign - "$app" >/dev/null

echo "$app"
