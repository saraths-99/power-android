# Choosing between MVVM and Clean Architecture + MVVM

Both options are first-class. This file exists so the recommendation is grounded
in the project's actual shape rather than a blanket preference.

## The short version

- **Small project** → `mvvm`. Single module, ViewModel talks to the repository.
- **Large project** → `clean-mvvm`. Multi module, ViewModel talks to use cases.

## What actually differs

| | `mvvm` | `clean-mvvm` |
|---|---|---|
| Gradle modules | 1 | 10 to 12 |
| Domain layer | none | `domain/` (pure Kotlin) |
| Repository interface lives in | `data/repository` | `domain/repository` |
| ViewModel depends on | `ItemRepository` | use cases |
| Convention plugins | none | `build-logic/convention` |
| Files generated (all layers on) | ~61 | ~94 |
| Layers a change to one screen touches | 1 module | 1 to 2 modules |
| Domain unit tests need Android | n/a | no, JVM only |
| Onboarding cost | low | moderate |
| Incremental build isolation | none | good |

Everything else is shared: Compose, Hilt, offline-first Room, Retrofit,
DataStore, unidirectional data flow, `Route`/`Screen` split, hand-written test
doubles, version catalog.

## Signals for `mvvm`

- Fewer than roughly 5 to 8 screens.
- One or two developers.
- Prototype, internal tool, demo, or a bet you might throw away.
- The team has not worked in a multi-module codebase before.
- Speed of first release matters more than long-run structure.

## Signals for `clean-mvvm`

- The app is expected to grow for years.
- More than two developers, or separate feature teams that should not block
  each other.
- Build times already noticeable, or expected to be.
- Business rules reused across several screens.
- You want unit tests for business logic that never touch Android.
- Kotlin Multiplatform is on the roadmap: a framework-free `domain` module is
  most of the work of getting there.

## Signals that neither is the real problem

If the user is unsure because requirements are unclear, the architecture is not
the thing to decide first. Ask what the first two screens are. That usually
settles it.

## Cost of `clean-mvvm` on a small app

Be honest about this rather than treating more structure as free:

- Adding one screen means editing 2 new modules plus `settings.gradle.kts`,
  the NavHost, and usually 1 to 3 new use case classes.
- A one-line change can span `domain`, `data`, and a feature module.
- Convention plugins are another layer to understand before the build makes
  sense.

On a 4-screen app this is overhead with little payoff. On a 40-screen app it is
what keeps the codebase workable.

## Starting with `mvvm` is not a dead end

The generated MVVM project is deliberately laid out so it can be lifted into the
clean layout later. The migration, in order:

1. Create a `domain` module with the `jvm-library` convention (or plain
   `kotlin("jvm")`), and move `model/` into it.
2. Move the `ItemRepository` **interface** into `domain/repository`, leaving
   `ItemRepositoryImpl` behind in `data`.
3. Add use cases in `domain/usecase` that wrap the repository, then change each
   ViewModel's constructor to take use cases instead of the repository.
4. Split `data/local`, `data/remote` and `data/preferences` into `core:database`,
   `core:network` and `core:datastore` modules.
5. Move `ui/theme` into `core:designsystem` and `ui/components` into `core:ui`.
6. Move each `ui/<feature>` package into `feature/<name>/impl`, and extract the
   route constant into `feature/<name>/api`.

Steps 1 to 3 deliver most of the testability benefit and can be done without
touching the module graph at all. That is a reasonable middle stop.

## What not to do

- Do not pick `clean-mvvm` because it sounds more professional. Unused
  indirection is a cost paid on every read.
- Do not pick `mvvm` for an app you already know will have 30 screens and four
  developers. Retrofitting module boundaries onto a large single module is
  substantially harder than starting with them.
- Do not mix the two by adding a `domain` package inside the single module and
  calling it clean. Without a module boundary nothing enforces the dependency
  rule, so it decays.
