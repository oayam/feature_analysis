---
name: sdk-to-js-frontend
description: Generate or complete OpenHarmony ArkUI declarative JS frontend bindings from SDK declaration files. Use when the user provides or references ArkUI SDK files such as navigation.d.ts, static .d.ets files, CommonMethod component attribute classes, or asks to add missing jsview JSBind/static parsing functions, create js_*.h/js_*.cpp files, or compare SDK properties with foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview implementations.
metadata:
  version: "1.0.0"
---

# SDK-to-JS-Frontend

## Overview

Use this skill to turn ArkUI SDK declarations into JS frontend parsing-layer work in `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/`.

The goal is to close the JS binding surface for SDK-declared components and attributes: discover `CommonMethod<T>` attribute classes, compare them with existing `jsview` implementations, add missing static parsing functions and `JSBind` registrations, and create new `js_*.h`/`js_*.cpp` component files when the SDK introduces a new component.

## Workflow

### 1. Locate Inputs

Identify the SDK declarations and the OpenHarmony source tree:

- SDK examples: `navigation.d.ts`, `nav_destination.d.ts`, `navigation.static.d.ets`, `navDestination.static.d.ets`.
- Source implementation root: `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/`.
- If the user gives only a component name, search for likely SDK files and matching `js_*` files before editing.

Prefer `rg` for discovery:

```bash
rg "extends CommonMethod<" <sdk-file-or-sdk-dir>
rg "class JS.*|JSBind|Bind\\(" foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview
```

### 2. Extract SDK Surface

From each relevant SDK file, list every component attribute class that extends `CommonMethod<T>`.

For each class, record:

- SDK class name, such as `NavigationAttribute`.
- Component name inferred from the class, such as `Navigation`.
- Attribute method names.
- Parameter types, including optional parameters, union types, arrays, resources, callbacks, and object literals.
- Return type and version comments when present.

Treat this as the expected JS frontend surface. Do not modify the SDK declaration unless the user explicitly asks.

### 3. Map SDK Names to JSView Files

Map SDK classes to existing `jsview` files by semantic naming, not by blind string conversion.

For example:

- SDK file: `navigation.d.ts`
- SDK class: `NavigationAttribute`
- JS frontend files: `js_navigation.h`, `js_navigation.cpp`

When unsure, search neighboring components and follow existing naming conventions in the same directory.

### 4. Check Existing Implementation

For every SDK method, verify the implementation has all three pieces:

- A static method declaration in the corresponding `js_*.h`.
- A static method implementation in the corresponding `js_*.cpp`.
- A `JSBind` registration that exposes the method to JS.

Do not count a method as implemented if only one or two of these pieces exist.

Useful searches:

```bash
rg "MethodName|methodName" foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/js_component.*
rg "JSBind|StaticMethod|Method" foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/js_component.cpp
```

### 5. Add Missing Attribute Methods

When an SDK property or method is missing in an existing component file:

1. Add the static method declaration to the component header.
2. Add the static method implementation to the component source file.
3. Register the method in `JSBind`, matching existing style and ordering.
4. Parse parameters according to the SDK type.
5. After successful parsing, add this placeholder comment instead of calling Model:

```cpp
// call to model to-be-done
```

Keep the implementation focused on JS frontend parsing. Do not wire to Model classes unless the user explicitly extends the task.

### 6. Add New Component Files

When the SDK introduces a component class with no existing `jsview` implementation:

1. Choose `js_<component>.h` and `js_<component>.cpp` names that match local conventions.
2. Copy structure from the closest existing component, including namespace, class shape, macros, and binding style.
3. Add declarations and implementations for the SDK-declared attribute methods.
4. Register all exposed methods in `JSBind`.
5. Make only the build-system edits that are necessary for the new files to compile, following nearby patterns.

### 7. Parse Parameters by Existing Patterns

Use adjacent or similar methods as the primary reference for argument parsing.

Common cases to check:

- Strings and resources.
- Numbers and dimensions.
- Booleans.
- Enums.
- Object literals.
- Arrays.
- Callback functions.
- Optional parameters and union types.

Prefer existing helpers and parsing idioms in `jsview` over introducing new helpers. If a type is ambiguous, implement the smallest defensible parser and call out any assumption in the final response.

### 8. Validate Completeness

Before finishing, re-run searches for each newly handled SDK method and confirm the declaration, implementation, and `JSBind` registration are present.

If a build is feasible in the local environment, run the smallest relevant build or compile check. If not, at least perform static consistency checks with `rg` and explain the remaining validation gap.

## Guardrails

- Keep changes scoped to SDK-to-JS frontend parsing.
- Do not call Model layer APIs in this workflow; leave `// call to model to-be-done`.
- Do not rewrite unrelated `jsview` code.
- Preserve local naming, ordering, include style, namespace usage, and registration patterns.
- Do not add scripts or large generated output unless the user asks for automation.
