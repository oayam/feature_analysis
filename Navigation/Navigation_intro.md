# Navigation 组件简介

本文基于 `./arkui_ace_engine` 中 `Navigation` / `NavDestination` 的源码整理，目标是快速说明：

- `Navigation` 的前后端分层方式
- `NavDestination` 作为 `Navigation` 子页面时的协作关系
- 后端核心架构与关键职责

## 1. 总体定位

`Navigation` 是 ArkUI NG 管线中的导航容器，负责管理导航栏、内容区、分栏/分屏、页面切换动画、生命周期和导航栈同步。  
`NavDestination` 是导航栈中的页面单元，通常由 `Navigation` 通过路由信息或 builder 动态创建，并作为其子页面参与显示、切换和回收。

从源码组织上看：

- `Navigation` 后端主目录在 `frameworks/core/components_ng/pattern/navigation/`
- `NavDestination` 的后端实现代码位于 `frameworks/core/components_ng/pattern/navrouter/`
- 两者在运行时并不是彼此孤立组件，而是由 `NavigationPattern + NavigationStack` 统一调度

说明：

- 本文只整理 `Navigation` 与 `NavDestination`
- `NavRouter` / `Navigator` 组件已废弃，不在本文范围内
- 文中出现 `navrouter/` 仅表示 `NavDestination` 的历史代码目录位置，不代表整理 `NavRouter` 组件

## 2. 前后端总体架构

### 2.1 前端层

前端主要有两条接入路径，并且在仓内同时存在：

1. ArkTS/生成组件路径
   - 典型文件：
     - `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/navigation.ets`
     - `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/navDestination.ets`
     - `frameworks/bridge/declarative_frontend/ark_modifier/src/navigation_modifier.ts`
     - `frameworks/bridge/declarative_frontend/ark_modifier/src/nav_destination_modifier.ts`
   - 这一层负责暴露 ArkTS 组件 API、属性对象和 modifier。
2. Declarative JS/JSView 路径
   - 这一层会将dynamic SDK中声明的JS方法做napi侧的实现。相关的SDK参见
     - [[dynamic]Navigation SDK](./SDK/dynamic/navigation.d.ts)
     - [[dynamic]NavDestination SDK](./SDK/dynamic/nav_destination.d.ts)
   - 典型文件：
     - `frameworks/bridge/declarative_frontend/jsview/js_navigation.cpp`
     - `frameworks/bridge/declarative_frontend/jsview/js_navdestination.cpp`
     - `frameworks/bridge/declarative_frontend/jsview/js_navigation_stack.cpp`
   - 这一层负责：
     - `Navigation.create(...)` / `NavDestination.create(...)` 绑定
     - `Navigation.navDestination({ builder })` 的 builder 注册
     - `NavPathStack/JSNavigationStack` 与 C++ 导航栈同步

### 2.2 桥接层

桥接层把前端属性和事件下沉到 C++ NG 组件：

- ArkTS modifier -> native bridge
  - `arkts_native_navigation_bridge.cpp`
  - `arkts_native_nav_destination_bridge.cpp`
- native bridge -> native node modifier
  - `frameworks/core/interfaces/native/node/navigation_modifier.cpp`
  - `frameworks/core/interfaces/native/node/nav_destination_modifier.cpp`
- native node modifier -> model
  - `NavigationModelNG`
  - `NavDestinationModelNG`

这条链路的职责很明确：前端只描述“要什么属性/回调”，真正落到节点树和布局/动画/生命周期的是后端 model/pattern。

### 2.3 后端层

后端核心是 NG 组件体系：

- Model：负责创建节点和写属性
- GroupNode/FrameNode：负责组织组件子树
- Pattern：负责行为、状态机、生命周期、动画、栈同步
- LayoutProperty/LayoutAlgorithm：负责布局参数和测量布局
- EventHub：负责事件回调
- NavigationStack/NavigationManager：负责导航栈、恢复、意图跳转、force split 等全局能力

可概括为：

```text
ArkTS / JS
  -> modifier / jsview
  -> native bridge / native modifier
  -> NavigationModelNG / NavDestinationModelNG
  -> NavigationGroupNode / NavDestinationGroupNode
  -> NavigationPattern / NavDestinationPattern
  -> layout / animation / lifecycle / stack manager
```

## 3. Navigation 前端到后端的主链路

`Navigation` 的关键前后端链路如下：

1. 前端创建组件
   - `JSNavigation::Create()` 创建 `Navigation`
   - `NavigationModel::GetInstance()->Create()` 最终走到 `NavigationModelNG::Create()`

2. 前端提供导航栈和页面 builder
   - `JSNavigation::Create()` 会给 `Navigation` 绑定 `JSNavigationStack`
   - `JSNavigation::SetNavDestination()` 把 `navDestination(builder)` 注册到 `JSNavigationStack`

3. 后端创建基础节点树
   - `NavigationModelNG::Create()` 创建 `NavigationGroupNode`
   - 按需创建：
     - `NavBarNode`
     - `PrimaryContentNode`（force split 场景）
     - `ForceSplitPlaceHolder`
     - `NavigationContent`
     - `Divider`
     - 可选 `DragBar`

4. 导航栈变化触发页面同步
   - `NavigationPattern::SetNavigationStack()` 给栈注册状态变化回调
   - 回调里标记 `needSyncWithJsStack`
   - 构建结束后调用 `SyncWithJsStackIfNeeded()`
   - 进一步执行 `UpdateNavPathList()`、`RefreshNavDestination()`，完成页面创建/复用/缓存/切换

这意味着 `Navigation` 不是简单容器，而是“组件树 + 导航栈 + 页面调度器”的组合体。

## 4. NavDestination 在架构中的位置

`NavDestination` 虽然是独立组件，但在 `Navigation` 体系中承担的是“栈页面”的角色。

### 4.1 创建来源

`NavDestination` 有两种典型进入方式：

1. 直接声明式创建
   - `JSNavDestination::Create()`
   - `NavDestinationModelNG::Create()`

2. 被 `Navigation` 动态创建
   - `JSNavigationStack::CreateNodeByIndex()`
   - `JSNavigationStack::CreateHomeDestination()`
   - `JSNavigationStack::CreateRelatedDestination()`
   - 底层通过 builder 或路由配置加载页面，并找到/生成 `NavDestinationGroupNode`

第二种才是 `Navigation` 常规运行时最关键的路径。

### 4.2 与 Navigation 的关系

运行时关系可以概括为：

- `NavigationStack` 维护“路径名 -> NavDestination 节点”的栈结构
- `NavigationPattern` 根据当前栈顶/前一页决定哪些 `NavDestination` 需要挂载、隐藏、缓存或回收
- `NavDestinationPattern` 负责单页内部的标题栏、工具栏、背景、安全区、滚动联动和系统栏样式

也就是说：

- `Navigation` 负责“哪一页应该出现、如何切换”
- `NavDestination` 负责“这一页自身怎么表现”

## 5. 后端核心架构

## 5.1 Navigation 核心对象

### 1. `NavigationModelNG`

主要职责：

- 创建 `NavigationGroupNode`
- 初始化基础子节点
- 写入导航属性（标题、工具栏、导航栏宽度、模式、分栏等）

关键文件：

- `frameworks/core/components_ng/pattern/navigation/navigation_model_ng.cpp`
- `frameworks/core/components_ng/pattern/navigation/navigation_model_ng.h`

### 2. `NavigationGroupNode`

是 `Navigation` 的节点容器，维护内部关键子节点引用。源码中可见其典型子树包括：

- `NavBarNode`
- `PrimaryContentNode`
- `ForceSplitPlaceHolderNode`
- `ContentNode`
- `DividerNode`
- 动画过渡相关节点

关键文件：

- `frameworks/core/components_ng/pattern/navigation/navigation_group_node.h`

### 3. `NavigationPattern`

是后端核心调度器，职责最重，主要负责：

- 挂接/解绑导航栈
- 同步 JS 栈到 C++ 节点树
- 创建 Home/Related `NavDestination`
- 切换时的 push/pop/replace 动画
- 生命周期分发
- force split、拖拽分栏、模式切换
- 与 `NavigationManager` 协作做恢复与全局状态管理

关键文件：

- `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp`
- `frameworks/core/components_ng/pattern/navigation/navigation_pattern.h`

### 4. `NavigationStack`

这是导航运行时的数据核心，负责维护：

- 当前页面列表 `navPathList_`
- 上一次页面列表 `preNavPathList_`
- 缓存节点
- push/pop/remove/replace
- 索引、恢复、动画标志、拦截回调

`NavigationPattern` 并不直接保存所有页面节点，而是通过 `NavigationStack` 查询、创建和复用。

关键文件：

- `frameworks/core/components_ng/pattern/navigation/navigation_stack.h`

### 5. `NavigationManager`

这是更高一层的全局管理者，主要处理：

- 多个 `Navigation` 实例登记/查找
- 生命周期广播
- recoverable 导航恢复
- intent 恢复
- force split 目标导航判定
- 过渡动画缓存和交互动画状态

关键文件：

- `frameworks/core/components_ng/manager/navigation/navigation_manager.h`
- `frameworks/core/components_ng/manager/navigation/navigation_manager.cpp`

## 5.2 Navigation 后端节点树

从 `NavigationModelNG::Create()` 可以归纳出 `Navigation` 的典型节点结构：

```text
NavigationGroupNode
|- NavBarNode / HomeDestination
|  |- TitleBarNode
|  |- NavBarContentNode
|  `- ToolBarNode
|- PrimaryContentNode            (force split 可选)
|- ForceSplitPlaceHolderNode     (可选)
|- NavigationContentNode
|- DividerNode
`- DragBarNode                   (可选)
```

其中：

- `NavBarNode` 管理左侧/顶部导航栏
- `NavigationContentNode` 承载当前显示的 `NavDestination`
- `DividerNode`/`DragBarNode` 服务于分栏宽度和交互

## 5.3 NavDestination 核心对象

### 1. `NavDestinationModelNG`

负责：

- 创建 `NavDestinationGroupNode`
- 初始化标题栏、返回按钮、内容区、工具栏
- 写入页面级属性：标题、标题栏/工具栏隐藏、背景色、系统过渡类型、模式等

关键文件：

- `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp`
- `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.h`

### 2. `NavDestinationGroupNode`

是单个导航页面的容器节点，维护：

- `TitleBarNode`
- `BackButton`
- `ContentNode`
- `ToolBarNode`
- 动画状态、缓存状态、mode、index、route/path 信息

关键文件：

- `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.h`

### 3. `NavDestinationPattern`

负责单页行为控制，主要包括：

- 标题栏/工具栏挂载与动画
- 页面名、背景色、安全区更新
- `NavDestinationContext` 维护
- 系统栏样式切换
- 滚动驱动标题栏/工具栏隐藏与恢复
- onAttach/onDetach/onShown/onHidden 等生命周期相关逻辑

关键文件：

- `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp`
- `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.h`

### 4. `NavDestinationContext`

这是 `NavDestination` 与导航栈之间的上下文对象，保存：

- `NavPathInfo`
- 所属 `NavigationStack`
- 当前 index / preIndex
- `navDestinationId`
- mode
- 当前尺寸等上下文信息

它是页面切换、动画、生命周期、回调向前端暴露时的重要上下文载体。

关键文件：

- `frameworks/core/components_ng/pattern/navrouter/navdestination_context.h`

## 5.4 NavDestination 后端节点树

从 `NavDestinationModelNG::Create()` 可以归纳其典型结构：

```text
NavDestinationGroupNode
|- TitleBarNode
|  `- BackButton
|- ContentNode
`- ToolBarNode
```

这是一个相对稳定的“页级壳子”：

- `TitleBarNode` 负责页面标题、返回、菜单
- `ContentNode` 承载页面主体内容
- `ToolBarNode` 承载底部工具栏

## 6. 运行时协作关系

从运行链路上看，`Navigation` 与 `NavDestination` 的协作可以简化为：

1. 前端把路由数据和 `navDestination(builder)` 交给 `JSNavigationStack`
2. `NavigationStack` 变化后，`NavigationPattern` 收到状态变化回调
3. `NavigationPattern::UpdateNavPathList()` 决定当前栈需要哪些 `NavDestination`
4. 不存在的页面由 `JSNavigationStack::CreateNodeByIndex()` 动态创建
5. 已存在页面优先复用，其次从 cache 取回，否则新建
6. `NavigationGroupNode` 更新内容区节点
7. `NavigationPattern` 执行 push/pop/replace 动画与生命周期分发
8. 单页内部的显示细节由 `NavDestinationPattern` 继续处理

因此，`NavDestination` 是 `Navigation` 的“内容页对象”，但它又保留了独立 pattern/context，使单页可以拥有完整的标题栏、工具栏、系统栏和滚动联动能力。

## 7. 结论

可以把该组件理解为两层架构：

- 外层 `Navigation`
  - 负责导航容器、栈同步、页面调度、分栏布局、切换动画、全局生命周期
- 内层 `NavDestination`
  - 负责单页外壳、标题栏/工具栏、页面上下文、单页生命周期和视觉表现

其中真正的后端核心是：

- `NavigationPattern`
- `NavigationStack`
- `NavigationManager`
- `NavDestinationPattern`
- `NavigationModelNG` / `NavDestinationModelNG`

这几类对象共同构成了 `Navigation` 组件的核心运行时架构。