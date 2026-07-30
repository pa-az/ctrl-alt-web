# Bundled Google Fonts

These are the only font files the app uses. `main.dart` sets
`GoogleFonts.config.allowRuntimeFetching = false`, so `google_fonts` resolves
every `GoogleFonts.x()` call against this folder and never touches
fonts.gstatic.com.

Before this, each family and weight was downloaded the first time a screen
needed it (during the session, not at startup) which showed up as UI lag on
slow or proxied networks.

## What is here

| File | Used by |
| --- | --- |
| `Inter-Regular.ttf` | `GoogleFonts.inter()` default weight, `interTextTheme` |
| `Inter-Medium.ttf` | `GoogleFonts.inter(fontWeight: FontWeight.w500)` |
| `Inter-SemiBold.ttf` | `w600` |
| `Inter-Bold.ttf` | `w700` / `FontWeight.bold` |
| `Inter-ExtraBold.ttf` | `w800` |
| `SpaceGrotesk-SemiBold.ttf` | `GoogleFonts.spaceGrotesk(fontWeight: w600)` |
| `SpaceGrotesk-Bold.ttf` | `w700`, and `w800` (Space Grotesk stops at 700, so the package resolves w800 to the closest available weight) |
| `Audiowide-Regular.ttf` | `GoogleFonts.audiowide()`. Audiowide ships one weight, so `bold` resolves here |
| `Outfit-Bold.ttf` | `GoogleFonts.outfit(fontWeight: bold)` |
| `Caveat-Bold.ttf` | `GoogleFonts.caveat(fontWeight: bold)` |

## Adding a family or weight

The filename is the lookup key, and it is not a free choice. `google_fonts`
builds it as `<ApiFamily>-<WeightName>.ttf`, where `ApiFamily` is the
space-free name in the package's `fontFamily:` literal (`SpaceGrotesk`, not
`Space Grotesk`) and `WeightName` is `Regular` (400), `Medium` (500),
`SemiBold` (600), `Bold` (700), `ExtraBold` (800). A name that does not match
is silently ignored and, with runtime fetching off, the text falls back to the
platform default.

Do not download from fonts.google.com: that now serves variable fonts, which
do not resolve to these static weights. Take the exact file the package would
have fetched instead: find the family's `static TextStyle <name>(` block in
`~/.pub-cache/hosted/pub.dev/google_fonts-*/lib/src/google_fonts_parts/part_<letter>.dart`,
read the sha256 and byte length for the weight you want out of its
`GoogleFontsFile(...)` entry, and download
`https://fonts.gstatic.com/s/a/<sha256>.ttf`. Verify both the hash and the
length before committing; the package checks them too.

Then add the weight to the table above and rebuild.

## Not covered by this

The Flutter engine still fetches its own Roboto default and Noto symbol
fallbacks from Google's CDN for glyphs missing from the fonts above. That is
engine behaviour, not `google_fonts`, and it is not controlled from here.
