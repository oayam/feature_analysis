---
name: js-to-modifier
description: Generate or complete OpenHarmony ArkUI modifier frontend parsing code by using an existing declarative JS frontend implementation as the source of truth. Use when the user references a jsview attribute implementation, asks to add matching ark_component modifier parsing, or wants to wire ArkUI modifier TypeScript/JavaScript, native bridge, node modifier, and declaration files for properties such as NavDestination.fullScreenOverlay.
metadata:
  version: "1.0.0"
---

# JS-to-Modifier

## Overview

Use this skill when an ArkUI component property already works in the declarative JS frontend under `jsview/`, and the task is to implement the equivalent modifier frontend path under `ark_component/` plus the native bridge and node modifier plumbing.

The goal is parity: the modifier frontend should parse valid and invalid inputs the same way as the existing JS attribute method, then call the same NG model/backend behavior.

## Source And Target Paths

Common source-of-truth locations:

- JS frontend: `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/`
- NG model/backend: `foundation/arkui/ace_engine/frameworks/core/components_ng/`

Common modifier frontend targets:

- Ark component source: `frameworks/bridge/declarative_frontend/ark_component/src/Ark<Component>.ts`
- Generated/runtime JS mirror: `frameworks/bridge/declarative_frontend/ark_component/src/arkComponent.js`
- Export declaration: `frameworks/bridge/declarative_frontend/ark_component/export/arkComponent.d.ts`
- Native module bridge: `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_<component>_bridge.{h,cpp}`
- Native module method export: `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_api_impl_bridge.cpp`
- Node modifier API struct: `frameworks/core/interfaces/arkoala/arkoala_api.h`
- Node modifier implementation: `frameworks/core/interfaces/native/node/<component>_modifier.cpp`

## Workflow

### 1. Locate The Existing JS Attribute

Find the JS frontend method, registration, and model call:

```bash
rg -n "propertyName|SetPropertyName|StaticMethod\\(\"propertyName\"" \
  foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview
```

Record:

- JS method name and exposed attribute name.
- Argument validity checks, default values, and reset semantics.
- Target model API, including whether it takes a raw value, `std::optional<T>`, resource object, callback, or structured type.
- Any resource cleanup/reset calls around the model update.

Example pattern:

```cpp
std::optional<bool> value = std::nullopt;
if (info.Length() > 0 && info[0]->IsBoolean()) {
    value = info[0]->ToBoolean();
}
Model::GetInstance()->SetProperty(value);
```

### 2. Confirm The Backend API Exists

Search the model and layout/property layer before adding modifier code:

```bash
rg -n "SetPropertyName|PropertyName" foundation/arkui/ace_engine/frameworks/core/components_ng
```

If the backend API is missing, stop and clarify whether the task is only modifier parsing or a deeper backend feature. Do not invent backend semantics in the modifier layer.

### 3. Map Component Names

Map names by existing files and nearby attributes, not by blind conversion:

- `JSNavDestination` -> `ArkNavDestinationComponent`
- `js_navdestination.cpp` -> `ArkNavDestination.ts`, `arkts_native_nav_destination_bridge.*`, `nav_destination_modifier.cpp`
- Native modifier accessor often uses `get<Component>Modifier()`.

Search similar attributes on the same component first:

```bash
rg -n "recoverable|enableNavigationIndicator|preferredOrientation" \
  foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/ark_component \
  foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/engine/jsi/nativeModule \
  foundation/arkui/ace_engine/frameworks/core/interfaces/native/node
```

Use the closest existing property as the template, especially for optional booleans, enums, resource values, callbacks, and object options.

### 4. Add The Ark Component Modifier

In `Ark<Component>.ts`:

1. Add the component method, returning `this`.
2. Use `modifierWithKey(...)` and a new `ModifierWithKey<T>` class.
3. In `applyPeer`, call `getUINativeModule().<component>.setProperty(...)` or `resetProperty(...)`.
4. Add `checkObjectDiff()` only when nearby equivalent attributes need custom comparison.

Also update `arkComponent.js` with the equivalent runtime JS mirror if this repository keeps the generated JS checked in. Preserve local ordering and style.

### 5. Add Native Bridge Methods

In `arkts_native_<component>_bridge.h`, declare `Set<Property>` and `Reset<Property>`.

In `arkts_native_<component>_bridge.cpp`:

1. Read node from arg 0.
2. Parse arguments using the same validity rules as JS frontend.
3. Represent unset/invalid values the same way as the JS frontend and backend expect.
4. Call `GetArkUINodeModifiers()->get<Component>Modifier()->setProperty(...)` or `resetProperty(...)`.

For optional boolean attributes, prefer this shape:

```cpp
ArkUIOptionalBool optionalValue;
optionalValue.isSet = false;
Framework::JsiCallbackInfo info = Framework::JsiCallbackInfo(runtimeCallInfo);
if (info[1]->IsBoolean()) {
    optionalValue.isSet = true;
    optionalValue.value = info[1]->ToBoolean();
}
modifier->setProperty(nativeNode, optionalValue);
```

Then export both functions in `arkts_native_api_impl_bridge.cpp` on the component object.

### 6. Add Node Modifier Plumbing

In `arkoala_api.h`, extend the matching `ArkUI<Component>Modifier` struct with function pointers. Be careful: changing a struct means every initializer for that struct must be updated.

In `frameworks/core/interfaces/native/node/<component>_modifier.cpp`:

1. Add the setter/resetter functions.
2. Convert bridge types to backend model types.
3. Call the same NG model/static model API found in the JS frontend path.
4. Register the functions in the `Get<Component>Modifier()` initializer.

For optional boolean attributes:

```cpp
std::optional<bool> value;
if (optionalValue.isSet) {
    value = optionalValue.value;
}
ModelNG::SetProperty(frameNode, value);
```

### 7. Update Declarations

Always check and update declaration files that expose `Ark<Component>Component`, especially:

- `frameworks/bridge/declarative_frontend/ark_component/export/arkComponent.d.ts`

This file is easy to miss because the implementation may compile while the modifier type surface is incomplete.

Add the public method signature next to related attributes, matching existing declaration style:

```ts
propertyName(value: boolean | undefined): this;
```

### 8. Validate Completeness

Before finishing, run symbol checks across every layer:

```bash
rg -n "propertyName|PropertyName|setPropertyName|resetPropertyName" \
  foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/ark_component \
  foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/engine/jsi/nativeModule \
  foundation/arkui/ace_engine/frameworks/core/interfaces/arkoala/arkoala_api.h \
  foundation/arkui/ace_engine/frameworks/core/interfaces/native/node
```

Check that all expected pieces exist:

- Ark component method.
- Modifier class and identity.
- Runtime JS mirror when present.
- Export `.d.ts` declaration.
- Bridge header declarations.
- Bridge C++ implementations.
- Native module method exports.
- `arkoala_api.h` struct entries.
- Node modifier setter/resetter.
- Node modifier function table entries.

If feasible, run the smallest relevant build, commonly:

```bash
./limited_fast_build.sh
```

If not feasible, report static verification only and name the remaining validation gap.

## Guardrails

- Keep parsing behavior aligned with the JS frontend source. Invalid values should reset or be ignored exactly the same way.
- Prefer existing helpers and nearby modifier patterns over new abstractions.
- Do not change backend behavior unless the user explicitly asks.
- Do not update SDK or generated static ArkTS paths unless the task scope requires them.
- Preserve local ordering, naming, namespace style, and reset semantics.
- Watch for multiple modifier surfaces: ArkTS source, checked-in JS mirror, export declaration, bridge, native modifier struct, and function table all need to agree.
