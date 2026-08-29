#!/usr/bin/env python3
"""Scaffold a new Android project in one of two architectures.

  architecture = "mvvm"
      Single-module app. UI (Compose + ViewModel + UiState) -> Repository ->
      data sources. No domain layer, no convention plugins. Right for small
      apps, prototypes and single-developer projects.

  architecture = "clean-mvvm"
      Multi-module Clean Architecture with MVVM in the presentation layer.
      A pure-Kotlin `domain` module owns models, repository interfaces and use
      cases; `data` implements them; feature modules depend on `domain` only.
      Right for larger or longer-lived codebases and multiple teams.

Usage:
    python3 scaffold_android_project.py --config project.json [--output-dir DIR]
    python3 scaffold_android_project.py --print-config-template [--architecture X]
    python3 scaffold_android_project.py --config project.json --dry-run

The Gradle wrapper JAR is a binary and is not generated. Run
`scripts/init_gradle_wrapper.sh <project-dir>` afterwards, or open the project in
Android Studio, which creates the wrapper for you.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path
from typing import Any, Dict, List, Tuple

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

MVVM = "mvvm"
CLEAN = "clean-mvvm"
ARCHITECTURES = (MVVM, CLEAN)

CONFIG_TEMPLATE: Dict[str, Any] = {
    "architecture": CLEAN,
    "appName": "My App",
    "packageName": "com.example.myapp",
    "projectDirName": "my-app",
    "rootProjectName": "MyApp",
    "initialFeature": "home",
    "minSdk": 24,
    "compileSdk": 34,
    "targetSdk": 34,
    "includeDatabase": True,
    "includeNetwork": True,
    "includeDatastore": True,
    "includeTestUtilities": True,
    "minifyRelease": True,
    "gradleVersion": "8.6",
}

# Architecture must be an explicit decision, not an accident of the defaults.
REQUIRED_KEYS = ("architecture", "appName", "packageName")

PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
FEATURE_RE = re.compile(r"^[a-z][a-z0-9]*$")

JAVA_VERSION = 17
KOTLIN_RESERVED = {
    "as", "break", "class", "continue", "do", "else", "false", "for", "fun", "if",
    "in", "interface", "is", "null", "object", "package", "return", "super",
    "this", "throw", "true", "try", "typealias", "typeof", "val", "var", "when",
    "while", "internal", "public", "private", "protected", "fn", "data", "enum",
}


class ScaffoldError(Exception):
    """Raised when the requested configuration cannot produce a valid project."""


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


def _load_template(relative_path: str) -> str:
    """Read a template file from assets/templates/, by path relative to it.

    Templates are plain text (Kotlin, Gradle Kotlin DSL, XML, TOML, or
    Markdown) containing {{TOKEN}} placeholders, resolved later by render().
    Keeping them as real files on disk, rather than Python string constants,
    means each one can be opened, linted and diffed as the language it
    actually is.
    """
    path = TEMPLATES_DIR / relative_path
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ScaffoldError(f"template asset is missing: {path}")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def pascal_case(value: str) -> str:
    out = []
    for part in re.split(r"[^A-Za-z0-9]+", value):
        if not part:
            continue
        if part[:1].isupper() and any(c.islower() for c in part[1:]):
            out.append(part)
        else:
            out.append(part[:1].upper() + part[1:].lower())
    return "".join(out) or "App"


def kebab_case(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower() or "app"


def alnum_lower(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value).lower() or "app"


def xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def kotlin_escape(value: str) -> str:
    """Escape a value for embedding in a Kotlin double-quoted string literal."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("\r", "")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def render(text: str, ctx: Dict[str, str]) -> str:
    # Longest keys first so PKG_MODEL is never partially matched by PKG.
    for key in sorted(ctx, key=len, reverse=True):
        text = text.replace("{{" + key + "}}", str(ctx[key]))
    left = re.findall(r"\{\{[A-Za-z_0-9]+\}\}", text)
    if left:
        raise ScaffoldError(f"unresolved template tokens: {sorted(set(left))}")
    return text


def solid_png(size: int, rgb: Tuple[int, int, int]) -> bytes:
    """Build a minimal valid 8-bit RGB PNG of a single colour."""
    r, g, b = rgb
    raw = (b"\x00" + bytes([r, g, b]) * size) * size

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return (
            struct.pack(">I", len(data))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def kt_file(module_dir: str, package: str, filename: str) -> str:
    return f"{module_dir}/src/main/kotlin/{package.replace('.', '/')}/{filename}"


def kt_test_file(module_dir: str, package: str, filename: str) -> str:
    return f"{module_dir}/src/test/kotlin/{package.replace('.', '/')}/{filename}"


# --------------------------------------------------------------------------- #
# Config loading
# --------------------------------------------------------------------------- #


def load_config(path: Path) -> Dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ScaffoldError(f"config file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ScaffoldError(f"config file is not valid JSON: {exc}")
    if not isinstance(raw, dict):
        raise ScaffoldError("config file must contain a JSON object")

    unknown = sorted(set(raw) - set(CONFIG_TEMPLATE))
    if unknown:
        raise ScaffoldError(
            f"unknown config keys: {unknown}. Supported keys: {sorted(CONFIG_TEMPLATE)}"
        )

    cfg = dict(CONFIG_TEMPLATE)
    cfg.update(raw)

    for key in REQUIRED_KEYS:
        if key not in raw or not str(raw.get(key) or "").strip():
            raise ScaffoldError(
                f"config key '{key}' is required and must be set explicitly"
                + (
                    f" (choose one of: {', '.join(ARCHITECTURES)})"
                    if key == "architecture"
                    else ""
                )
            )

    cfg["architecture"] = str(cfg["architecture"]).strip().lower()
    if cfg["architecture"] not in ARCHITECTURES:
        raise ScaffoldError(
            f"architecture must be one of {list(ARCHITECTURES)}, "
            f"got '{cfg['architecture']}'"
        )

    cfg["packageName"] = str(cfg["packageName"]).strip()
    if not PACKAGE_RE.match(cfg["packageName"]):
        raise ScaffoldError(
            f"packageName '{cfg['packageName']}' is not a valid Android package "
            "(expected lowercase segments separated by dots, e.g. com.example.myapp)"
        )
    for segment in cfg["packageName"].split("."):
        if segment in KOTLIN_RESERVED:
            raise ScaffoldError(
                f"packageName segment '{segment}' is a Kotlin/Java reserved word"
            )

    cfg["initialFeature"] = alnum_lower(str(cfg["initialFeature"]) or "home")
    if not FEATURE_RE.match(cfg["initialFeature"]):
        raise ScaffoldError("initialFeature must be a single lowercase word, e.g. home")
    if cfg["initialFeature"] in KOTLIN_RESERVED:
        raise ScaffoldError(
            f"initialFeature '{cfg['initialFeature']}' is a Kotlin reserved word"
        )

    for key in ("minSdk", "compileSdk", "targetSdk"):
        try:
            cfg[key] = int(cfg[key])
        except (TypeError, ValueError):
            raise ScaffoldError(f"config key '{key}' must be an integer")
    if cfg["minSdk"] < 21:
        raise ScaffoldError("minSdk must be 21 or higher (Compose requires 21+)")
    if cfg["targetSdk"] > cfg["compileSdk"]:
        raise ScaffoldError("targetSdk cannot be greater than compileSdk")
    if cfg["minSdk"] > cfg["targetSdk"]:
        raise ScaffoldError("minSdk cannot be greater than targetSdk")

    for key in (
        "includeDatabase",
        "includeNetwork",
        "includeDatastore",
        "includeTestUtilities",
        "minifyRelease",
    ):
        cfg[key] = bool(cfg[key])

    if cfg["includeNetwork"] and not cfg["includeDatabase"]:
        raise ScaffoldError(
            "includeNetwork requires includeDatabase: the generated repository is "
            "offline-first, so remote data needs a local source of truth"
        )

    cfg["projectDirName"] = kebab_case(str(cfg.get("projectDirName") or cfg["appName"]))
    cfg["rootProjectName"] = (
        str(cfg.get("rootProjectName") or "").strip() or pascal_case(cfg["appName"])
    )
    return cfg


def build_context(cfg: Dict[str, Any]) -> Dict[str, str]:
    pkg = cfg["packageName"]
    app_class = pascal_case(cfg["appName"])
    feature = cfg["initialFeature"]
    clean = cfg["architecture"] == CLEAN

    ctx = {
        "PKG": pkg,
        "APP_NAME": cfg["appName"],
        "APP_NAME_XML": xml_escape(cfg["appName"]),
        "APP_NAME_KT": kotlin_escape(cfg["appName"]),
        "APP_CLASS": app_class,
        # Avoid "MyAppApp" when the app name already ends in "App".
        "APP_ROOT": app_class if app_class.endswith("App") else app_class + "App",
        "ROOT_PROJECT": cfg["rootProjectName"],
        "PREFIX": alnum_lower(cfg["rootProjectName"]),
        "DB_NAME": kebab_case(cfg["rootProjectName"]) + "-database",
        "FEATURE": feature,
        "FEATURE_CLASS": pascal_case(feature),
        "FEATURE_UPPER": feature.upper(),
        "MIN_SDK": str(cfg["minSdk"]),
        "COMPILE_SDK": str(cfg["compileSdk"]),
        "TARGET_SDK": str(cfg["targetSdk"]),
        "JAVA_VERSION": str(JAVA_VERSION),
        "GRADLE_VERSION": str(cfg["gradleVersion"]),
        "ARCHITECTURE": cfg["architecture"],
    }

    # Package layout per architecture. Every Kotlin template refers to these
    # tokens instead of hard-coding a package, so the same source templates
    # serve both architectures.
    if clean:
        ctx.update(
            {
                "PKG_MODEL": f"{pkg}.domain.model",
                "PKG_REPO": f"{pkg}.domain.repository",
                "PKG_USECASE": f"{pkg}.domain.usecase",
                "PKG_REPO_IMPL": f"{pkg}.data.repository",
                "PKG_MAPPER": f"{pkg}.data.mapper",
                "PKG_DATA_DI": f"{pkg}.data.di",
                "PKG_RESULT": f"{pkg}.core.common.result",
                "PKG_DISPATCHERS": f"{pkg}.core.common.dispatcher",
                "PKG_DISPATCHERS_DI": f"{pkg}.core.common.dispatcher.di",
                "PKG_DB": f"{pkg}.core.database",
                "PKG_DB_DI": f"{pkg}.core.database.di",
                "PKG_NET": f"{pkg}.core.network",
                "PKG_NET_DI": f"{pkg}.core.network.di",
                "PKG_PREFS": f"{pkg}.core.datastore",
                "PKG_PREFS_DI": f"{pkg}.core.datastore.di",
                "PKG_THEME": f"{pkg}.core.designsystem.theme",
                "PKG_COMPONENTS": f"{pkg}.core.ui",
                "PKG_FEATURE": f"{pkg}.feature.{feature}.impl",
                "PKG_FEATURE_NAV": f"{pkg}.feature.{feature}.impl.navigation",
                "PKG_FEATURE_API": f"{pkg}.feature.{feature}.api",
                "PKG_NAV": f"{pkg}.navigation",
                "PKG_APP_UI": f"{pkg}.ui",
                "PKG_TESTING": f"{pkg}.core.testing",
                # Feature impl module namespace == its package, so R needs no import.
                "R_IMPORT": "",
                "ACTIVITY_VM_IMPORT": f"import {pkg}.domain.usecase.ObserveUserDataUseCase\n",
                "ACTIVITY_VM_PARAM": "observeUserData: ObserveUserDataUseCase,",
                "ACTIVITY_VM_SOURCE": "observeUserData()",
            }
        )
    else:
        ctx.update(
            {
                "PKG_MODEL": f"{pkg}.model",
                "PKG_REPO": f"{pkg}.data.repository",
                "PKG_USECASE": f"{pkg}.data.repository",  # unused in MVVM
                "PKG_REPO_IMPL": f"{pkg}.data.repository",
                "PKG_MAPPER": f"{pkg}.data.mapper",
                "PKG_DATA_DI": f"{pkg}.di",
                "PKG_RESULT": f"{pkg}.common",
                "PKG_DISPATCHERS": f"{pkg}.common",
                "PKG_DISPATCHERS_DI": f"{pkg}.di",
                "PKG_DB": f"{pkg}.data.local",
                "PKG_DB_DI": f"{pkg}.di",
                "PKG_NET": f"{pkg}.data.remote",
                "PKG_NET_DI": f"{pkg}.di",
                "PKG_PREFS": f"{pkg}.data.preferences",
                "PKG_PREFS_DI": f"{pkg}.di",
                "PKG_THEME": f"{pkg}.ui.theme",
                "PKG_COMPONENTS": f"{pkg}.ui.components",
                "PKG_FEATURE": f"{pkg}.ui.{feature}",
                "PKG_FEATURE_NAV": f"{pkg}.ui.navigation",
                "PKG_FEATURE_API": f"{pkg}.ui.navigation",
                "PKG_NAV": f"{pkg}.ui.navigation",
                "PKG_APP_UI": f"{pkg}.ui",
                "PKG_TESTING": f"{pkg}.testing",
                # Single module: R lives at the app namespace, so it must be imported.
                "R_IMPORT": f"import {pkg}.R\n",
                "ACTIVITY_VM_IMPORT": f"import {pkg}.data.repository.UserDataRepository\n",
                "ACTIVITY_VM_PARAM": "userDataRepository: UserDataRepository,",
                "ACTIVITY_VM_SOURCE": "userDataRepository.userData",
            }
        )

    # Imports that would be redundant when two roles share a package (which is
    # what happens in the single-module layout) are emitted as empty strings.
    def same_package_aware(import_pkg: str, symbol: str, target_pkg: str) -> str:
        return "" if import_pkg == target_pkg else f"import {import_pkg}.{symbol}\n"

    ctx["REPO_IFACE_IMPORT"] = same_package_aware(
        ctx["PKG_REPO"], "ItemRepository", ctx["PKG_REPO_IMPL"]
    )
    ctx["USER_REPO_IFACE_IMPORT"] = same_package_aware(
        ctx["PKG_REPO"], "UserDataRepository", ctx["PKG_REPO_IMPL"]
    )
    ctx["ROUTE_IMPORT"] = same_package_aware(
        ctx["PKG_FEATURE_API"], f"{ctx['FEATURE_UPPER']}_ROUTE", ctx["PKG_FEATURE_NAV"]
    )
    ctx["NAVHOST_IMPORTS"] = same_package_aware(
        ctx["PKG_FEATURE_API"], f"{ctx['FEATURE_UPPER']}_ROUTE", ctx["PKG_NAV"]
    ) + same_package_aware(
        ctx["PKG_FEATURE_NAV"], f"{ctx['FEATURE']}Screen", ctx["PKG_NAV"]
    )
    return ctx


# --------------------------------------------------------------------------- #
# Root build files (shared)
# --------------------------------------------------------------------------- #

SETTINGS_GRADLE = _load_template("root/SETTINGS_GRADLE.gradle.kts")

ROOT_BUILD_GRADLE = _load_template("root/ROOT_BUILD_GRADLE.gradle.kts")

GRADLE_PROPERTIES = _load_template("root/GRADLE_PROPERTIES.properties")

GRADLE_WRAPPER_PROPERTIES = _load_template("root/GRADLE_WRAPPER_PROPERTIES.properties")

GITIGNORE = _load_template("root/GITIGNORE.gitignore")

VERSION_CATALOG_BASE = _load_template("root/VERSION_CATALOG_BASE.toml")

VERSION_CATALOG_CONVENTION = _load_template("root/VERSION_CATALOG_CONVENTION.toml")

# --------------------------------------------------------------------------- #
# build-logic (clean-mvvm only)
# --------------------------------------------------------------------------- #

BUILD_LOGIC_SETTINGS = _load_template("build-logic/BUILD_LOGIC_SETTINGS.gradle.kts")

BUILD_LOGIC_CONVENTION_BUILD = _load_template("build-logic/BUILD_LOGIC_CONVENTION_BUILD.gradle.kts")

# Each plugin configures the concrete AGP extension type (ApplicationExtension /
# LibraryExtension) rather than the star-projected CommonExtension, so the code
# is not sensitive to AGP's type-parameter arity.
CONVENTION_SOURCES: Dict[str, str] = {
    path.name: path.read_text(encoding="utf-8")
    for path in sorted((TEMPLATES_DIR / "convention-sources").glob("*.kt"))
}













# --------------------------------------------------------------------------- #
# Kotlin source templates
#
# Every template addresses packages through {{PKG_*}} tokens, so the same source
# serves both architectures; only the token values and the target module change.
# --------------------------------------------------------------------------- #

T_MODEL_ITEM = _load_template("kotlin/T_MODEL_ITEM.kt")

T_MODEL_DARK_THEME = _load_template("kotlin/T_MODEL_DARK_THEME.kt")

T_MODEL_USER_DATA = _load_template("kotlin/T_MODEL_USER_DATA.kt")

T_DISPATCHERS = _load_template("kotlin/T_DISPATCHERS.kt")

T_DISPATCHERS_MODULE = _load_template("kotlin/T_DISPATCHERS_MODULE.kt")

T_THEME_COLOR = _load_template("kotlin/T_THEME_COLOR.kt")

T_THEME_TYPE = _load_template("kotlin/T_THEME_TYPE.kt")

T_THEME = _load_template("kotlin/T_THEME.kt")

T_ITEM_CARD = _load_template("kotlin/T_ITEM_CARD.kt")

T_STATE_VIEWS = _load_template("kotlin/T_STATE_VIEWS.kt")

# --------------------------------------------------------------------------- #
# Local persistence (Room)
# --------------------------------------------------------------------------- #

T_DB_ENTITY = _load_template("kotlin/T_DB_ENTITY.kt")

T_DB_DAO = _load_template("kotlin/T_DB_DAO.kt")

T_DB_DATABASE = _load_template("kotlin/T_DB_DATABASE.kt")

T_DB_MODULE = _load_template("kotlin/T_DB_MODULE.kt")

# --------------------------------------------------------------------------- #
# Remote (Retrofit)
# --------------------------------------------------------------------------- #

T_NET_DTO = _load_template("kotlin/T_NET_DTO.kt")

T_NET_DATASOURCE = _load_template("kotlin/T_NET_DATASOURCE.kt")

T_NET_RETROFIT = _load_template("kotlin/T_NET_RETROFIT.kt")

T_NET_MODULE = _load_template("kotlin/T_NET_MODULE.kt")

# --------------------------------------------------------------------------- #
# Preferences (DataStore)
# --------------------------------------------------------------------------- #

T_PREFS_DATASOURCE = _load_template("kotlin/T_PREFS_DATASOURCE.kt")

T_PREFS_MODULE = _load_template("kotlin/T_PREFS_MODULE.kt")


# --------------------------------------------------------------------------- #
# Mappers
# --------------------------------------------------------------------------- #

T_ITEM_MAPPERS_HEAD = _load_template("kotlin/T_ITEM_MAPPERS_HEAD.kt")



T_ITEM_MAPPERS_BODY_DB = _load_template("kotlin/T_ITEM_MAPPERS_BODY_DB.kt")

T_ITEM_MAPPERS_BODY_NET = _load_template("kotlin/T_ITEM_MAPPERS_BODY_NET.kt")

T_PREFS_MAPPERS = _load_template("kotlin/T_PREFS_MAPPERS.kt")

# --------------------------------------------------------------------------- #
# Repositories
# --------------------------------------------------------------------------- #

T_REPO_ITEM = _load_template("kotlin/T_REPO_ITEM.kt")

T_REPO_ITEM_IMPL_OFFLINE = _load_template("kotlin/T_REPO_ITEM_IMPL_OFFLINE.kt")

T_REPO_ITEM_IMPL_MEMORY = _load_template("kotlin/T_REPO_ITEM_IMPL_MEMORY.kt")

T_REPO_USER = _load_template("kotlin/T_REPO_USER.kt")

T_REPO_USER_IMPL = _load_template("kotlin/T_REPO_USER_IMPL.kt")

T_REPO_MODULE = _load_template("kotlin/T_REPO_MODULE.kt")

# --------------------------------------------------------------------------- #
# Use cases (clean-mvvm only)
# --------------------------------------------------------------------------- #

T_USE_CASE = _load_template("kotlin/T_USE_CASE.kt")


def use_case_specs(cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    """One use case per business operation, as separate classes."""
    specs = [
        {
            "name": "ObserveItemsUseCase",
            "doc": "Streams every item, newest state first on each change.",
            "repo": "ItemRepository",
            "imports": ["{{PKG_MODEL}}.Item", "{{PKG_REPO}}.ItemRepository", "kotlinx.coroutines.flow.Flow"],
            "signature": "operator fun invoke(): Flow<List<Item>>",
            "body": "repository.observeItems()",
        },
        {
            "name": "ObserveItemUseCase",
            "doc": "Streams a single item, or null once it is gone.",
            "repo": "ItemRepository",
            "imports": ["{{PKG_MODEL}}.Item", "{{PKG_REPO}}.ItemRepository", "kotlinx.coroutines.flow.Flow"],
            "signature": "operator fun invoke(id: String): Flow<Item?>",
            "body": "repository.observeItem(id)",
        },
        {
            "name": "UpsertItemUseCase",
            "doc": "Creates the item, or updates it if the id already exists.",
            "repo": "ItemRepository",
            "imports": ["{{PKG_MODEL}}.Item", "{{PKG_REPO}}.ItemRepository"],
            "signature": "suspend operator fun invoke(item: Item)",
            "body": "repository.upsertItem(item)",
        },
        {
            "name": "DeleteItemUseCase",
            "doc": "Removes the item with the given id.",
            "repo": "ItemRepository",
            "imports": ["{{PKG_REPO}}.ItemRepository"],
            "signature": "suspend operator fun invoke(id: String)",
            "body": "repository.deleteItem(id)",
        },
        {
            "name": "SyncItemsUseCase",
            "doc": "Refreshes the local store from the remote source.",
            "repo": "ItemRepository",
            "imports": ["{{PKG_REPO}}.ItemRepository"],
            "signature": "suspend operator fun invoke(): Boolean",
            "body": "repository.sync()",
        },
    ]
    if cfg["includeDatastore"]:
        specs += [
            {
                "name": "ObserveUserDataUseCase",
                "doc": "Streams the user's settings.",
                "repo": "UserDataRepository",
                "imports": [
                    "{{PKG_MODEL}}.UserData",
                    "{{PKG_REPO}}.UserDataRepository",
                    "kotlinx.coroutines.flow.Flow",
                ],
                "signature": "operator fun invoke(): Flow<UserData>",
                "body": "repository.userData",
            },
            {
                "name": "SetDarkThemeConfigUseCase",
                "doc": "Persists the user's dark theme choice.",
                "repo": "UserDataRepository",
                "imports": [
                    "{{PKG_MODEL}}.DarkThemeConfig",
                    "{{PKG_REPO}}.UserDataRepository",
                ],
                "signature": "suspend operator fun invoke(darkThemeConfig: DarkThemeConfig)",
                "body": "repository.setDarkThemeConfig(darkThemeConfig)",
            },
            {
                "name": "SetDynamicColorPreferenceUseCase",
                "doc": "Persists whether wallpaper-derived colours are used.",
                "repo": "UserDataRepository",
                "imports": ["{{PKG_REPO}}.UserDataRepository"],
                "signature": "suspend operator fun invoke(useDynamicColor: Boolean)",
                "body": "repository.setDynamicColorPreference(useDynamicColor)",
            },
        ]
    return specs


# --------------------------------------------------------------------------- #
# Presentation layer (MVVM in both architectures)
# --------------------------------------------------------------------------- #

T_FEATURE_UISTATE = _load_template("kotlin/T_FEATURE_UISTATE.kt")

# MVVM: the ViewModel talks to the repository directly. Fewer moving parts, which
# is the point of this architecture for a small app.
T_FEATURE_VIEWMODEL_MVVM = _load_template("kotlin/T_FEATURE_VIEWMODEL_MVVM.kt")

# Clean + MVVM: the ViewModel depends on use cases, never on a repository. It has
# no idea whether data comes from Room, the network, or a fake.
T_FEATURE_VIEWMODEL_CLEAN = _load_template("kotlin/T_FEATURE_VIEWMODEL_CLEAN.kt")

T_FEATURE_SCREEN = _load_template("kotlin/T_FEATURE_SCREEN.kt")

T_FEATURE_ROUTE = _load_template("kotlin/T_FEATURE_ROUTE.kt")

T_FEATURE_NAV = _load_template("kotlin/T_FEATURE_NAV.kt")

T_NAV_HOST = _load_template("kotlin/T_NAV_HOST.kt")

T_APP_ROOT = _load_template("kotlin/T_APP_ROOT.kt")

T_APPLICATION = _load_template("kotlin/T_APPLICATION.kt")

T_MAIN_ACTIVITY_VM = _load_template("kotlin/T_MAIN_ACTIVITY_VM.kt")

T_MAIN_ACTIVITY_SETTINGS = _load_template("kotlin/T_MAIN_ACTIVITY_SETTINGS.kt")

T_MAIN_ACTIVITY_PLAIN = _load_template("kotlin/T_MAIN_ACTIVITY_PLAIN.kt")

# --------------------------------------------------------------------------- #
# Test utilities (infrastructure, not tests)
# --------------------------------------------------------------------------- #

T_TEST_DISPATCHER_RULE = _load_template("kotlin/T_TEST_DISPATCHER_RULE.kt")

T_TEST_FAKE_REPO = _load_template("kotlin/T_TEST_FAKE_REPO.kt")

# --------------------------------------------------------------------------- #
# Android resources
# --------------------------------------------------------------------------- #

T_MANIFEST = _load_template("kotlin/T_MANIFEST.xml")

T_THEMES_XML = _load_template("kotlin/T_THEMES_XML.xml")

T_FEATURE_STRINGS = _load_template("kotlin/T_FEATURE_STRINGS.xml.fragment")

T_PROGUARD_HEAD = _load_template("kotlin/T_PROGUARD_HEAD.pro")

# OkHttp references these optional TLS providers reflectively; without the
# -dontwarn entries R8 fails the release build on missing classes.
T_PROGUARD_OKHTTP = _load_template("kotlin/T_PROGUARD_OKHTTP.pro")


# --------------------------------------------------------------------------- #
# Emit helpers
# --------------------------------------------------------------------------- #


def emit(
    files: Dict[str, str],
    ctx: Dict[str, str],
    module: str,
    pkg_token: str,
    filename: str,
    template: str,
    extra: Dict[str, str] = None,
    test_source: bool = False,
    package_suffix: str = "",
) -> None:
    local = dict(ctx)
    if extra:
        local.update(extra)
    package = ctx[pkg_token] + (("." + package_suffix) if package_suffix else "")
    path_fn = kt_test_file if test_source else kt_file
    files[path_fn(module, package, filename)] = render(template, local)


def module_build_file(
    ctx: Dict[str, str],
    namespace: str,
    plugins: List[str],
    dependencies: List[str],
    extra_blocks: str = "",
) -> str:
    plugin_lines = "\n".join("    " + p for p in plugins)
    dep_lines = "\n".join(("    " + d) if d else "" for d in dependencies)
    android_block = (
        f"\nandroid {{\n    namespace = \"{namespace}\"\n}}\n" if namespace else "\n"
    )
    deps_block = f"\ndependencies {{\n{dep_lines}\n}}\n" if dependencies else ""
    return f"plugins {{\n{plugin_lines}\n}}\n{android_block}{extra_blocks}{deps_block}"


def item_mappers_source(cfg: Dict[str, Any], ctx: Dict[str, str]) -> str:
    imports = [render("{{PKG_MODEL}}.Item", ctx)]
    if cfg["includeDatabase"]:
        imports.append(render("{{PKG_DB}}.model.ItemEntity", ctx))
    if cfg["includeNetwork"]:
        imports.append(render("{{PKG_NET}}.model.ItemDto", ctx))
    body = render(T_ITEM_MAPPERS_HEAD, ctx)
    body += "".join(f"import {i}\n" for i in sorted(imports))
    body += render(T_ITEM_MAPPERS_BODY_DB, ctx)
    if cfg["includeNetwork"]:
        body += render(T_ITEM_MAPPERS_BODY_NET, ctx)
    return body


def repository_module_source(cfg: Dict[str, Any], ctx: Dict[str, str]) -> str:
    imports = [
        render("{{PKG_REPO}}.ItemRepository", ctx),
        render("{{PKG_REPO_IMPL}}.ItemRepositoryImpl", ctx),
    ]
    binds = [
        "    @Binds\n"
        "    fun bindsItemRepository(impl: ItemRepositoryImpl): ItemRepository"
    ]
    if cfg["includeDatastore"]:
        imports += [
            render("{{PKG_REPO}}.UserDataRepository", ctx),
            render("{{PKG_REPO_IMPL}}.UserDataRepositoryImpl", ctx),
        ]
        binds.append(
            "    @Binds\n"
            "    fun bindsUserDataRepository("
            "impl: UserDataRepositoryImpl): UserDataRepository"
        )
    # Same-package imports would be redundant; drop them.
    di_pkg = ctx["PKG_DATA_DI"]
    import_block = "".join(
        f"import {i}\n"
        for i in sorted(set(imports))
        if i.rsplit(".", 1)[0] != di_pkg
    )
    return render(
        T_REPO_MODULE,
        {**ctx, "REPO_MODULE_IMPORTS": import_block, "REPO_BINDS": "\n\n".join(binds)},
    )


def offline_repository_source(cfg: Dict[str, Any], ctx: Dict[str, str]) -> str:
    imports = [
        render("{{PKG_DISPATCHERS}}.AppDispatchers", ctx),
        render("{{PKG_DISPATCHERS}}.Dispatcher", ctx),
        render("{{PKG_DB}}.dao.ItemDao", ctx),
        render("{{PKG_MAPPER}}.toDomain", ctx),
        render("{{PKG_MAPPER}}.toEntity", ctx),
        render("{{PKG_MODEL}}.Item", ctx),
    ]
    if ctx["PKG_REPO"] != ctx["PKG_REPO_IMPL"]:
        imports.append(render("{{PKG_REPO}}.ItemRepository", ctx))
    if cfg["includeNetwork"]:
        imports.append(render("{{PKG_NET}}.ItemRemoteDataSource", ctx))

    import_block = "".join(f"import {i}\n" for i in sorted(imports))
    import_block += (
        "import kotlinx.coroutines.CoroutineDispatcher\n"
        "import kotlinx.coroutines.flow.Flow\n"
        "import kotlinx.coroutines.flow.map\n"
        "import kotlinx.coroutines.withContext\n"
        "import javax.inject.Inject\n"
    )

    if cfg["includeNetwork"]:
        sync_body = (
            "        runCatching {\n"
            "            remoteDataSource.fetchItems().map { it.toEntity() }\n"
            "                .let { entities -> itemDao.upsertAll(entities) }\n"
            "        }.isSuccess"
        )
        remote_param = "    private val remoteDataSource: ItemRemoteDataSource,\n"
    else:
        sync_body = (
            "        // No remote source configured, so the local store is already current.\n"
            "        true"
        )
        remote_param = ""

    return render(
        T_REPO_ITEM_IMPL_OFFLINE,
        {
            **ctx,
            "OFFLINE_IMPORTS": import_block,
            "REMOTE_PARAM": remote_param,
            "SYNC_BODY": sync_body,
        },
    )


def add_shared_presentation(
    cfg: Dict[str, Any],
    ctx: Dict[str, str],
    files: Dict[str, str],
    ui_module: str,
    feature_module: str,
    nav_module: str,
    theme_module: str,
    components_module: str,
    viewmodel_template: str,
) -> None:
    """Design system, shared components, the feature screen, and the app shell."""
    emit(files, ctx, theme_module, "PKG_THEME", "Color.kt", T_THEME_COLOR)
    emit(files, ctx, theme_module, "PKG_THEME", "Type.kt", T_THEME_TYPE)
    emit(files, ctx, theme_module, "PKG_THEME", "Theme.kt", T_THEME)

    emit(files, ctx, components_module, "PKG_COMPONENTS", "ItemCard.kt", T_ITEM_CARD)
    emit(files, ctx, components_module, "PKG_COMPONENTS", "StateViews.kt", T_STATE_VIEWS)

    fc = ctx["FEATURE_CLASS"]
    emit(files, ctx, feature_module, "PKG_FEATURE", f"{fc}UiState.kt", T_FEATURE_UISTATE)
    emit(files, ctx, feature_module, "PKG_FEATURE", f"{fc}ViewModel.kt", viewmodel_template)
    emit(files, ctx, feature_module, "PKG_FEATURE", f"{fc}Screen.kt", T_FEATURE_SCREEN)
    emit(files, ctx, feature_module, "PKG_FEATURE_NAV", f"{fc}Navigation.kt", T_FEATURE_NAV)

    emit(files, ctx, nav_module, "PKG_NAV", f"{ctx['APP_CLASS']}NavHost.kt", T_NAV_HOST)
    emit(files, ctx, ui_module, "PKG_APP_UI", f"{ctx['APP_ROOT']}.kt", T_APP_ROOT)


def add_app_entry_points(
    cfg: Dict[str, Any], ctx: Dict[str, str], files: Dict[str, str]
) -> None:
    emit(files, ctx, "app", "PKG", f"{ctx['APP_CLASS']}Application.kt", T_APPLICATION)
    if cfg["includeDatastore"]:
        emit(files, ctx, "app", "PKG", "MainActivityViewModel.kt", T_MAIN_ACTIVITY_VM)
        emit(files, ctx, "app", "PKG", "MainActivity.kt", T_MAIN_ACTIVITY_SETTINGS)
    else:
        emit(files, ctx, "app", "PKG", "MainActivity.kt", T_MAIN_ACTIVITY_PLAIN)


def app_resources(cfg: Dict[str, Any], ctx: Dict[str, str], feature_strings: bool) -> Dict[str, str]:
    permissions = (
        '\n    <uses-permission android:name="android.permission.INTERNET" />\n'
        if cfg["includeNetwork"]
        else ""
    )
    strings = '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
    strings += render('    <string name="app_name">{{APP_NAME_XML}}</string>\n', ctx)
    if feature_strings:
        strings += render(T_FEATURE_STRINGS, ctx)
    strings += "</resources>\n"

    proguard = T_PROGUARD_HEAD + (T_PROGUARD_OKHTTP if cfg["includeNetwork"] else "")

    return {
        "app/src/main/AndroidManifest.xml": render(
            T_MANIFEST, {**ctx, "PERMISSIONS": permissions}
        ),
        "app/src/main/res/values/strings.xml": strings,
        "app/src/main/res/values/themes.xml": render(T_THEMES_XML, ctx),
        "app/proguard-rules.pro": proguard,
    }


STEERING_ASSETS = Path(__file__).resolve().parent.parent / "assets" / "steering"


def steering_files(cfg: Dict[str, Any], ctx: Dict[str, str]) -> Dict[str, str]:
    """Render the steering templates into the new project's `.kiro/steering/`.

    These carry the project's own conventions forward, so an agent working in the
    generated repository follows the architecture it was scaffolded with instead of
    guessing. Returns an empty dict if the assets are missing, so the scaffolder
    still works when the script is copied out of the power.
    """
    if not STEERING_ASSETS.is_dir():
        return {}

    clean = cfg["architecture"] == CLEAN
    local = dict(ctx)
    local.update(
        {
            "PROJECT_NAME": ctx["APP_NAME"],
            "PACKAGE_NAME": ctx["PKG"],
            "PACKAGE_PATH": ctx["PKG"].replace(".", "/"),
        }
    )

    if clean:
        local.update(
            {
                "DATA_FLOW_DIAGRAM": (
                    "Composable ──action──▶ ViewModel ──▶ UseCase ──▶ Repository ──▶ DataSource\n"
                    "Composable ◀──state─── ViewModel ◀── Flow ◀───────────────────────┘"
                ),
                "VM_CONSTRUCTOR": (
                    "    observeItems: ObserveItemsUseCase,\n"
                    "    private val syncItems: SyncItemsUseCase,\n"
                ),
                "VM_SOURCE": "observeItems()",
                "VM_DEPENDENCY_RULE": (
                    "A ViewModel depends on use cases, never on a repository. That is what\n"
                    "keeps `feature/*/impl` independent of `data`.\n"
                ),
                "USE_CASE_SECTION": (
                    "## 4a. Use cases\n"
                    "\n"
                    "One class per business operation, in `domain/usecase`, invoked with\n"
                    "`operator fun invoke`:\n"
                    "\n"
                    "```kotlin\n"
                    "class ObserveItemsUseCase @Inject constructor(\n"
                    "    private val repository: ItemRepository,\n"
                    ") {\n"
                    "    operator fun invoke(): Flow<List<Item>> = repository.observeItems()\n"
                    "}\n"
                    "```\n"
                    "\n"
                    "A thin pass-through use case is fine: its value is the dependency direction,\n"
                    "not the logic inside it. Business rules belong here rather than in a\n"
                    "ViewModel or a repository. Hilt constructs use cases directly, so they need\n"
                    "no module.\n"
                    "\n"
                ),
                "USE_CASE_NAMING_ROW": (
                    "| Use case | `<Verb><Thing>UseCase`, e.g. `ObserveItemsUseCase` |\n"
                ),
                "REPO_INTERFACE_HOME": "`domain/repository`",
                "REPO_BINDING_HOME": "`data/di/RepositoryModule.kt`",
                "COMPONENT_HOME": "`core:ui`",
                "TEST_DOUBLE_HOME": "`core:testing`",
            }
        )
    else:
        local.update(
            {
                "DATA_FLOW_DIAGRAM": (
                    "Composable ──action──▶ ViewModel ──▶ Repository ──▶ DataSource\n"
                    "Composable ◀──state─── ViewModel ◀── Flow ◀────────┘"
                ),
                "VM_CONSTRUCTOR": "    private val itemRepository: ItemRepository,\n",
                "VM_SOURCE": "itemRepository.observeItems()",
                "VM_DEPENDENCY_RULE": (
                    "A ViewModel depends on a repository interface, not on a DAO or a Retrofit\n"
                    "service. There is no use-case layer in this project by design.\n"
                ),
                "USE_CASE_SECTION": "",
                "USE_CASE_NAMING_ROW": "",
                "REPO_INTERFACE_HOME": "`data/repository`",
                "REPO_BINDING_HOME": "`di/RepositoryModule.kt`",
                "COMPONENT_HOME": "`ui/components`",
                "TEST_DOUBLE_HOME": "`src/test/.../testing/`",
            }
        )

    suffix = CLEAN if clean else MVVM
    sources = {
        "module-architecture.md": f"module-architecture-{suffix}.md",
        "build-conventions.md": f"build-conventions-{suffix}.md",
        "code-patterns.md": "code-patterns.md",
    }

    out: Dict[str, str] = {}
    for dest, src in sources.items():
        path = STEERING_ASSETS / src
        if not path.is_file():
            raise ScaffoldError(f"steering asset is missing: {path}")
        out[f".kiro/steering/{dest}"] = render(
            path.read_text(encoding="utf-8"), local
        )
    return out


def launcher_icons() -> Dict[str, bytes]:
    """Real PNG bytes so resource resolution works on every API level."""
    binary: Dict[str, bytes] = {}
    for density, size in (
        ("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)
    ):
        png = solid_png(size, (0x3B, 0x5B, 0xA9))
        binary[f"app/src/main/res/mipmap-{density}/ic_launcher.png"] = png
        binary[f"app/src/main/res/mipmap-{density}/ic_launcher_round.png"] = png
    return binary


T_APP_BUILD_MVVM = _load_template("app-build/T_APP_BUILD_MVVM.gradle.kts")

# --------------------------------------------------------------------------- #
# Architecture 1: MVVM, single module
# --------------------------------------------------------------------------- #


def build_mvvm(cfg: Dict[str, Any], ctx: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
    files: Dict[str, str] = {}

    plugins = [
        "alias(libs.plugins.android.application)",
        "alias(libs.plugins.kotlin.android)",
        "alias(libs.plugins.ksp)",
        "alias(libs.plugins.hilt)",
    ]
    if cfg["includeNetwork"]:
        plugins.append("alias(libs.plugins.kotlin.serialization)")
    if cfg["includeDatabase"]:
        plugins.append("alias(libs.plugins.room)")

    deps = [
        "implementation(platform(libs.androidx.compose.bom))",
        "androidTestImplementation(platform(libs.androidx.compose.bom))",
        "",
        "implementation(libs.androidx.core.ktx)",
        "implementation(libs.androidx.activity.compose)",
        "implementation(libs.androidx.compose.ui)",
        "implementation(libs.androidx.compose.ui.graphics)",
        "implementation(libs.androidx.compose.ui.tooling.preview)",
        "implementation(libs.androidx.compose.material3)",
        "implementation(libs.androidx.lifecycle.runtime.compose)",
        "implementation(libs.androidx.lifecycle.viewmodel.compose)",
        "implementation(libs.androidx.navigation.compose)",
        "",
        "implementation(libs.hilt.android)",
        "implementation(libs.androidx.hilt.navigation.compose)",
        "ksp(libs.hilt.android.compiler)",
        "",
        "implementation(libs.kotlinx.coroutines.android)",
    ]
    if cfg["includeDatabase"]:
        deps += [
            "",
            "implementation(libs.room.runtime)",
            "implementation(libs.room.ktx)",
            "ksp(libs.room.compiler)",
        ]
    if cfg["includeNetwork"]:
        deps += [
            "",
            "implementation(libs.kotlinx.serialization.json)",
            "implementation(libs.retrofit.core)",
            "implementation(libs.retrofit.kotlin.serialization)",
            "implementation(libs.okhttp.logging)",
        ]
    if cfg["includeDatastore"]:
        deps += ["", "implementation(libs.androidx.datastore.preferences)"]
    deps += [
        "",
        "debugImplementation(libs.androidx.compose.ui.tooling)",
        "debugImplementation(libs.androidx.compose.ui.test.manifest)",
        "",
        "testImplementation(libs.junit)",
        "testImplementation(libs.kotlinx.coroutines.test)",
    ]
    if cfg["includeTestUtilities"]:
        deps.append("testImplementation(libs.turbine)")
    deps += [
        "androidTestImplementation(libs.androidx.test.ext)",
        "androidTestImplementation(libs.androidx.compose.ui.test.junit4)",
    ]

    room_block = (
        '\nroom {\n    schemaDirectory("$projectDir/schemas")\n}\n'
        if cfg["includeDatabase"]
        else ""
    )

    files["app/build.gradle.kts"] = render(
        T_APP_BUILD_MVVM,
        {
            **ctx,
            "PLUGINS": "\n".join("    " + p for p in plugins),
            "MINIFY": "true" if cfg["minifyRelease"] else "false",
            "ROOM_BLOCK": room_block,
            "DEPENDENCIES": "\n".join(("    " + d) if d else "" for d in deps),
        },
    )

    m = "app"

    # Domain models
    emit(files, ctx, m, "PKG_MODEL", "Item.kt", T_MODEL_ITEM)
    if cfg["includeDatastore"]:
        emit(files, ctx, m, "PKG_MODEL", "DarkThemeConfig.kt", T_MODEL_DARK_THEME)
        emit(files, ctx, m, "PKG_MODEL", "UserData.kt", T_MODEL_USER_DATA)

    # Dispatchers
    emit(files, ctx, m, "PKG_DISPATCHERS", "AppDispatchers.kt", T_DISPATCHERS)
    emit(files, ctx, m, "PKG_DISPATCHERS_DI", "DispatchersModule.kt", T_DISPATCHERS_MODULE)

    # Local persistence
    if cfg["includeDatabase"]:
        emit(files, ctx, m, "PKG_DB", "ItemEntity.kt", T_DB_ENTITY, package_suffix="model")
        emit(files, ctx, m, "PKG_DB", "ItemDao.kt", T_DB_DAO, package_suffix="dao")
        emit(files, ctx, m, "PKG_DB", f"{ctx['APP_CLASS']}Database.kt", T_DB_DATABASE)
        emit(files, ctx, m, "PKG_DB_DI", "DatabaseModule.kt", T_DB_MODULE)

    # Remote
    if cfg["includeNetwork"]:
        emit(files, ctx, m, "PKG_NET", "ItemDto.kt", T_NET_DTO, package_suffix="model")
        emit(files, ctx, m, "PKG_NET", "ItemRemoteDataSource.kt", T_NET_DATASOURCE)
        emit(
            files, ctx, m, "PKG_NET", "RetrofitItemRemoteDataSource.kt",
            T_NET_RETROFIT, package_suffix="retrofit",
        )
        emit(files, ctx, m, "PKG_NET_DI", "NetworkModule.kt", T_NET_MODULE)

    # Preferences
    if cfg["includeDatastore"]:
        emit(files, ctx, m, "PKG_PREFS", "UserPreferencesDataSource.kt", T_PREFS_DATASOURCE)
        emit(files, ctx, m, "PKG_PREFS_DI", "DataStoreModule.kt", T_PREFS_MODULE)

    # Mappers
    if cfg["includeDatabase"]:
        files[kt_file(m, ctx["PKG_MAPPER"], "ItemMappers.kt")] = item_mappers_source(cfg, ctx)
    if cfg["includeDatastore"]:
        emit(files, ctx, m, "PKG_MAPPER", "PreferencesMappers.kt", T_PREFS_MAPPERS)

    # Repositories
    emit(files, ctx, m, "PKG_REPO", "ItemRepository.kt", T_REPO_ITEM)
    if cfg["includeDatabase"]:
        files[kt_file(m, ctx["PKG_REPO_IMPL"], "ItemRepositoryImpl.kt")] = (
            offline_repository_source(cfg, ctx)
        )
    else:
        emit(files, ctx, m, "PKG_REPO_IMPL", "ItemRepositoryImpl.kt", T_REPO_ITEM_IMPL_MEMORY)
    if cfg["includeDatastore"]:
        emit(files, ctx, m, "PKG_REPO", "UserDataRepository.kt", T_REPO_USER)
        emit(files, ctx, m, "PKG_REPO_IMPL", "UserDataRepositoryImpl.kt", T_REPO_USER_IMPL)
    files[kt_file(m, ctx["PKG_DATA_DI"], "RepositoryModule.kt")] = (
        repository_module_source(cfg, ctx)
    )

    # Presentation + app shell
    emit(files, ctx, m, "PKG_FEATURE_API", "Routes.kt", T_FEATURE_ROUTE)
    add_shared_presentation(
        cfg, ctx, files,
        ui_module=m, feature_module=m, nav_module=m,
        theme_module=m, components_module=m,
        viewmodel_template=T_FEATURE_VIEWMODEL_MVVM,
    )
    add_app_entry_points(cfg, ctx, files)
    files.update(app_resources(cfg, ctx, feature_strings=True))

    # Test utilities live in the test source set of the single module.
    if cfg["includeTestUtilities"]:
        emit(
            files, ctx, m, "PKG_TESTING", "MainDispatcherRule.kt",
            T_TEST_DISPATCHER_RULE, test_source=True, package_suffix="util",
        )
        emit(
            files, ctx, m, "PKG_TESTING", "FakeItemRepository.kt",
            T_TEST_FAKE_REPO, test_source=True, package_suffix="repository",
        )

    return files, [":app"]


T_APP_BUILD_CLEAN = _load_template("app-build/T_APP_BUILD_CLEAN.gradle.kts")

# --------------------------------------------------------------------------- #
# Architecture 2: Clean Architecture + MVVM, multi module
# --------------------------------------------------------------------------- #


def build_clean(cfg: Dict[str, Any], ctx: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
    files: Dict[str, str] = {}
    prefix = ctx["PREFIX"]
    feature = ctx["FEATURE"]

    # ----- build-logic ---------------------------------------------------- #
    files["build-logic/settings.gradle.kts"] = BUILD_LOGIC_SETTINGS
    files["build-logic/convention/build.gradle.kts"] = render(
        BUILD_LOGIC_CONVENTION_BUILD, ctx
    )
    for name, body in CONVENTION_SOURCES.items():
        files[f"build-logic/convention/src/main/kotlin/{name}"] = render(body, ctx)

    # ----- domain: pure Kotlin, no Android, no framework ------------------ #
    files["domain/build.gradle.kts"] = module_build_file(
        ctx,
        namespace="",
        plugins=[f"alias(libs.plugins.{prefix}.jvm.library)"],
        dependencies=[
            "// Pure Kotlin only. Adding an Android dependency here breaks the",
            "// dependency rule that makes this layer testable on the JVM.",
            "api(libs.kotlinx.coroutines.core)",
            "api(libs.javax.inject)",
        ],
    )
    emit(files, ctx, "domain", "PKG_MODEL", "Item.kt", T_MODEL_ITEM)
    emit(files, ctx, "domain", "PKG_REPO", "ItemRepository.kt", T_REPO_ITEM)
    if cfg["includeDatastore"]:
        emit(files, ctx, "domain", "PKG_MODEL", "DarkThemeConfig.kt", T_MODEL_DARK_THEME)
        emit(files, ctx, "domain", "PKG_MODEL", "UserData.kt", T_MODEL_USER_DATA)
        emit(files, ctx, "domain", "PKG_REPO", "UserDataRepository.kt", T_REPO_USER)

    for spec in use_case_specs(cfg):
        imports = sorted(render(i, ctx) for i in spec["imports"])
        files[kt_file("domain", ctx["PKG_USECASE"], spec["name"] + ".kt")] = render(
            T_USE_CASE,
            {
                **ctx,
                "USE_CASE_NAME": spec["name"],
                "USE_CASE_DOC": spec["doc"],
                "USE_CASE_REPO": spec["repo"],
                "USE_CASE_SIGNATURE": spec["signature"],
                "USE_CASE_BODY": spec["body"],
                "USE_CASE_IMPORTS": "".join(f"import {i}\n" for i in imports),
            },
        )

    # ----- core:common ---------------------------------------------------- #
    files["core/common/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.core.common",
        plugins=[
            f"alias(libs.plugins.{prefix}.android.library)",
            f"alias(libs.plugins.{prefix}.hilt)",
        ],
        dependencies=["implementation(libs.kotlinx.coroutines.android)"],
    )
    emit(files, ctx, "core/common", "PKG_DISPATCHERS", "AppDispatchers.kt", T_DISPATCHERS)
    emit(
        files, ctx, "core/common", "PKG_DISPATCHERS_DI",
        "DispatchersModule.kt", T_DISPATCHERS_MODULE,
    )

    # ----- core:designsystem ---------------------------------------------- #
    files["core/designsystem/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.core.designsystem",
        plugins=[
            f"alias(libs.plugins.{prefix}.android.library)",
            f"alias(libs.plugins.{prefix}.android.library.compose)",
        ],
        dependencies=[
            "// Compose dependencies come from the compose convention plugin.",
        ],
    )

    # ----- core:ui -------------------------------------------------------- #
    files["core/ui/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.core.ui",
        plugins=[
            f"alias(libs.plugins.{prefix}.android.library)",
            f"alias(libs.plugins.{prefix}.android.library.compose)",
        ],
        dependencies=[
            "api(projects.domain)",
            "api(projects.core.designsystem)",
        ],
    )

    add_shared_presentation(
        cfg, ctx, files,
        ui_module="app",
        feature_module=f"feature/{feature}/impl",
        nav_module="app",
        theme_module="core/designsystem",
        components_module="core/ui",
        viewmodel_template=T_FEATURE_VIEWMODEL_CLEAN,
    )

    # ----- core:database -------------------------------------------------- #
    if cfg["includeDatabase"]:
        files["core/database/build.gradle.kts"] = module_build_file(
            ctx,
            namespace=f"{ctx['PKG']}.core.database",
            plugins=[
                f"alias(libs.plugins.{prefix}.android.library)",
                f"alias(libs.plugins.{prefix}.android.room)",
                f"alias(libs.plugins.{prefix}.hilt)",
            ],
            dependencies=[
                "// No dependency on :domain. Entities are mapped to domain",
                "// models in :data, which keeps this module swappable.",
                "implementation(libs.kotlinx.coroutines.android)",
            ],
        )
        emit(
            files, ctx, "core/database", "PKG_DB", "ItemEntity.kt",
            T_DB_ENTITY, package_suffix="model",
        )
        emit(files, ctx, "core/database", "PKG_DB", "ItemDao.kt", T_DB_DAO, package_suffix="dao")
        emit(
            files, ctx, "core/database", "PKG_DB",
            f"{ctx['APP_CLASS']}Database.kt", T_DB_DATABASE,
        )
        emit(files, ctx, "core/database", "PKG_DB_DI", "DatabaseModule.kt", T_DB_MODULE)

    # ----- core:network --------------------------------------------------- #
    if cfg["includeNetwork"]:
        files["core/network/build.gradle.kts"] = module_build_file(
            ctx,
            namespace=f"{ctx['PKG']}.core.network",
            plugins=[
                f"alias(libs.plugins.{prefix}.android.library)",
                f"alias(libs.plugins.{prefix}.hilt)",
                "alias(libs.plugins.kotlin.serialization)",
            ],
            dependencies=[
                "implementation(libs.kotlinx.coroutines.android)",
                "implementation(libs.kotlinx.serialization.json)",
                "implementation(libs.retrofit.core)",
                "implementation(libs.retrofit.kotlin.serialization)",
                "implementation(libs.okhttp.logging)",
            ],
        )
        emit(
            files, ctx, "core/network", "PKG_NET", "ItemDto.kt",
            T_NET_DTO, package_suffix="model",
        )
        emit(files, ctx, "core/network", "PKG_NET", "ItemRemoteDataSource.kt", T_NET_DATASOURCE)
        emit(
            files, ctx, "core/network", "PKG_NET", "RetrofitItemRemoteDataSource.kt",
            T_NET_RETROFIT, package_suffix="retrofit",
        )
        emit(files, ctx, "core/network", "PKG_NET_DI", "NetworkModule.kt", T_NET_MODULE)

    # ----- core:datastore ------------------------------------------------- #
    if cfg["includeDatastore"]:
        files["core/datastore/build.gradle.kts"] = module_build_file(
            ctx,
            namespace=f"{ctx['PKG']}.core.datastore",
            plugins=[
                f"alias(libs.plugins.{prefix}.android.library)",
                f"alias(libs.plugins.{prefix}.hilt)",
            ],
            dependencies=[
                "implementation(projects.core.common)",
                "implementation(libs.androidx.datastore.preferences)",
                "implementation(libs.kotlinx.coroutines.android)",
            ],
        )
        emit(
            files, ctx, "core/datastore", "PKG_PREFS",
            "UserPreferencesDataSource.kt", T_PREFS_DATASOURCE,
        )
        emit(files, ctx, "core/datastore", "PKG_PREFS_DI", "DataStoreModule.kt", T_PREFS_MODULE)

    # ----- data: implements the domain contracts -------------------------- #
    data_deps = ["api(projects.domain)", "implementation(projects.core.common)"]
    if cfg["includeDatabase"]:
        data_deps.append("implementation(projects.core.database)")
    if cfg["includeNetwork"]:
        data_deps.append("implementation(projects.core.network)")
    if cfg["includeDatastore"]:
        data_deps.append("implementation(projects.core.datastore)")
    data_deps.append("implementation(libs.kotlinx.coroutines.android)")

    files["data/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.data",
        plugins=[
            f"alias(libs.plugins.{prefix}.android.library)",
            f"alias(libs.plugins.{prefix}.hilt)",
        ],
        dependencies=data_deps,
    )

    if cfg["includeDatabase"]:
        files[kt_file("data", ctx["PKG_MAPPER"], "ItemMappers.kt")] = item_mappers_source(
            cfg, ctx
        )
        files[kt_file("data", ctx["PKG_REPO_IMPL"], "ItemRepositoryImpl.kt")] = (
            offline_repository_source(cfg, ctx)
        )
    else:
        emit(files, ctx, "data", "PKG_REPO_IMPL", "ItemRepositoryImpl.kt", T_REPO_ITEM_IMPL_MEMORY)
    if cfg["includeDatastore"]:
        emit(files, ctx, "data", "PKG_MAPPER", "PreferencesMappers.kt", T_PREFS_MAPPERS)
        emit(files, ctx, "data", "PKG_REPO_IMPL", "UserDataRepositoryImpl.kt", T_REPO_USER_IMPL)
    files[kt_file("data", ctx["PKG_DATA_DI"], "RepositoryModule.kt")] = (
        repository_module_source(cfg, ctx)
    )

    # ----- core:testing --------------------------------------------------- #
    if cfg["includeTestUtilities"]:
        files["core/testing/build.gradle.kts"] = module_build_file(
            ctx,
            namespace=f"{ctx['PKG']}.core.testing",
            plugins=[f"alias(libs.plugins.{prefix}.android.library)"],
            dependencies=[
                "// Depends on :domain only, so test doubles implement the same",
                "// contracts the production code does.",
                "api(projects.domain)",
                "api(libs.junit)",
                "api(libs.kotlinx.coroutines.test)",
                "api(libs.turbine)",
            ],
        )
        emit(
            files, ctx, "core/testing", "PKG_TESTING", "MainDispatcherRule.kt",
            T_TEST_DISPATCHER_RULE, package_suffix="util",
        )
        emit(
            files, ctx, "core/testing", "PKG_TESTING", "FakeItemRepository.kt",
            T_TEST_FAKE_REPO, package_suffix="repository",
        )

    # ----- feature:<name>:api / impl -------------------------------------- #
    api_dir = f"feature/{feature}/api"
    impl_dir = f"feature/{feature}/impl"

    files[f"{api_dir}/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.feature.{feature}.api",
        plugins=[f"alias(libs.plugins.{prefix}.android.library)"],
        dependencies=[
            "// Navigation contract only. Other features depend on this, never",
            "// on :impl, so features stay decoupled from each other.",
            "api(libs.androidx.navigation.compose)",
        ],
    )
    emit(
        files, ctx, api_dir, "PKG_FEATURE_API",
        f"{ctx['FEATURE_CLASS']}Navigation.kt", T_FEATURE_ROUTE,
    )

    impl_deps = [f"api(projects.feature.{feature}.api)"]
    if cfg["includeTestUtilities"]:
        impl_deps.append("testImplementation(projects.core.testing)")
    files[f"{impl_dir}/build.gradle.kts"] = module_build_file(
        ctx,
        namespace=f"{ctx['PKG']}.feature.{feature}.impl",
        plugins=[f"alias(libs.plugins.{prefix}.android.feature)"],
        dependencies=impl_deps,
    )
    files[f"{impl_dir}/src/main/res/values/strings.xml"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        + render(T_FEATURE_STRINGS, ctx)
        + "</resources>\n"
    )

    # ----- app ------------------------------------------------------------ #
    app_deps = [
        f"implementation(projects.feature.{feature}.impl)",
        f"implementation(projects.feature.{feature}.api)",
        "",
        "// :data is wired in here and nowhere else. Feature modules see only",
        "// :domain, so they cannot reach into an implementation detail.",
        "implementation(projects.data)",
        "implementation(projects.domain)",
        "",
        "implementation(projects.core.designsystem)",
        "implementation(projects.core.ui)",
        "",
        "implementation(libs.androidx.core.ktx)",
        "implementation(libs.androidx.activity.compose)",
        "implementation(libs.androidx.navigation.compose)",
        "implementation(libs.androidx.lifecycle.runtime.compose)",
    ]
    files["app/build.gradle.kts"] = render(
        T_APP_BUILD_CLEAN,
        {
            **ctx,
            "MINIFY": "true" if cfg["minifyRelease"] else "false",
            "APP_DEPENDENCIES": "\n".join(("    " + d) if d else "" for d in app_deps),
        },
    )

    add_app_entry_points(cfg, ctx, files)
    files.update(app_resources(cfg, ctx, feature_strings=False))

    # ----- module list ---------------------------------------------------- #
    core_modules = ["common", "designsystem", "ui"]
    if cfg["includeDatabase"]:
        core_modules.append("database")
    if cfg["includeDatastore"]:
        core_modules.append("datastore")
    if cfg["includeNetwork"]:
        core_modules.append("network")
    if cfg["includeTestUtilities"]:
        core_modules.append("testing")
    core_modules.sort()

    gradle_paths = [":app", ":domain", ":data"]
    gradle_paths += [f":core:{n}" for n in core_modules]
    gradle_paths += [f":feature:{feature}:api", f":feature:{feature}:impl"]
    return files, gradle_paths


def module_includes_block(architecture: str, gradle_paths: List[str]) -> str:
    if architecture == MVVM:
        return 'include(":app")\n'
    lines = ['include(":app")', "", "// Architecture layers"]
    lines += [f'include("{p}")' for p in (":domain", ":data")]
    lines += ["", "// Shared infrastructure"]
    lines += [f'include("{p}")' for p in gradle_paths if p.startswith(":core:")]
    lines += ["", "// Feature modules"]
    lines += [f'include("{p}")' for p in gradle_paths if p.startswith(":feature:")]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Generated README
# --------------------------------------------------------------------------- #

README_MVVM = _load_template("readme/README_MVVM.md")

README_CLEAN = _load_template("readme/README_CLEAN.md")


# --------------------------------------------------------------------------- #
# Project assembly
# --------------------------------------------------------------------------- #


def build_project(
    cfg: Dict[str, Any], ctx: Dict[str, str]
) -> Tuple[Dict[str, str], Dict[str, bytes], List[str]]:
    clean = cfg["architecture"] == CLEAN

    if clean:
        files, gradle_paths = build_clean(cfg, ctx)
    else:
        files, gradle_paths = build_mvvm(cfg, ctx)

    catalog = VERSION_CATALOG_BASE + (VERSION_CATALOG_CONVENTION if clean else "")

    files.update(
        {
            "settings.gradle.kts": render(
                SETTINGS_GRADLE,
                {
                    **ctx,
                    "INCLUDE_BUILD": '    includeBuild("build-logic")\n' if clean else "",
                    "TYPESAFE_ACCESSORS": (
                        '\nenableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")\n'
                        if clean
                        else ""
                    ),
                    "MODULE_INCLUDES": module_includes_block(
                        cfg["architecture"], gradle_paths
                    ),
                },
            ),
            "build.gradle.kts": render(ROOT_BUILD_GRADLE, ctx),
            "gradle.properties": GRADLE_PROPERTIES,
            "gradle/libs.versions.toml": render(catalog, ctx),
            "gradle/wrapper/gradle-wrapper.properties": render(
                GRADLE_WRAPPER_PROPERTIES, ctx
            ),
            ".gitignore": GITIGNORE,
            "README.md": render(
                README_CLEAN if clean else README_MVVM,
                {**ctx, **readme_tokens(cfg, ctx, clean)},
            ),
        }
    )

    files.update(steering_files(cfg, ctx))

    return files, launcher_icons(), gradle_paths


def readme_tokens(
    cfg: Dict[str, Any], ctx: Dict[str, str], clean: bool
) -> Dict[str, str]:
    """Keep the generated README honest about which layers actually exist."""
    net_line = (
        "- Point `BASE_URL` in `{}` at your real backend.\n".format(
            "core/network" if clean else "data/remote"
        )
        if cfg["includeNetwork"]
        else ""
    )

    # Tree lines are padded to a fixed description column so the diagram stays
    # aligned regardless of how long the feature name is.
    feature = ctx["FEATURE"]
    if clean:
        column = 28
        feature_lines = [
            (
                f"feature/{feature}/api/",
                "Navigation contract other features may depend on",
            ),
            (f"feature/{feature}/impl/", "Screen, ViewModel, UiState, Hilt bindings"),
        ]
    else:
        column = 27
        feature_lines = [(f"    ├── {feature}/", "Screen + ViewModel + UiState")]

    tokens = {
        "PKG_PATH": ctx["PKG"].replace(".", "/"),
        "SHIP_NETWORK_LINE": net_line,
        "FEATURE_TREE_LINE": "".join(
            path.ljust(column) + desc + "\n" for path, desc in feature_lines
        ),
    }

    if clean:
        optional = []
        if cfg["includeDatabase"]:
            optional.append("core/database/              Room entities, DAO, database")
        if cfg["includeNetwork"]:
            optional.append("core/network/               Retrofit DTOs and remote data source")
        if cfg["includeDatastore"]:
            optional.append("core/datastore/             DataStore-backed settings")
        if cfg["includeTestUtilities"]:
            optional.append("core/testing/               Test doubles and the Main dispatcher rule")
        tokens["OPTIONAL_MODULES"] = "".join(line + "\n" for line in optional)

        data_deps = []
        if cfg["includeDatabase"]:
            data_deps.append("core:database")
        if cfg["includeNetwork"]:
            data_deps.append("core:network")
        if cfg["includeDatastore"]:
            data_deps.append("core:datastore")
        tokens["DATA_RULE_MODULES"] = (", " + ", ".join(data_deps)) if data_deps else ""

        source_rules = []
        if cfg["includeDatabase"]:
            source_rules.append(
                "core:database   -> nothing from domain (entities are mapped in :data)"
            )
        if cfg["includeNetwork"]:
            source_rules.append(
                "core:network    -> nothing from domain (DTOs are mapped in :data)"
            )
        tokens["DATA_SOURCE_RULES"] = "".join(line + "\n" for line in source_rules)
    else:
        dirs = []
        if cfg["includeDatabase"]:
            dirs.append("│   ├── local/             Room entities, DAO, database")
        if cfg["includeNetwork"]:
            dirs.append("│   ├── remote/            Retrofit DTOs and remote data source")
        if cfg["includeDatastore"]:
            dirs.append("│   ├── preferences/       DataStore-backed settings")
        if cfg["includeDatabase"]:
            dirs.append("│   ├── mapper/            Entity/DTO <-> domain mapping")
        elif cfg["includeDatastore"]:
            dirs.append("│   ├── mapper/            Stored preferences -> domain mapping")
        tokens["OPTIONAL_DATA_DIRS"] = "".join(line + "\n" for line in dirs)

    return tokens


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def write_project(root: Path, text: Dict[str, str], binary: Dict[str, bytes]) -> None:
    for rel, content in sorted(text.items()):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for rel, blob in sorted(binary.items()):
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold an Android project in MVVM or Clean Architecture + MVVM.",
    )
    parser.add_argument("--config", help="path to the JSON config file")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="directory the project folder is created in (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="delete and recreate the target directory if it already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list the files that would be created without writing anything",
    )
    parser.add_argument(
        "--print-config-template",
        action="store_true",
        help="print a config file with every supported key and its default",
    )
    parser.add_argument(
        "--architecture",
        choices=ARCHITECTURES,
        help="architecture used by --print-config-template",
    )
    args = parser.parse_args(argv)

    if args.print_config_template:
        template = dict(CONFIG_TEMPLATE)
        if args.architecture:
            template["architecture"] = args.architecture
        print(json.dumps(template, indent=2))
        return 0

    if not args.config:
        parser.error("--config is required (or use --print-config-template)")

    try:
        cfg = load_config(Path(args.config).expanduser())
        ctx = build_context(cfg)
        text, binary, gradle_paths = build_project(cfg, ctx)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    root = Path(args.output_dir).expanduser().resolve() / cfg["projectDirName"]

    if args.dry_run:
        print(f"Would create {len(text) + len(binary)} files under {root}")
        for rel in sorted(list(text) + list(binary)):
            print(f"  {rel}")
        return 0

    if root.exists():
        if not args.force:
            print(
                f"error: {root} already exists. Re-run with --force to replace it.",
                file=sys.stderr,
            )
            return 2
        if not root.is_dir():
            print(f"error: {root} exists and is not a directory.", file=sys.stderr)
            return 2
        shutil.rmtree(root)

    root.mkdir(parents=True)
    write_project(root, text, binary)

    label = (
        "Clean Architecture + MVVM (multi module)"
        if cfg["architecture"] == CLEAN
        else "MVVM (single module)"
    )
    print(f"Created {len(text) + len(binary)} files in {root}")
    print(f"Architecture: {label}")
    print()
    print("Gradle modules:")
    for path in gradle_paths:
        print(f"  {path}")
    print()
    print("Next steps:")
    print(f"  1. cd {root}")
    print(
        "  2. Generate the Gradle wrapper (a binary JAR, so it is not scaffolded):\n"
        f"       gradle wrapper --gradle-version {cfg['gradleVersion']}\n"
        "     or open the project in Android Studio, which creates it for you."
    )
    print("  3. ./gradlew :app:assembleDebug")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
