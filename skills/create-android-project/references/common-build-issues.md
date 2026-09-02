# Common Build Issues and Solutions

This document describes build errors and warnings that may occur when scaffolding
or building generated Android projects, and how the power handles them.

## Launcher Icon Issues

### Error: `<adaptive-icon> elements require a sdk version of at least 26`

**Cause:** Adaptive icons (`<adaptive-icon>`) were introduced in Android API 26
(Android 8.0). If adaptive icon XML files are placed in `mipmap-anydpi/` without
the `-v26` qualifier, they apply to all API levels, causing a build failure when
`minSdk` is below 26.

**Solution:** The power creates launcher icons in two locations:
1. **Adaptive icons** in `app/src/main/res/mipmap-anydpi-v26/` (API 26+)
   - `ic_launcher.xml` with `<adaptive-icon>` element
   - `ic_launcher_round.xml` with `<adaptive-icon>` element

2. **Fallback icons** in `app/src/main/res/mipmap-anydpi/` (API 24-25)
   - `ic_launcher.xml` as plain vector drawable
   - `ic_launcher_round.xml` as plain vector drawable

**CRITICAL:** NEVER place `<adaptive-icon>` elements in `mipmap-anydpi/` without
the `-v26` qualifier. Always use `mipmap-anydpi-v26/` for adaptive icons.

**Verification:**
```bash
# Check for incorrectly placed adaptive icons
grep -r "<adaptive-icon>" app/src/main/res/mipmap-anydpi/
# Should return no results

# Verify adaptive icons are in v26 directory
ls app/src/main/res/mipmap-anydpi-v26/
# Should show ic_launcher.xml and ic_launcher_round.xml
```

### Structure Overview

```
app/src/main/res/
├── values/
│   └── ic_launcher_background.xml          # Color resource
├── drawable/
│   └── ic_launcher_foreground.xml          # Vector foreground layer
├── mipmap-anydpi-v26/                      # API 26+ only
│   ├── ic_launcher.xml                     # <adaptive-icon> for square
│   └── ic_launcher_round.xml               # <adaptive-icon> for round
└── mipmap-anydpi/                          # API 24-25 fallback
    ├── ic_launcher.xml                     # <vector> fallback
    └── ic_launcher_round.xml               # <vector> fallback
```

## Build Warnings (Non-Blocking)

These warnings are expected and do not prevent the build from succeeding. They
indicate areas for future improvement but are not errors.

### Warning: "We recommend using a newer Android Gradle plugin to use compileSdk = 35"

**Cause:** The project uses a tested, stable combination of AGP 8.2.2 with
compileSdk 34. Google recommends updating AGP when using newer SDK versions.

**Impact:** None. The build succeeds. The warning is informational.

**When to act:** When the power's dependency versions are updated to include
a newer AGP version that supports compileSdk 35+.

**User action:** Users can safely ignore this warning or update AGP and compileSdk
in `gradle/libs.versions.toml` after verifying compatibility with the Kotlin
version (see Kotlin ↔ Compose Compiler compatibility table).

### Warning: "'capitalize(): String' is deprecated. Use replaceFirstChar instead"

**Cause:** Kotlin 1.5+ deprecated `String.capitalize()` in favor of
`replaceFirstChar { it.titlecase() }` for better Unicode support.

**Location:** May appear in generated Compose UI code if template uses old API.

**Impact:** None. The deprecated function still works. The warning prompts
modernization.

**Fix:** Replace in generated code:
```kotlin
// Old (deprecated)
val text = name.capitalize()

// New
val text = name.replaceFirstChar { it.uppercase() }
```

**Power action:** Update templates to use `replaceFirstChar` instead of `capitalize`.

### Warning: "'setter for statusBarColor: Int' is deprecated. Deprecated in Java"

**Cause:** Android 11 (API 30) introduced edge-to-edge design. Setting
`statusBarColor` directly is deprecated in favor of `WindowCompat.setDecorFitsSystemWindows()`.

**Location:** May appear in `Theme.kt` or `MainActivity.kt` if the template
configures system UI colors.

**Impact:** None. The deprecated API still works. Modern Android handles system
bars gracefully.

**Fix:** Remove manual status bar color setting and use Material 3 theming:
```kotlin
// Old (deprecated)
window.statusBarColor = Color.Transparent

// New (edge-to-edge)
WindowCompat.setDecorFitsSystemWindows(window, false)
```

**Power action:** Consider removing status bar color configuration from templates,
or use the modern edge-to-edge approach.

## Resource Linking Failures

### Error: "Android resource linking failed"

**General cause:** AAPT2 (Android Asset Packaging Tool) could not link resources.
Common reasons:
1. Adaptive icons in wrong directory (see above)
2. Missing resource references (e.g., `@drawable/foo` doesn't exist)
3. Invalid XML syntax in resource files
4. Resource IDs conflict between modules

**Debugging:**
```bash
# Run build with stacktrace for details
./gradlew :app:assembleDebug --stacktrace

# Check resource files for syntax errors
find app/src/main/res -name "*.xml" -exec xmllint --noout {} \;
```

**Prevention in scaffolding:**
- Verify all `@drawable/*`, `@color/*`, `@string/*` references exist
- Ensure XML files are well-formed
- Place resources in correct directories with proper qualifiers

## Dependency Resolution

### Error: "Could not resolve all dependencies"

**Causes:**
1. Version catalog entry missing or malformed
2. Repository not declared (e.g., Google Maven)
3. Network issues preventing dependency download
4. Version conflict between dependencies

**Solution:**
- Verify `gradle/libs.versions.toml` is complete
- Check `settings.gradle.kts` declares required repositories
- Run with `--refresh-dependencies` to clear cache
- Review dependency tree: `./gradlew :app:dependencies`

## Module Configuration (Clean Architecture)

### Error: "Project with path ':domain' could not be found"

**Cause:** Module referenced in `dependencies {}` but not included in
`settings.gradle.kts`.

**Fix in scaffolding:** Ensure every module directory has a corresponding
`include(":module:path")` in `settings.gradle.kts`.

**Verification:**
```bash
# List all build.gradle.kts files
find . -name "build.gradle.kts" -not -path "./build-logic/*"

# Check settings.gradle.kts includes each one
grep "include" settings.gradle.kts
```

### Error: "Cannot access 'androidx.compose.runtime.Composable'"

**Cause:** `domain` module (pure Kotlin) depends on Android or Compose libraries.

**Fix:** Remove Android dependencies from `core/domain/build.gradle.kts`. Domain
must use `kotlin("jvm")` plugin, not Android Library plugin.

**Prevention:** SKILL.md Step 7 verification checks that domain module has no
`android.` or `androidx.` imports.

## SDK Configuration

### Error: "SDK location not found"

**Cause:** Android SDK path not configured. Gradle needs to know where the
Android SDK is installed.

**Solution (user environment):**
1. Set environment variable: `export ANDROID_HOME=/path/to/android/sdk`
2. OR create `local.properties` with: `sdk.dir=/path/to/android/sdk`

**Power responsibility:** The power does NOT create `local.properties` because
it is machine-specific. SKILL.md Step 7 mentions this as an environment issue,
not a scaffolding bug.

## Verification Checklist

After scaffolding, verify:

- [ ] No `{{TOKEN}}` remains in any file
- [ ] Adaptive icons are in `mipmap-anydpi-v26/`, not `mipmap-anydpi/`
- [ ] Fallback icons are in `mipmap-anydpi/` without `<adaptive-icon>` elements
- [ ] All modules in `include()` statements exist as directories
- [ ] Version catalog entries are well-formed (no unclosed quotes, valid syntax)
- [ ] Package declarations match directory structure
- [ ] Domain module (if Clean) has no Android imports
- [ ] Build succeeds: `./gradlew :app:assembleDebug` exits with status 0
- [ ] Warnings are documented and expected (AGP version, deprecations)

## Summary

| Issue | Severity | Action |
|---|---|---|
| Adaptive icons in `mipmap-anydpi/` | **Error** | Move to `mipmap-anydpi-v26/` |
| AGP version recommendation | Warning | Ignore or update later |
| `capitalize()` deprecation | Warning | Fix in generated code if desired |
| `statusBarColor` deprecation | Warning | Fix in generated code if desired |
| SDK location not found | **Error** | User environment issue |
| Missing module in settings | **Error** | Scaffolding bug, add `include()` |

**Build success criteria:** `./gradlew :app:assembleDebug` exits with status 0,
regardless of non-blocking warnings.
