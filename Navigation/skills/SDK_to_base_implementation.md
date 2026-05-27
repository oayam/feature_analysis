# SDK-to-Base-Impl

## 一、简介

OpenHarmony ArkUI 的组件声明通常先出现在 SDK `.d.ts` 文件中，再逐步落到声明式前端解析、native modifier、model、pattern 等 C++ 实现层。对于新增或扩展的 SDK 属性，基础实现的目标不是一次完成全部业务逻辑，而是先建立一条可编译、可追踪、命名一致的最小闭环。

本文档用于指导从 SDK 声明文件生成或补齐 ArkUI 基础实现，重点覆盖：

1. 从 SDK 中识别组件属性类、属性方法、参数类型、回调类型和新增数据结构。
2. 在 JS 前端解析层或 ArkTS/native bridge 中补齐入口解析与绑定。
3. 在 `*_model.h`、`*_model_ng.h`、`*_model_ng.cpp`、`*_pattern.h`、`*_declaration.h` 等后端文件中补齐基础声明、转发、存储和触发器。
4. 对回调属性补齐 `std::function` 类型、保存接口、触发接口以及必要的 JS 包装逻辑。

相关代码通常分布在以下目录：

- `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/`
- `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/`
- `foundation/arkui/ace_engine/frameworks/core/interfaces/native/node/`
- `foundation/arkui/ace_engine/frameworks/core/components_ng/pattern/`

## 二、工作流程

1. 扫描给定 SDK 文件，列出所有继承自 `CommonMethod<T>` 的组件属性类及其方法。
   - 示例：`declare class NavigationAttribute extends CommonMethod<NavigationAttribute> {}`
   - 对每个方法记录方法名、参数类型、返回值、是否可选、是否为回调，以及注释中的版本信息。
   - 同时记录 SDK 中新增的 `interface`、`enum`、`type`，判断它们是否需要映射为 C++ 数据结构或枚举。

2. 建立 SDK 名称与 C++ 实现名称的映射。
   - 不要只按 SDK 文件名直接拼接路径；应优先搜索现有组件的类名、model 名、pattern 名和 modifier 名。
   - 例如 `nav_destination.d.ts` 可能对应 `js_navdestination.*`、`NavDestinationModelNG`、`NavDestinationPattern` 和 `nav_destination_modifier.cpp`。
   - 若已有同类组件，优先复用其文件结构、命名空间、宏、注册方式和参数解析风格。

3. 检查前端入口与绑定。
   - 在 `jsview` 中检查是否存在对应 `js_*.h`、`js_*.cpp`、静态解析函数和 `JSBind` 注册。
   - 在 ArkTS/native bridge 路径中检查 bridge 声明、bridge 实现、modifier 函数表、reset 函数和 node modifier 调用链。
   - 回调入参需要在 JS 或 bridge 层包装为可传递到后端的 `std::function`，并注意作用域、生命周期和空值重置逻辑。

4. 检查基础后端接口。
   - 在 `*_model.h` 中补齐抽象接口或默认空实现。
   - 在 `*_model_ng.h` 中补齐实例接口和必要的静态接口。
   - 在 `*_model_ng.cpp` 中完成从当前 frame node（非静态函数） 或显式 frame node（静态函数） 到 pattern/property/event hub 的转发。如果是事件回调需要转发至event hub。如果是功能属性转发至pattern，如果是布局属性转发至layout-property
   - 对 static pipeline 已覆盖的属性，还要检查 `*_model_static.*` 是否需要同步。

5. 检查 pattern、property、event hub 与 declaration。
   - 普通状态属性优先落在 layout/property 或 pattern 中，保持与相邻属性一致。
   - 事件和生命周期回调优先落在 event hub 或 pattern 中，保持触发时机清晰。
   - 新增 SDK 数据结构应补齐到已有 `*_declaration.h` 或合适的组件声明文件；没有对应文件时再新增。
   - 如果在 `pattern.h` 中新增常驻成员，需要评估内存涨幅。较大的可选对象应优先考虑智能指针或延迟分配，并在新增处写明估算依据。

6. 补齐最小实现闭环。
   - 新增属性至少应具备：前端入口、参数解析、model 声明、model_ng 实现、pattern/property/event hub 存取逻辑、reset/default 路径。
   - 新增回调至少应具备：类型声明、保存接口、清空接口、触发接口、JS 包装和异常/空值保护。
   - 新增枚举或结构体至少应具备：SDK 值到 C++ 值的转换、默认值策略、非法值处理。
   - 仅需要补充声明、预备触发器能力，不需要实现逻辑调用

7. 完成一致性检查。
   - SDK 方法、JS/bridge 方法、modifier 方法、model 方法和 pattern/property 方法应语义一致。
   - 命名应遵循现有代码风格，而不是机械转换 SDK 名称。
   - 参数可选、联合类型、资源类型、数组类型和回调类型应优先参考同组件或同类型属性实现。
   - 不修改 SDK 声明本身，除非任务明确要求。
   - 不引入无关重构，保持改动范围可审阅。

## 三、要点

1. 同一组件在 SDK 与 C++ 中通常语义一致，但命名可能不同。以 Navigation/NavDestination 为例：
   - SDK 文件：`navigation.d.ts`、`nav_destination.d.ts`
   - SDK 属性类：`NavigationAttribute`、`NavDestinationAttribute`
   - JS 前端文件：`js_navigation.*`、`js_navdestination.*`
   - 后端核心文件：`navigation_model.h`、`navigation_model_ng.*`、`navigation_pattern.*`
   - native modifier 文件：`navigation_modifier.cpp`、`nav_destination_modifier.cpp`

2. 检查绑定时不要只看单点代码。
   - `JSBind` 或 bridge 注册只是入口。
   - 还要确认头文件声明、源文件实现、modifier 函数表、model 转发和 pattern/property 存储均已接通。

3. 参数解析应优先参考相邻或同类型属性。
   - 字符串、数字、布尔值、枚举、对象、数组、资源类型、联合类型和回调类型应分别复用已有 helper 或解析模式。
   - 可选参数需要明确默认值、reset 行为和非法值处理。
   - 回调参数需要明确 JS 执行上下文、生命周期、空值清理和后端触发位置。

4. 基础实现应形成最小闭环。
   - 能保存、能重置、能从前端传递到后端。
   - 回调能注册、能清空、能在合适位置触发。
   - 复杂业务逻辑可留给后续需求实现，但不能留下断链接口。

5. 仅生成基础实现，不进行逻辑调用
   - 本文档仅用于指导基础框架的实现，仅实现SDK对应的js层、model层、modelNG层的声明与基础能力预埋，不需要对这些预埋能力在逻辑代码中进行调用