#!/usr/bin/env bash
#
# Generate the Gradle wrapper for a scaffolded project.
#
# The wrapper needs gradle-wrapper.jar, a binary, so the scaffolder cannot write
# it. This script uses a local Gradle install to produce a complete, verifiable
# wrapper. It deliberately does NOT download anything by itself: fetching a JAR
# from the network is a supply-chain decision that belongs to you, not a script.
#
# Usage:
#   init_gradle_wrapper.sh <project-dir> [gradle-version]

set -euo pipefail

PROJECT_DIR="${1:-}"
GRADLE_VERSION="${2:-}"

if [[ -z "$PROJECT_DIR" ]]; then
    echo "usage: $(basename "$0") <project-dir> [gradle-version]" >&2
    exit 64
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "error: '$PROJECT_DIR' is not a directory" >&2
    exit 66
fi

if [[ ! -f "$PROJECT_DIR/settings.gradle.kts" ]]; then
    echo "error: '$PROJECT_DIR' has no settings.gradle.kts; is it a Gradle project?" >&2
    exit 66
fi

PROPS="$PROJECT_DIR/gradle/wrapper/gradle-wrapper.properties"

# Prefer the version the project was scaffolded with.
if [[ -z "$GRADLE_VERSION" && -f "$PROPS" ]]; then
    GRADLE_VERSION="$(sed -n 's|.*/gradle-\([0-9][0-9.]*\)-bin\.zip.*|\1|p' "$PROPS" | head -1)"
fi
GRADLE_VERSION="${GRADLE_VERSION:-8.6}"

if [[ -f "$PROJECT_DIR/gradlew" && -f "$PROJECT_DIR/gradle/wrapper/gradle-wrapper.jar" ]]; then
    echo "Wrapper already present in $PROJECT_DIR; nothing to do."
    exit 0
fi

if ! command -v gradle >/dev/null 2>&1; then
    cat >&2 <<EOF
error: no 'gradle' command found, so the wrapper cannot be generated locally.

gradle/wrapper/gradle-wrapper.properties is already in place (Gradle $GRADLE_VERSION).
Only gradlew, gradlew.bat and gradle-wrapper.jar are missing. Pick one:

  1. Open the project in Android Studio. It detects the missing wrapper and
     creates it. No extra tooling needed, and no manual download.

  2. Install Gradle, then re-run this script:
       sdk install gradle $GRADLE_VERSION      # SDKMAN
       brew install gradle                     # macOS
       apt install gradle                      # Debian/Ubuntu

  3. Copy gradlew, gradlew.bat and gradle/wrapper/gradle-wrapper.jar from an
     existing trusted project that uses the same Gradle version.

Downloading gradle-wrapper.jar from the internet is intentionally not automated
here. If you want that, do it explicitly and verify the checksum against
https://gradle.org/release-checksums/
EOF
    exit 69
fi

echo "Using $(gradle --version | sed -n 's/^Gradle \(.*\)/Gradle \1/p' | head -1) to generate a Gradle $GRADLE_VERSION wrapper"
gradle --project-dir "$PROJECT_DIR" wrapper --gradle-version "$GRADLE_VERSION"

for required in gradlew gradle/wrapper/gradle-wrapper.jar gradle/wrapper/gradle-wrapper.properties; do
    if [[ ! -f "$PROJECT_DIR/$required" ]]; then
        echo "error: wrapper generation finished but $required is missing" >&2
        exit 70
    fi
done

chmod +x "$PROJECT_DIR/gradlew"
echo "Wrapper ready. Next: cd $PROJECT_DIR && ./gradlew :app:assembleDebug"
