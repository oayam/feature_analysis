# SDK-to-JS-Frontend

## 一、简介

OpenHarmony ArkUI 的声明式前端解析层主要位于 `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/`。这部分代码通常根据 SDK 中的组件声明补充 JS 绑定与参数解析，格式相对固定，适合从 SDK 声明中抽取组件属性类、方法列表，再按既有 `js_*` 文件模式进行增量实现。

本文档用于指导从 SDK 声明文件生成或补齐 ArkUI JS 前端解析层代码，重点覆盖组件属性类、属性方法、`JSBind` 绑定、静态解析函数和新增组件文件。

## 二、工作流程

1. 扫描给定 SDK 文件，列出所有继承自 `CommonMethod<T>` 的组件属性类，以及这些类中声明的方法。
   - 示例：`declare class NavigationAttribute extends CommonMethod<NavigationAttribute> {}`
   - 对每个方法记录方法名、参数类型、返回值和注释中的版本信息。

2. 在 `foundation/arkui/ace_engine/frameworks/bridge/declarative_frontend/jsview/` 下查找对应实现。
   - 检查组件是否已有对应的 `js_*.h` 和 `js_*.cpp`。
   - 检查方法是否已有静态函数声明、静态函数实现和 `JSBind` 绑定。
   - 同时确认命名是否符合现有代码风格，而不是只按 SDK 名称直接拼接。

3. 针对 SDK 中新增的组件类，参考同类组件新增 `js_*.h` 和 `js_*.cpp`。
   - 文件结构、类名、继承关系、宏和命名空间应与 `jsview` 目录中的现有组件保持一致。
   - 新文件创建后，还需要补齐该组件下每个 SDK 属性方法的静态解析函数和 `JSBind` 绑定。

4. 针对 SDK 中新增的组件属性，在对应 `js_*` 文件中补充静态方法与 `JSBind`。
   - 静态方法根据 SDK 参数类型完成参数解析。
   - 本流程只实现 JS 前端解析层，不调用 Model 层。
   - 参数解析完成后添加注释：`// call to model to-be-done`

5. 完成后进行一致性检查。
   - 新增方法应同时具备：头文件静态方法声明、源文件静态方法实现、`JSBind` 绑定。
   - 新增组件应同时具备：头文件、源文件、绑定入口以及与现有组件一致的命名空间和注册方式。

## 三、要点

1. 同一个组件或属性在 SDK 与 C++ 解析层中通常语义一致，但命名风格可能不同。以 Navigation 为例：
   - SDK 文件：`navigation.d.ts`
   - SDK 属性类：`NavigationAttribute`
   - 解析层核心文件：`js_navigation.h`、`js_navigation.cpp`

2. 检查 `JSBind` 时不要只看绑定语句，还要同时检查：
   - 头文件中是否有静态方法声明。
   - 源文件中是否有静态方法实现。
   - `JSBind` 中是否注册了该方法。

3. 参数解析应优先参考相邻或同类型属性的实现方式。
   - 字符串、数字、布尔值、枚举、对象、数组、回调等参数类型应分别参考现有解析函数。
   - 参数可选、联合类型、资源类型等情况，应尽量复用已有 helper 或解析模式。

4. 新增代码应保持最小闭环。
   - 不提前接入 Model 层。
   - 不引入无关重构。
   - 不修改 SDK 声明本身，除非任务明确要求。
