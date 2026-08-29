# {{APP_NAME}}

Scaffolded by the **Android Project - Initial Setup** Kiro power.
Architecture: **MVVM, single module**.

## Structure

```
app/src/main/kotlin/{{PKG_PATH}}/
├── model/                 Domain models (plain Kotlin data classes)
├── data/
{{OPTIONAL_DATA_DIRS}}│   └── repository/        Repository interface + implementation
├── di/                    Hilt modules
├── common/                Injected dispatcher qualifiers
└── ui/
    ├── theme/             Colour scheme, typography, {{APP_CLASS}}Theme
    ├── components/        Reusable composables
{{FEATURE_TREE_LINE}}    └── navigation/        Routes and NavHost
```

## How data flows

```
{{FEATURE_CLASS}}Screen  ->  {{FEATURE_CLASS}}ViewModel  ->  ItemRepository  ->  DAO / API
   (state in,              (exposes StateFlow,        (source of truth
    actions out)            owns the mapping)          decisions)
```

The ViewModel talks to the repository directly. There is no use-case layer, and
for an app this size that is the point: fewer indirections to read through.

## When to move to Clean Architecture

Consider the `clean-mvvm` layout instead once any of these is true:

- more than roughly 5 to 8 screens
- more than one or two developers touching the code
- build times becoming noticeable
- business rules that need reuse across screens, or unit tests that do not want
  to know about Android

Re-scaffolding is not required: extract a `domain` module with models, repository
interfaces and use cases, then move implementations into a `data` module.

## Build

```bash
./gradlew :app:assembleDebug     # debug APK
./gradlew test                   # unit tests
./gradlew build                  # everything, including lint and release
```

If `./gradlew` is missing, generate the wrapper first:

```bash
gradle wrapper --gradle-version {{GRADLE_VERSION}}
```

Opening the project in Android Studio also creates the wrapper.

## Before you ship

- Replace the placeholder launcher icons in `app/src/main/res/mipmap-*`
  (Android Studio: right-click `res` > New > Image Asset).
- Set your brand colours in `ui/theme/Color.kt`.
{{SHIP_NETWORK_LINE}}- Add a release signing config in `app/build.gradle.kts`.
- Rename the sample `Item` model to something from your own domain.
