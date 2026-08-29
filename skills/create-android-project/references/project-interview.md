# Interviewing the user

The goal is one round trip. Ask everything at once, show the defaults, and let
the user answer only what they care about.

## Suggested opening message

> Before I scaffold anything, a few things. Reply "defaults" for anything you
> don't mind.
>
> **Needed:**
> 1. **Architecture** — `mvvm` (single module, ViewModel talks straight to the
>    repository; good for small apps) or `clean-mvvm` (multi module with a pure
>    Kotlin domain layer and use cases; good for larger, longer-lived apps).
> 2. **App name** — what shows under the launcher icon, e.g. `Trail Log`.
> 3. **Package name** — applicationId and root Kotlin package, e.g.
>    `com.acme.traillog`.
>
> **Defaults, override if you like:**
> 4. Project folder: kebab-case of the app name
> 5. First screen: `home`
> 6. minSdk `24`, compileSdk/targetSdk `34`
> 7. Room database: yes
> 8. Retrofit API: yes
> 9. DataStore settings: yes
> 10. Test utilities: yes
> 11. R8 minification on release: yes

## Handling the required answers

### Architecture

If the user has not thought about it, ask one question: how many screens do they
expect, and how many people will work on it. Then recommend from
`architecture-selection.md`. Do not present `clean-mvvm` as strictly better.

If they say something like "keep it simple", pick `mvvm`. If they say
"production", "we're a team", or "this will grow", pick `clean-mvvm`. Say which
you chose and why in one line, then continue.

### App name

Take it verbatim, including spaces and capitals. It becomes:
- `app_name` in `strings.xml` (XML-escaped)
- the PascalCase class prefix: `Trail Log` → `TrailLogApplication`,
  `TrailLogTheme`, `TrailLogDatabase`, `TrailLogNavHost`
- the default `rootProjectName` and `projectDirName`

### Package name

This is the one answer that is genuinely expensive to change later, because it is
the applicationId that identifies the app on Play and on device. Push back if it
looks like a placeholder.

Rules enforced by the scaffolder:
- lowercase segments separated by dots, at least two segments
- each segment starts with a letter
- no segment may be a Kotlin or Java reserved word (`object`, `class`, `data`,
  `in`, `is`, `fun`, …), which is a real trap for domains like `in` (India) or
  companies named `object`

If the user gives `com.example.*`, note that it cannot be published to Play and
offer to use a reverse of a domain they control.

## Handling the optional answers

### First screen / feature name

One lowercase word, no separators: `home`, `feed`, `tasks`, `dashboard`. It
becomes a route constant (`TASKS_ROUTE`), a class prefix (`TasksViewModel`), and
in `clean-mvvm` two module paths (`feature/tasks/api`, `feature/tasks/impl`).

If the user offers a multi-word name, ask for a single word or condense it
(`my tasks` → `tasks`).

### minSdk

Default 24. Only expand if asked: a lower minSdk reaches more devices but costs
compatibility work; a higher one unlocks newer APIs. Note that dynamic colour
needs API 31 either way, and the generated theme already guards for that.

Do not go below 21; Compose requires it and the scaffolder rejects it.

### Room, Retrofit, DataStore

Map plain-language answers onto the flags:

| User says | Flags |
|---|---|
| "it needs to work offline" | Room yes |
| "it talks to our API" | Room yes, Retrofit yes |
| "no backend yet" | Retrofit no |
| "just local data" | Room yes, Retrofit no |
| "everything in memory for now" | Room no, Retrofit no |
| "users can pick a theme" | DataStore yes |
| "no settings" | DataStore no |

Retrofit requires Room. The generated repository is offline-first, so remote data
needs somewhere local to land. If the user wants network-only, explain that and
let them choose: keep Room, or take Retrofit out and add a plain network
repository afterwards.

With Room off you get an in-memory repository seeded with sample items. It
implements the same interface, so swapping it for a database-backed one later
changes nothing above the data layer.

### Test utilities

Generates helpers, not tests: a `MainDispatcherRule` and a `FakeItemRepository`.
In `clean-mvvm` these go in a `core:testing` module; in `mvvm` they go in
`src/test`. Say yes unless the user objects.

### R8 minification

Default on, with a `proguard-rules.pro` that carries the `-dontwarn` entries the
common libraries need. Turn it off if the user wants the simplest possible
release build to start with.

## Confirm before writing

Echo the decisions back compactly and wait for a yes:

> Scaffolding **Trail Log** at `/home/you/projects/trail-log`:
> `clean-mvvm`, package `com.acme.traillog`, first screen `home`, minSdk 24,
> Room + Retrofit + DataStore + test utilities, R8 on for release.
> 12 Gradle modules. Go ahead?

## Do not ask about

These are decided by the power and should not be put to the user unless they
raise them:

- Kotlin, AGP, Compose or Hilt versions (a matched set in the version catalog)
- Kotlin DSL vs Groovy for build files (always Kotlin DSL)
- Hilt vs Koin (always Hilt; the Android-first choice here)
- Compose vs Views (always Compose)
- Java version (always 17)
- whether to use a version catalog (always yes)

If the user asks to change any of these, that is a real request. Handle it after
scaffolding rather than trying to parameterise the generator.
